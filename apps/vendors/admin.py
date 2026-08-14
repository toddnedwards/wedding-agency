from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from .models import (
    Musician,
    Caricaturist,
    Photographer,
    VendorUnavailableDate,
    VendorCertificate,
    VendorPortfolioItem,
    VendorReview,
    VendorMediaImage,
    VendorMediaVideo,
    VendorProfileUpdateRequest,
    VendorProfileImageDraft,
    VendorProfileVideoDraft,
)


@admin.register(VendorUnavailableDate)
class VendorUnavailableDateAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'date', 'note', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('vendor__business_name', 'vendor__act_name', 'vendor__stage_name', 'note')
    ordering = ('date', 'vendor__business_name')

@admin.register(Musician)
class MusicianAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'act_name_is_current', 'instruments', 'experience_years', 'hourly_rate', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'created_at')
    search_fields = ('business_name', 'instruments', 'genres')
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'business_name', 'act_name_is_current', 'bio', 'profile_image')}),
        ('Experience', {'fields': ('experience_years', 'instruments', 'genres', 'ensemble_size')}),
        ('Pricing', {'fields': ('hourly_rate',)}),
        ('Location & Contact', {'fields': ('location', 'phone', 'website')}),
        ('Social Media', {'fields': ('instagram', 'facebook')}),
        ('Services', {'fields': ('can_provide_sound_system',)}),
        ('Status', {'fields': ('is_approved', 'is_active')}),
    )

@admin.register(Caricaturist)
class CaricaturistAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'act_name_is_current', 'style', 'experience_years', 'hourly_rate', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'style', 'created_at')
    search_fields = ('business_name', 'medium')
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'business_name', 'act_name_is_current', 'bio', 'profile_image')}),
        ('Experience', {'fields': ('experience_years', 'style', 'medium')}),
        ('Pricing', {'fields': ('hourly_rate',)}),
        ('Location & Contact', {'fields': ('location', 'phone', 'website')}),
        ('Social Media', {'fields': ('instagram', 'facebook')}),
        ('Services', {'fields': ('rush_delivery_available', 'turnaround_days')}),
        ('Status', {'fields': ('is_approved', 'is_active')}),
    )

@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'act_name_is_current', 'specialization', 'experience_years', 'hourly_rate', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'specialization', 'created_at')
    search_fields = ('business_name', 'specialization')
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'business_name', 'act_name_is_current', 'bio', 'profile_image')}),
        ('Experience', {'fields': ('experience_years', 'specialization', 'editing_style')}),
        ('Pricing', {'fields': ('hourly_rate',)}),
        ('Location & Contact', {'fields': ('location', 'phone', 'website')}),
        ('Social Media', {'fields': ('instagram', 'facebook')}),
        ('Services', {'fields': ('has_second_shooter', 'drone_available', 'photos_included')}),
        ('Status', {'fields': ('is_approved', 'is_active')}),
    )

@admin.register(VendorCertificate)
class VendorCertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'certificate_type', 'expiry_date', 'is_valid')
    list_filter = ('certificate_type', 'is_valid', 'expiry_date')
    search_fields = ('name', 'vendor__business_name')
    readonly_fields = ('created_at',)

@admin.register(VendorPortfolioItem)
class VendorPortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'vendor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'vendor__business_name')

@admin.register(VendorReview)
class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'customer_name', 'customer_email', 'rating', 'is_approved', 'created_at', 'approved_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('vendor__business_name', 'customer__email', 'customer_name', 'customer_email', 'title')
    readonly_fields = ('created_at', 'approved_at')
    actions = ['approve_reviews']

    def save_model(self, request, obj, form, change):
        if obj.is_approved and obj.approved_at is None:
            obj.approved_at = timezone.now()
            obj.approved_by = request.user
        elif not obj.is_approved:
            obj.approved_at = None
            obj.approved_by = None
        super().save_model(request, obj, form, change)

    @admin.action(description='Approve selected reviews')
    def approve_reviews(self, request, queryset):
        updated = queryset.filter(is_approved=False).update(
            is_approved=True,
            approved_at=timezone.now(),
            approved_by=request.user,
        )
        self.message_user(request, f'Approved {updated} review(s).')


