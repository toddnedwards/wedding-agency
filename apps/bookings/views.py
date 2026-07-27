from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Enquiry, EnquiryNotification
from .forms import EnquiryForm
from apps.vendors.models import Musician, Caricaturist, Photographer


class VendorListView(ListView):
    """Display list of available vendors by type"""
    template_name = 'bookings/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 12
    
    def get_queryset(self):
        vendor_type = self.kwargs.get('vendor_type')
        
        if vendor_type == 'musicians':
            return Musician.objects.filter(is_active=True, is_approved=True)
        elif vendor_type == 'caricaturists':
            return Caricaturist.objects.filter(is_active=True, is_approved=True)
        elif vendor_type == 'photographers':
            return Photographer.objects.filter(is_active=True, is_approved=True)
        
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor_type'] = self.kwargs.get('vendor_type')
        return context


class VendorDetailView(DetailView):
    """Display individual vendor profile and allow enquiry"""
    template_name = 'bookings/vendor_detail.html'
    context_object_name = 'vendor'
    
    def get_object(self):
        vendor_type = self.kwargs.get('vendor_type')
        vendor_id = self.kwargs.get('pk')
        
        if vendor_type == 'musicians':
            return get_object_or_404(Musician, pk=vendor_id, is_active=True, is_approved=True)
        elif vendor_type == 'caricaturists':
            return get_object_or_404(Caricaturist, pk=vendor_id, is_active=True, is_approved=True)
        elif vendor_type == 'photographers':
            return get_object_or_404(Photographer, pk=vendor_id, is_active=True, is_approved=True)
        
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor_type'] = self.kwargs.get('vendor_type')
        context['enquiry_form'] = EnquiryForm()
        return context


class EnquiryCreateView(CreateView):
    """Handle enquiry submission"""
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'bookings/enquiry_form.html'
    success_url = reverse_lazy('enquiry_confirmation')
    
    def form_valid(self, form):
        enquiry = form.save(commit=False)
        
        # Get vendor from URL kwargs
        vendor_type = self.kwargs.get('vendor_type')
        vendor_id = self.kwargs.get('vendor_id')
        
        if vendor_type == 'musicians':
            enquiry.vendor = Musician.objects.get(pk=vendor_id)
        elif vendor_type == 'caricaturists':
            enquiry.vendor = Caricaturist.objects.get(pk=vendor_id)
        elif vendor_type == 'photographers':
            enquiry.vendor = Photographer.objects.get(pk=vendor_id)
        
        # Link to user if logged in
        if self.request.user.is_authenticated:
            enquiry.customer_user = self.request.user
        
        enquiry.save()
        
        # Send notifications
        self._send_notifications(enquiry)
        
        return super().form_valid(form)
    
    def _send_notifications(self, enquiry):
        """Send notifications to vendor and admin"""
        
        # Notify vendor
        vendor_email = enquiry.vendor.user.email
        vendor_context = {
            'vendor_name': enquiry.vendor.business_name,
            'customer_name': enquiry.customer_name,
            'customer_email': enquiry.customer_email,
            'customer_phone': enquiry.customer_phone,
            'event_date': enquiry.event_date,
            'event_time': enquiry.event_time,
            'event_type': enquiry.event_type,
            'event_location': enquiry.event_location,
            'details': enquiry.details,
            'special_requirements': enquiry.special_requirements,
        }
        
        vendor_subject = f"New Enquiry: {enquiry.customer_name} - {enquiry.event_date}"
        vendor_message = render_to_string('bookings/emails/vendor_enquiry.html', vendor_context)
        
        send_mail(
            vendor_subject,
            vendor_message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor_email],
            html_message=vendor_message,
            fail_silently=True,
        )
        
        # Create notification record for vendor
        EnquiryNotification.objects.create(
            enquiry=enquiry,
            notification_type='vendor_new_enquiry',
            recipient_email=vendor_email,
            recipient_name=enquiry.vendor.business_name,
            sent=True,
        )
        
        # Notify admin
        admin_context = {
            'vendor_name': enquiry.vendor.business_name,
            'customer_name': enquiry.customer_name,
            'customer_email': enquiry.customer_email,
            'event_date': enquiry.event_date,
            'event_type': enquiry.event_type,
        }
        
        admin_subject = f"Enquiry Forwarded: {enquiry.customer_name} → {enquiry.vendor.business_name}"
        admin_message = render_to_string('bookings/emails/admin_enquiry.html', admin_context)
        
        send_mail(
            admin_subject,
            admin_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            html_message=admin_message,
            fail_silently=True,
        )
        
        # Create notification record for admin
        EnquiryNotification.objects.create(
            enquiry=enquiry,
            notification_type='admin_new_enquiry',
            recipient_email=settings.ADMIN_EMAIL,
            recipient_name='Admin',
            sent=True,
        )
        
        # Send customer confirmation
        customer_context = {
            'customer_name': enquiry.customer_name,
            'vendor_name': enquiry.vendor.business_name,
            'event_date': enquiry.event_date,
        }
        
        customer_subject = "Your Enquiry Has Been Received"
        customer_message = render_to_string('bookings/emails/customer_confirmation.html', customer_context)
        
        send_mail(
            customer_subject,
            customer_message,
            settings.DEFAULT_FROM_EMAIL,
            [enquiry.customer_email],
            html_message=customer_message,
            fail_silently=True,
        )


def enquiry_confirmation(request):
    """Display enquiry confirmation page"""
    return render(request, 'bookings/enquiry_confirmation.html')


@login_required
def my_enquiries(request):
    """Display user's enquiries"""
    enquiries = Enquiry.objects.filter(customer_user=request.user).order_by('-created_at')
    return render(request, 'bookings/my_enquiries.html', {'enquiries': enquiries})


@login_required
def enquiry_detail(request, pk):
    """Display enquiry details"""
    enquiry = get_object_or_404(Enquiry, pk=pk)
    
    # Check if user is customer or vendor
    if enquiry.customer_user != request.user and enquiry.vendor.user != request.user:
        return redirect('home')
    
    return render(request, 'bookings/enquiry_detail.html', {'enquiry': enquiry})
