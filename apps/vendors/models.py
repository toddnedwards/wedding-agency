from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta

class Vendor(models.Model):
    """Base vendor model"""
    VENDOR_TYPES = [
        ('musician', 'Musician'),
        ('caricaturist', 'Caricaturist'),
        ('photographer', 'Photographer'),
    ]
    
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPES)
    act_name = models.CharField(max_length=200, default='')
    stage_name = models.CharField(max_length=200, blank=True, default='')
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    act_types = models.CharField(max_length=300, blank=True, default='')
    number_of_members = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    home_county = models.CharField(max_length=100, default='')
    home_country = models.CharField(max_length=100, default='')
    start_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    business_name = models.CharField(max_length=200)
    bio = models.TextField()
    profile_image = models.ImageField(upload_to='vendors/')
    experience_years = models.IntegerField(validators=[MinValueValidator(0)])
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.business_name

    @classmethod
    def build_unique_slug(cls, source_text, instance_id=None):
        """Create a unique, URL-safe slug for a vendor record."""
        base_slug = slugify(source_text or '') or 'vendor'
        candidate = base_slug
        counter = 2

        while True:
            qs = cls.objects.filter(slug=candidate)
            if instance_id:
                qs = qs.exclude(pk=instance_id)
            if not qs.exists():
                return candidate
            candidate = f"{base_slug}-{counter}"
            counter += 1

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_source = self.act_name or self.stage_name or self.business_name
            self.slug = self.build_unique_slug(slug_source, self.pk)
        super().save(*args, **kwargs)

    @property
    def public_name(self):
        """Public-facing name shown on the website."""
        if self.stage_name and str(self.stage_name).strip():
            return self.stage_name.strip()
        if self.act_name and str(self.act_name).strip():
            return self.act_name.strip()
        return self.business_name


class VendorMediaImage(models.Model):
    """Approved gallery images shown on the live vendor profile."""
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='media_images')
    image = models.ImageField(upload_to='vendors/gallery/')
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']


class VendorMediaVideo(models.Model):
    """Approved YouTube links shown on the live vendor profile."""
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='media_videos')
    youtube_url = models.URLField()
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']


class VendorProfileUpdateRequest(models.Model):
    """Vendor-submitted profile changes awaiting admin approval."""
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='update_requests')
    requested_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='vendor_update_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    field_data = models.JSONField(default=dict, blank=True)
    pending_profile_image = models.ImageField(upload_to='vendors/pending/', blank=True, null=True)
    review_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='vendor_update_reviews',
    )

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Update Request #{self.id} for {self.vendor.business_name} ({self.status})"

    def _get_typed_vendor_instance(self):
        """Return the concrete subtype instance for this vendor when available."""
        base_vendor = self.vendor
        for relation_name in ('musician', 'caricaturist', 'photographer'):
            try:
                return getattr(base_vendor, relation_name)
            except ObjectDoesNotExist:
                continue
        return base_vendor

    def apply_approved_changes(self, reviewed_by=None):
        """Apply approved data/media to live vendor profile."""
        live_vendor = self._get_typed_vendor_instance()

        for field_name, value in (self.field_data or {}).items():
            if hasattr(live_vendor, field_name):
                setattr(live_vendor, field_name, value)

        if self.pending_profile_image:
            live_vendor.profile_image = self.pending_profile_image

        live_vendor.business_name = live_vendor.public_name
        live_vendor.hourly_rate = live_vendor.start_price
        live_vendor.location = f"{live_vendor.home_county}, {live_vendor.home_country}"
        live_vendor.save()

        draft_images = list(self.draft_images.all())
        if draft_images:
            VendorMediaImage.objects.filter(vendor=self.vendor).delete()
            created_images = []
            for item in draft_images:
                created_images.append(
                    VendorMediaImage.objects.create(
                        vendor=self.vendor,
                        image=item.image,
                        sort_order=item.sort_order,
                        is_primary=item.is_primary,
                    )
                )

            primary = next((img for img in created_images if img.is_primary), None)
            if primary is None and created_images:
                primary = created_images[0]
                primary.is_primary = True
                primary.save(update_fields=['is_primary'])
            if primary is not None:
                live_vendor.profile_image = primary.image
                live_vendor.save(update_fields=['profile_image'])

        draft_videos = list(self.draft_videos.all())
        if draft_videos:
            VendorMediaVideo.objects.filter(vendor=self.vendor).delete()
            for item in draft_videos:
                VendorMediaVideo.objects.create(
                    vendor=self.vendor,
                    youtube_url=item.youtube_url,
                    sort_order=item.sort_order,
                )

        self.status = self.STATUS_APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by
        self.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])