@admin.register(VendorMediaImage)
class VendorMediaImageAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'sort_order', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('vendor__business_name',)
    ordering = ('vendor', 'sort_order')


@admin.register(VendorMediaVideo)
class VendorMediaVideoAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'youtube_url', 'sort_order', 'created_at')
    search_fields = ('vendor__business_name', 'youtube_url')
    ordering = ('vendor', 'sort_order')


class VendorProfileImageDraftInline(admin.TabularInline):
    model = VendorProfileImageDraft
    extra = 0


class VendorProfileVideoDraftInline(admin.TabularInline):
    model = VendorProfileVideoDraft
    extra = 0


@admin.register(VendorProfileUpdateRequest)
class VendorProfileUpdateRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'status', 'requested_by', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'submitted_at')
    search_fields = ('vendor__business_name', 'requested_by__email')
    readonly_fields = ('submitted_at', 'field_data_summary')
    inlines = [VendorProfileImageDraftInline, VendorProfileVideoDraftInline]
    actions = ['approve_requests', 'reject_requests']
    fieldsets = (
        ('Request', {
            'fields': ('vendor', 'requested_by', 'status', 'submitted_at'),
        }),
        ('Submitted Field Data', {
            'fields': ('field_data_summary',),
        }),
        ('Admin Review', {
            'fields': ('review_notes',),
            'description': 'Use this area to record approval/rejection notes for internal moderation.',
        }),
    )

    @admin.display(description='Submitted values')
    def field_data_summary(self, obj):
        data = obj.field_data or {}
        if not data:
            return '(No field changes submitted)'

        def format_value(value):
            if isinstance(value, (list, tuple)):
                return ', '.join(str(item) for item in value) if value else '(empty)'
            if isinstance(value, dict):
                return '; '.join(f'{k}: {v}' for k, v in value.items()) if value else '(empty)'
            if value is None:
                return '(none)'
            return str(value)

        cards = [
            (
                key.replace('_', ' ').title(),
                format_value(value),
            )
            for key, value in data.items()
        ]

        return format_html_join(
            '',
            '<div class="vendor-update-field-card">'
            '<div class="vendor-update-field-label">{}</div>'
            '<div class="vendor-update-field-value">{}</div>'
            '</div>',
            cards,
        )

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = (
                VendorProfileUpdateRequest.objects
                .filter(pk=obj.pk)
                .values_list('status', flat=True)
                .first()
            )

        # Stash previous status so save_related can decide whether to publish after inlines are saved.
        obj._previous_status = previous_status

        if obj.status == VendorProfileUpdateRequest.STATUS_REJECTED:
            obj.reviewed_at = obj.reviewed_at or timezone.now()
            obj.reviewed_by = obj.reviewed_by or request.user

        if obj.status == VendorProfileUpdateRequest.STATUS_APPROVED:
            obj.reviewed_at = obj.reviewed_at or timezone.now()
            obj.reviewed_by = obj.reviewed_by or request.user

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        obj = form.instance
        previous_status = getattr(obj, '_previous_status', None)
        should_publish = (
            obj.status == VendorProfileUpdateRequest.STATUS_APPROVED
            and previous_status != VendorProfileUpdateRequest.STATUS_APPROVED
        )

        if should_publish:
            obj.apply_approved_changes(reviewed_by=request.user)

    @admin.action(description='Approve selected requests and publish changes')
    def approve_requests(self, request, queryset):
        approved_count = 0
        for item in queryset.exclude(status=VendorProfileUpdateRequest.STATUS_APPROVED):
            item.apply_approved_changes(reviewed_by=request.user)
            approved_count += 1
        self.message_user(request, f'Approved {approved_count} request(s).')

    @admin.action(description='Reject selected requests')
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status=VendorProfileUpdateRequest.STATUS_PENDING).update(
            status=VendorProfileUpdateRequest.STATUS_REJECTED,
            reviewed_at=timezone.now(),
            reviewed_by=request.user,
        )
        self.message_user(request, f'Rejected {updated} request(s).')
