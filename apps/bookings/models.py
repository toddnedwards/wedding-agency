from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class Enquiry(models.Model):
    """Enquiry model for wedding services - vendors must confirm availability"""
    STATUS_CHOICES = [
        ('pending', 'Pending - Awaiting Vendor Response'),
        ('viewed', 'Viewed by Vendor'),
        ('available', 'Available - Vendor Confirmed'),
        ('unavailable', 'Unavailable - Vendor Declined'),
        ('booked', 'Booked - Contract Signed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_user = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='enquiries')
    
    # Vendor details
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='enquiries')
    
    # Event details
    event_date = models.DateField()
    event_time = models.TimeField()
    event_type = models.CharField(max_length=200)  # Wedding, Birthday, Corporate, etc.
    event_location = models.CharField(max_length=300)
    venue_name = models.CharField(max_length=200, blank=True)
    county = models.CharField(max_length=100, blank=True)
    
    # Enquiry details
    details = models.TextField(help_text="Additional information about the event and requirements")
    special_requirements = models.TextField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    vendor_viewed = models.BooleanField(default=False)
    vendor_viewed_date = models.DateTimeField(null=True, blank=True)
    
    # Vendor response
    vendor_response = models.TextField(blank=True, help_text="Vendor's response to the enquiry")
    vendor_availability_note = models.TextField(blank=True)
    
    # Admin tracking
    admin_notified = models.BooleanField(default=False)
    admin_notified_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Admin notes for follow-up")
    needs_followup = models.BooleanField(default=True)
    followup_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Enquiries'
    
    def __str__(self):
        return f"Enquiry #{self.id} - {self.customer_name} for {self.vendor.business_name}"
    
    def is_upcoming(self):
        """Check if event is in the future"""
        from datetime import datetime
        event_datetime = datetime.combine(self.event_date, self.event_time)
        return event_datetime > timezone.now()
    
    def days_until_event(self):
        """Get days until event"""
        from datetime import datetime
        event_datetime = datetime.combine(self.event_date, self.event_time)
        if not self.is_upcoming():
            return 0
        return (event_datetime.date() - timezone.now().date()).days
    
    def mark_as_viewed(self):
        """Mark enquiry as viewed by vendor"""
        self.vendor_viewed = True
        self.vendor_viewed_date = timezone.now()
        self.status = 'viewed'
        self.save()


class EnquiryResponse(models.Model):
    """Track vendor responses to enquiries"""
    RESPONSE_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
        ('awaiting', 'Awaiting Confirmation'),
    ]
    
    enquiry = models.OneToOneField(Enquiry, on_delete=models.CASCADE, related_name='response')
    response_status = models.CharField(max_length=20, choices=RESPONSE_CHOICES)
    response_message = models.TextField()
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    response_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-response_date']
    
    def __str__(self):
        return f"Response to Enquiry #{self.enquiry.id}"


class EnquiryFollowUp(models.Model):
    """Track follow-ups on enquiries"""
    FOLLOWUP_TYPE = [
        ('admin_to_vendor', 'Admin Follow-up with Vendor'),
        ('admin_to_customer', 'Admin Follow-up with Customer'),
        ('vendor_reminder', 'Vendor Reminder'),
    ]
    
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='followups')
    followup_type = models.CharField(max_length=30, choices=FOLLOWUP_TYPE)
    message = models.TextField()
    scheduled_date = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['scheduled_date']
    
    def __str__(self):
        return f"Follow-up for Enquiry #{self.enquiry.id}"


class EnquiryNotification(models.Model):
    """Track notifications sent for enquiries"""
    NOTIFICATION_TYPE = [
        ('vendor_new_enquiry', 'New Enquiry for Vendor'),
        ('admin_new_enquiry', 'New Enquiry Alert for Admin'),
        ('customer_confirmation', 'Enquiry Confirmation to Customer'),
        ('vendor_accepted', 'Vendor Accepted Enquiry'),
        ('vendor_declined', 'Vendor Declined Enquiry'),
        ('customer_review_request', 'Post-Event Review Request to Customer'),
    ]
    
    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE)
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=200)
    sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient_email}"


class ReviewRequest(models.Model):
    """Tracks delayed review request emails sent after a booked event."""
    enquiry = models.OneToOneField(Enquiry, on_delete=models.CASCADE, related_name='review_request')
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='review_requests')
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    scheduled_send_at = models.DateTimeField()
    email_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    review_submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review request for enquiry #{self.enquiry_id} ({'sent' if self.email_sent else 'pending'})"


class FunnelEvent(models.Model):
    """Stores lightweight conversion events from public pages."""
    event = models.CharField(max_length=80)
    path = models.CharField(max_length=500, blank=True)
    context = models.CharField(max_length=120, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True)
    vendor_type = models.CharField(max_length=50, blank=True)
    href = models.CharField(max_length=500, blank=True)
    session_key = models.CharField(max_length=80, blank=True)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='funnel_events')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} @ {self.created_at:%Y-%m-%d %H:%M}"
