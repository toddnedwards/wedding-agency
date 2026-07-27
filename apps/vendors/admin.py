from django.contrib import admin
from .models import Musician, Caricaturist, Photographer, VendorCertificate, VendorPortfolioItem, VendorReview

@admin.register(Musician)
class MusicianAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'instruments', 'experience_years', 'hourly_rate', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'created_at')
    search_fields = ('business_name', 'instruments', 'genres')
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'business_name', 'bio', 'profile_image')}),
        ('Experience', {'fields': ('experience_years', 'instruments', 'genres', 'ensemble_size')}),
        ('Pricing', {'fields': ('hourly_rate',)}),
        ('Location & Contact', {'fields': ('location', 'phone', 'website')}),
        ('Social Media', {'fields': ('instagram', 'facebook')}),
        ('Services', {'fields': ('can_provide_sound_system',)}),
        ('Status', {'fields': ('is_approved', 'is_active')}),
    )

@admin.register(Caricaturist)
class CaricaturistAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'style', 'experience_years', 'hourly_rate', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'style', 'created_at')
    search_fields = ('business_name', 'medium')
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'business_name', 'bio', 'profile_image')}),
        ('Experience', {'fields': ('experience_years', 'style', 'medium')}),
        ('Pricing', {'fields': ('hourly_rate',)}),
        ('Location & Contact', {'fields': ('location', 'phone', 'website')}),
        ('Social Media', {'fields': ('instagram', 'facebook')}),
        ('Services', {'fields': ('rush_delivery_available', 'turnaround_days')}),
        ('Status', {'fields': ('is_approved', 'is_active')}),
    )

@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'specialization', 'experience_years', 'hourly_rate', 'is_approved', 'is_active')
    list_filter = ('is_approved', 'is_active', 'specialization', 'created_at')
    search_fields = ('business_name', 'specialization')
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'business_name', 'bio', 'profile_image')}),
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
    list_display = ('vendor', 'customer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('vendor__business_name', 'customer__email', 'title')
    readonly_fields = ('created_at',)
