from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count, Q
from urllib.parse import parse_qs, urlparse
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
        search_query = self.request.GET.get('q', '').strip()
        sort = self.request.GET.get('sort', 'alphabetical')
        style_filter = self.request.GET.get('style', '').strip()

        if vendor_type == 'musicians':
            queryset = Musician.objects.filter(is_active=True, is_approved=True)
            style_map = {
                'wedding-bands': 'wedding_band',
                'acoustic-solo-duo': 'acoustic_solo_duo',
                'wedding-djs': 'wedding_dj',
                'saxophone-players': 'saxophone_player',
                'pianist': 'pianist',
            }
            if style_filter in style_map:
                queryset = queryset.filter(act_types=style_map[style_filter])
        elif vendor_type == 'caricaturists':
            queryset = Caricaturist.objects.filter(is_active=True, is_approved=True)
        elif vendor_type == 'photographers':
            queryset = Photographer.objects.filter(is_active=True, is_approved=True)
        else:
            return []

        if search_query:
            search_filter = (
                Q(business_name__icontains=search_query)
                | Q(act_name__icontains=search_query)
                | Q(stage_name__icontains=search_query)
                | Q(location__icontains=search_query)
                | Q(bio__icontains=search_query)
                | Q(act_types__icontains=search_query)
            )
            if vendor_type == 'musicians':
                search_filter = search_filter | Q(instruments__icontains=search_query) | Q(genres__icontains=search_query)
            queryset = queryset.filter(search_filter)

        queryset = queryset.annotate(review_count=Count('reviews', distinct=True))

        if sort == 'popular':
            queryset = queryset.order_by('-review_count', 'business_name')
        elif sort == 'price_low':
            queryset = queryset.order_by('hourly_rate', 'business_name')
        elif sort == 'price_high':
            queryset = queryset.order_by('-hourly_rate', 'business_name')
        else:
            queryset = queryset.order_by('business_name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor_type'] = self.kwargs.get('vendor_type')
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['sort_option'] = self.request.GET.get('sort', 'alphabetical')
        return context


class VendorDetailView(DetailView):
    """Display individual vendor profile and allow enquiry"""
    template_name = 'bookings/vendor_detail.html'
    context_object_name = 'vendor'

    @staticmethod
    def _youtube_embed_url(url):
        """Normalize common YouTube URLs into embeddable URLs."""
        if not url:
            return ''

        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.strip('/')
        video_id = ''

        if 'youtu.be' in host:
            video_id = path.split('/')[0]
        elif 'youtube.com' in host:
            if path == 'watch':
                video_id = parse_qs(parsed.query).get('v', [''])[0]
            elif path.startswith('shorts/'):
                video_id = path.split('/')[1] if len(path.split('/')) > 1 else ''
            elif path.startswith('embed/'):
                video_id = path.split('/')[1] if len(path.split('/')) > 1 else ''

        return f'https://www.youtube.com/embed/{video_id}' if video_id else ''
    
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
        vendor = self.object
        gallery_images = vendor.media_images.all().order_by('sort_order', 'id')
        main_gallery_image = gallery_images.filter(is_primary=True).first() or gallery_images.first()
        gallery_videos = vendor.media_videos.all().order_by('sort_order', 'id')
        gallery_video_embeds = [
            {
                'url': item.youtube_url,
                'embed_url': self._youtube_embed_url(item.youtube_url),
            }
            for item in gallery_videos
            if item.youtube_url
        ]

        context['vendor_type'] = self.kwargs.get('vendor_type')
        context['enquiry_form'] = EnquiryForm()
        context['gallery_images'] = gallery_images
        context['main_gallery_image'] = main_gallery_image
        context['gallery_video_embeds'] = gallery_video_embeds
        context['reviews'] = vendor.reviews.select_related('customer').all()
        return context


class EnquiryCreateView(CreateView):
    """Handle enquiry submission"""
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'bookings/enquiry_form.html'
    success_url = reverse_lazy('bookings:enquiry_confirmation')
    
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
