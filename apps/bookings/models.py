from django.db import models
from django.utils import timezone
from datetime import timedelta

class Booking(models.Model):
    """Booking model for wedding services"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]
    
    customer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='bookings')
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE, related_name='bookings')
    event_date = models.DateTimeField()
    event_location = models.CharField(max_length=300)
    event_details = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    deposit_required = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_paid = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
    
    def __str__(self):
        return f"Booking #{self.id} - {self.vendor.business_name} - {self.event_date.strftime('%Y-%m-%d')}"
    
    def is_upcoming(self):
        """Check if booking is in the future"""
        return self.event_date > timezone.now()
    
    def days_until_event(self):
        """Get days until event"""
        if not self.is_upcoming():
            return 0
        return (self.event_date - timezone.now()).days
    
    def get_remaining_amount(self):
        """Get remaining amount to be paid"""
        return self.total_amount - self.paid_amount


class BookingInvoice(models.Model):
    """Invoice for bookings"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.invoice_number


class BookingPayment(models.Model):
    """Track individual payments for a booking"""
    PAYMENT_METHOD = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment of ${self.amount} for Booking #{self.booking.id}"


class BookingReminder(models.Model):
    """Reminders for upcoming bookings and certificate expirations"""
    REMINDER_TYPE = [
        ('booking', 'Booking Reminder'),
        ('certificate', 'Certificate Expiry'),
        ('payment', 'Payment Due'),
    ]
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    reminder_date = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['reminder_date']
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} - {self.title}"


class BookingContract(models.Model):
    """Contract for bookings"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='contract')
    contract_date = models.DateTimeField(auto_now_add=True)
    contract_content = models.TextField()
    signed = models.BooleanField(default=False)
    signed_date = models.DateTimeField(null=True, blank=True)
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    
    def __str__(self):
        return f"Contract for Booking #{self.booking.id}"