class VendorProfileImageDraft(models.Model):
    """Draft gallery images attached to an update request."""
    update_request = models.ForeignKey('vendors.VendorProfileUpdateRequest', on_delete=models.CASCADE, related_name='draft_images')
    image = models.ImageField(upload_to='vendors/pending/gallery/')
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort_order', 'id']


class VendorProfileVideoDraft(models.Model):
    """Draft YouTube links attached to an update request."""
    update_request = models.ForeignKey('vendors.VendorProfileUpdateRequest', on_delete=models.CASCADE, related_name='draft_videos')
    youtube_url = models.URLField()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']


class Musician(Vendor):
    """Musician vendor model"""
    INSTRUMENT_CHOICES = [
        ('guitar', 'Guitar'),
        ('piano', 'Piano'),
        ('violin', 'Violin'),
        ('drums', 'Drums'),
        ('saxophone', 'Saxophone'),
        ('trumpet', 'Trumpet'),
        ('flute', 'Flute'),
        ('harp', 'Harp'),
        ('other', 'Other'),
    ]
    
    instruments = models.CharField(max_length=200)  # Comma-separated or CharField for primary instrument
    genres = models.CharField(max_length=200)  # Comma-separated genres
    can_provide_sound_system = models.BooleanField(default=False)
    sound_system_details = models.TextField(blank=True)
    can_provide_lighting_system = models.BooleanField(default=False)
    lighting_system_details = models.TextField(blank=True)
    sample_setlist = models.TextField(blank=True)
    ensemble_size = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    
    class Meta:
        verbose_name_plural = 'Musicians'


class Caricaturist(Vendor):
    """Caricaturist vendor model"""
    STYLE_CHOICES = [
        ('realistic', 'Realistic'),
        ('cartoon', 'Cartoon'),
        ('abstract', 'Abstract'),
        ('mixed', 'Mixed'),
    ]
    
    style = models.CharField(max_length=20, choices=STYLE_CHOICES)
    medium = models.CharField(max_length=200)  # e.g., "Digital", "Pencil", "Watercolor"
    rush_delivery_available = models.BooleanField(default=False)
    turnaround_days = models.IntegerField(default=7)
    
    class Meta:
        verbose_name_plural = 'Caricaturists'


class Photographer(Vendor):
    """Photographer vendor model"""
    SPECIALIZATION_CHOICES = [
        ('portrait', 'Portrait'),
        ('wedding', 'Wedding'),
        ('event', 'Event'),
        ('landscape', 'Landscape'),
        ('product', 'Product'),
        ('mixed', 'Mixed'),
    ]
    
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES)
    has_second_shooter = models.BooleanField(default=False)
    drone_available = models.BooleanField(default=False)
    photos_included = models.IntegerField(validators=[MinValueValidator(1)])
    editing_style = models.CharField(max_length=200)  # e.g., "Natural", "Vibrant", "Black & White"
    
    class Meta:
        verbose_name_plural = 'Photographers'


class VendorCertificate(models.Model):
    """Track vendor certifications and licenses"""
    CERTIFICATE_TYPES = [
        ('license', 'License'),
        ('insurance', 'Insurance'),
        ('certification', 'Certification'),
        ('other', 'Other'),
    ]
    
    vendor = models.ForeignKey('vendors.Musician', on_delete=models.CASCADE, related_name='certificates', null=True, blank=True)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES)
    name = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    document = models.FileField(upload_to='certificates/')
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['expiry_date']
    
    def __str__(self):
        return f"{self.name} - {self.vendor.business_name}"
    
    def is_expiring_soon(self, days=30):
        """Check if certificate expires within specified days"""
        expiry_threshold = timezone.now().date() + timedelta(days=days)
        return self.expiry_date <= expiry_threshold and self.expiry_date >= timezone.now().date()
    
    def is_expired(self):
        """Check if certificate is expired"""
        return self.expiry_date < timezone.now().date()
    
    def days_until_expiry(self):
        """Get number of days until expiry"""
        if self.is_expired():
            return 0
        return (self.expiry_date - timezone.now().date()).days


class VendorPortfolioItem(models.Model):
    """Portfolio items for vendors"""
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='portfolio/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class VendorReview(models.Model):
    """Customer reviews for vendors"""
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['vendor', 'customer']
    
    def __str__(self):
        return f"{self.rating}★ - {self.vendor.business_name}"
