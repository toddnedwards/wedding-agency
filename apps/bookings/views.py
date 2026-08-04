from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from urllib.parse import parse_qs, urlparse
from .models import Enquiry, EnquiryNotification
from .forms import EnquiryForm
from apps.vendors.models import Musician, Caricaturist, Photographer


VENDOR_MODEL_MAP = {
    'musicians': Musician,
    'caricaturists': Caricaturist,
    'photographers': Photographer,
}


def _parse_multi_act_token(raw_token):
    """Parse a token like 'musicians:2|photographers:4' into approved vendor records."""
    token = (raw_token or '').strip()
    if not token:
        return []

    requested = []
    seen_keys = set()

    for part in token.split('|'):
        chunk = (part or '').strip()
        if not chunk:
            continue

        if ':' in chunk:
            vendor_type, vendor_id = chunk.split(':', 1)
        elif '-' in chunk:
            vendor_type, vendor_id = chunk.rsplit('-', 1)
        else:
            continue

        vendor_type = vendor_type.strip()
        vendor_id = vendor_id.strip()

        if vendor_type not in VENDOR_MODEL_MAP or not vendor_id.isdigit():
            continue

        key = f"{vendor_type}:{vendor_id}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        requested.append((vendor_type, int(vendor_id)))

    if not requested:
        return []

    ids_by_type = {}
    for vendor_type, vendor_id in requested:
        ids_by_type.setdefault(vendor_type, []).append(vendor_id)

    loaded_by_type = {}
    for vendor_type, ids in ids_by_type.items():
        model = VENDOR_MODEL_MAP[vendor_type]
        loaded_by_type[vendor_type] = {
            item.id: item
            for item in model.objects.filter(id__in=ids, is_active=True, is_approved=True)
        }

    selected = []
    for vendor_type, vendor_id in requested:
        vendor_obj = loaded_by_type.get(vendor_type, {}).get(vendor_id)
        if not vendor_obj:
            continue
        selected.append({
            'vendor_type': vendor_type,
            'vendor': vendor_obj,
            'name': vendor_obj.public_name,
            'location': vendor_obj.location,
            'type_label': vendor_obj.get_vendor_type_display(),
        })

    return selected


def _serialize_multi_act_token(selected_acts):
    return '|'.join(
        f"{item['vendor_type']}:{item['vendor'].id}"
        for item in selected_acts
    )


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
        vendor_type = self.kwargs.get('vendor_type')
        style_filter = self.request.GET.get('style', '').strip()

        hero_by_vendor_type = {
            'musicians': {
                'title': 'Musicians',
                'image': 'images/banners/musicians-hero.svg',
            },
            'caricaturists': {
                'title': 'Caricaturists',
                'image': 'images/banners/caricaturists-hero.png',
            },
            'photographers': {
                'title': 'Photographers',
                'image': 'images/banners/photographers-hero.png',
            },
        }

        musician_style_hero = {
            'wedding-bands': {
                'title': 'Wedding Bands',
                'image': 'images/banners/wedding-bands-hero.png',
            },
            'acoustic-solo-duo': {
                'title': 'Acoustic Solo / Duo',
                'image': 'images/banners/acoustic-solo-duo-hero.jpg',
            },
            'wedding-djs': {
                'title': 'Wedding DJs',
                'image': 'images/banners/wedding-djs-hero.jpg',
            },
            'saxophone-players': {
                'title': 'Saxophone Players',
                'image': 'images/banners/saxophone-players-hero.png',
            },
            'pianist': {
                'title': 'Pianists',
                'image': 'images/banners/pianist-hero.jpg',
            },
        }

        vendor_hero = hero_by_vendor_type.get(vendor_type, {
            'title': vendor_type.title(),
            'image': 'images/logo.webp',
        })

        if vendor_type == 'musicians' and style_filter in musician_style_hero:
            vendor_hero = musician_style_hero[style_filter]

        context['vendor_type'] = vendor_type
        context['vendor_hero'] = vendor_hero
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
    
    def _send_notifications(self, enquiry, selected_acts=None):
        """Send notifications to vendor and admin"""
        selected_acts = selected_acts or []
        
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
            'selected_acts': selected_acts,
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
            'selected_acts': selected_acts,
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
            'selected_acts': selected_acts,
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


class MultiActEnquiryView(EnquiryCreateView):
    """Submit one enquiry form for multiple selected acts."""
    template_name = 'bookings/enquiry_form.html'

    def get(self, request, *args, **kwargs):
        selected_acts = _parse_multi_act_token(request.GET.get('acts', ''))
        if len(selected_acts) < 2:
            messages.warning(request, 'Please like at least two acts before using Enquire for all.')
            return redirect('home')

        context = {
            'form': EnquiryForm(),
            'selected_acts': selected_acts,
            'selected_acts_token': _serialize_multi_act_token(selected_acts),
            'is_multi_enquiry': True,
            'selected_count': len(selected_acts),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = EnquiryForm(request.POST)
        selected_acts = _parse_multi_act_token(request.POST.get('selected_acts', ''))

        if len(selected_acts) < 2:
            form.add_error(None, 'Please choose at least two acts before sending a multi-enquiry.')

        if not form.is_valid():
            context = {
                'form': form,
                'selected_acts': selected_acts,
                'selected_acts_token': _serialize_multi_act_token(selected_acts),
                'is_multi_enquiry': True,
                'selected_count': len(selected_acts),
            }
            return render(request, self.template_name, context)

        cleaned = form.cleaned_data
        selected_for_email = [
            {
                'name': item['name'],
                'location': item['location'],
                'type_label': item['type_label'],
            }
            for item in selected_acts
        ]

        for item in selected_acts:
            enquiry = Enquiry.objects.create(
                vendor=item['vendor'],
                customer_name=cleaned['customer_name'],
                customer_email=cleaned['customer_email'],
                customer_phone=cleaned['customer_phone'],
                customer_user=request.user if request.user.is_authenticated else None,
                event_date=cleaned['event_date'],
                event_time=cleaned['event_time'],
                event_type=cleaned['event_type'],
                event_location=cleaned['event_location'],
                venue_name=cleaned.get('venue_name', ''),
                county=cleaned.get('county', ''),
                details=cleaned['details'],
                special_requirements=cleaned.get('special_requirements', ''),
            )
            self._send_notifications(enquiry, selected_acts=selected_for_email)

        return HttpResponseRedirect(self.success_url)


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
