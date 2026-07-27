from django.contrib import admin
from .models import Enquiry, EnquiryResponse, EnquiryFollowUp, EnquiryNotification

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'vendor', 'event_date', 'status', 'created_at')
    list_filter = ('status', 'event_date', 'created_at', 'needs_followup')
    search_fields = ('customer_name', 'customer_email', 'vendor__business_name', 'event_location')
    readonly_fields = ('created_at', 'updated_at', 'vendor_viewed_date', 'admin_notified_date')
    
    fieldsets = (
        ('Customer Details', {'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_user')}),
        ('Vendor', {'fields': ('vendor',)}),
        ('Event Details', {'fields': ('event_date', 'event_time', 'event_type', 'event_location', 'venue_name', 'county')}),
        ('Enquiry Information', {'fields': ('details', 'special_requirements')}),
        ('Status', {'fields': ('status', 'vendor_viewed', 'vendor_viewed_date')}),
        ('Vendor Response', {'fields': ('vendor_response', 'vendor_availability_note')}),
        ('Admin Tracking', {'fields': ('admin_notified', 'admin_notified_date', 'admin_notes', 'needs_followup', 'followup_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(EnquiryResponse)
class EnquiryResponseAdmin(admin.ModelAdmin):
    list_display = ('enquiry', 'response_status', 'suggested_price', 'response_date')
    list_filter = ('response_status', 'response_date')
    search_fields = ('enquiry__customer_name', 'enquiry__vendor__business_name')
    readonly_fields = ('response_date',)

@admin.register(EnquiryFollowUp)
class EnquiryFollowUpAdmin(admin.ModelAdmin):
    list_display = ('enquiry', 'followup_type', 'scheduled_date', 'sent')
    list_filter = ('followup_type', 'scheduled_date', 'sent')
    search_fields = ('enquiry__customer_name', 'message')

@admin.register(EnquiryNotification)
class EnquiryNotificationAdmin(admin.ModelAdmin):
    list_display = ('enquiry', 'notification_type', 'recipient_email', 'sent', 'sent_date')
    list_filter = ('notification_type', 'sent', 'sent_date')
    search_fields = ('enquiry__customer_name', 'recipient_email')
    readonly_fields = ('sent_date',)
