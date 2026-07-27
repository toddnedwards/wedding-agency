from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
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
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return self.business_name


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
    ensemble_size = models.IntegerField(validators=[MinValueValidator(1)])
    
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
