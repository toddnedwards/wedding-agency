import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count, DecimalField, F, Q
from django.db.models.functions import Cast
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from urllib.parse import parse_qs, urlparse, urlencode
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Enquiry, EnquiryNotification, ReviewRequest, FunnelEvent
from .forms import EnquiryForm, ReviewSubmissionForm
from apps.vendors.models import Musician, Caricaturist, Photographer, VendorReview, VendorUnavailableDate
from apps.vendors.constants import UK_COUNTIES

logger = logging.getLogger(__name__)

ALLOWED_FUNNEL_EVENTS = {
    'vendor_card_click',
    'check_availability_click',
    'multi_enquiry_click',
    'enquiry_submit',
}


VENDOR_MODEL_MAP = {
    'musicians': Musician,
    'caricaturists': Caricaturist,
    'photographers': Photographer,
}


def _get_vendor_queryset(vendor_type):
    model = VENDOR_MODEL_MAP.get(vendor_type)
    if not model:
        return None
    return model.objects.filter(is_active=True, is_approved=True)


def vendor_detail_legacy_redirect(request, vendor_type, pk):
    queryset = _get_vendor_queryset(vendor_type)
    if queryset is None:
        return redirect('bookings:vendor_list', vendor_type=vendor_type)

    vendor = get_object_or_404(queryset, pk=pk)
    if not vendor.slug:
        vendor.slug = vendor.build_unique_slug(vendor.public_name, vendor.pk)
        vendor.save(update_fields=['slug'])

    return redirect(
        reverse('bookings:vendor_detail', kwargs={'vendor_type': vendor_type, 'slug': vendor.slug}),
        permanent=True,
    )


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


def _build_enquiry_initial(request):
    """Build enquiry initial values from URL query parameters."""
    initial = {}

    event_date_raw = (request.GET.get('event_date') or request.GET.get('available_date') or '').strip()
    if event_date_raw:
        parsed = parse_date(event_date_raw)
        if parsed is not None:
            initial['event_date'] = parsed

    for form_field, query_key in (
        ('event_type', 'event_type'),
        ('event_location', 'event_location'),
        ('county', 'county'),
    ):
        value = (request.GET.get(query_key) or '').strip()
        if value:
            initial[form_field] = value

    budget = (request.GET.get('budget') or '').strip()
    if budget:
        initial['details'] = f"Estimated budget: {budget}"

    return initial


class VendorListView(ListView):
    """Display list of available vendors by type"""
    template_name = 'bookings/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 12
    
    def get_queryset(self):
        self.show_unavailable_search_message = False
        vendor_type = self.kwargs.get('vendor_type')
        search_query = self.request.GET.get('q', '').strip()
        sort = self.request.GET.get('sort', 'alphabetical')
        style_filter = self.request.GET.get('style', '').strip()
        location_filter = self.request.GET.get('location', '').strip()
        available_date_raw = self.request.GET.get('available_date', '').strip()
        available_date = parse_date(available_date_raw) if available_date_raw else None

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

        valid_locations = dict(UK_COUNTIES)
        if location_filter in valid_locations:
            queryset = queryset.filter(
                **{f'county_pricing__{location_filter}__isnull': False}
            ).annotate(
                region_price=Cast(
                    F(f'county_pricing__{location_filter}'),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            ).exclude(region_price__lte=0)

        alternatives_queryset = queryset

        if search_query:
            search_filter = (
                Q(business_name__icontains=search_query)
                | Q(act_name__icontains=search_query)
                | Q(stage_name__icontains=search_query)
                | Q(act_types__icontains=search_query)
            )
            if vendor_type == 'musicians':
                search_filter = Q(business_name__icontains=search_query) | Q(act_name__icontains=search_query) | Q(stage_name__icontains=search_query) | Q(genres__icontains=search_query)
            queryset = queryset.filter(search_filter)

        if available_date is not None:
            unavailable_vendor_ids = set(Enquiry.objects.filter(
                event_date=available_date,
                status='booked',
            ).values_list('vendor_id', flat=True))

            manually_blocked_vendor_ids = VendorUnavailableDate.objects.filter(
                date=available_date,
            ).values_list('vendor_id', flat=True)
            unavailable_vendor_ids.update(manually_blocked_vendor_ids)

            queryset = queryset.exclude(id__in=unavailable_vendor_ids)

            if search_query and not queryset.exists() and alternatives_queryset.exists():
                queryset = alternatives_queryset.exclude(id__in=unavailable_vendor_ids)
                self.show_unavailable_search_message = True

        queryset = queryset.annotate(
            review_count=Count('reviews', filter=Q(reviews__is_approved=True), distinct=True)
        )

        if sort == 'popular':
            queryset = queryset.order_by('-review_count', 'business_name')
        elif sort == 'price_low':
            queryset = queryset.order_by('region_price' if location_filter in valid_locations else 'hourly_rate', 'business_name')
        elif sort == 'price_high':
            queryset = queryset.order_by('-region_price' if location_filter in valid_locations else '-hourly_rate', 'business_name')
        else:
            queryset = queryset.order_by('business_name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor_type = self.kwargs.get('vendor_type')
        style_filter = self.request.GET.get('style', '').strip()
        available_date_raw = self.request.GET.get('available_date', '').strip()
        available_date = parse_date(available_date_raw) if available_date_raw else None

        hero_by_vendor_type = {
            'musicians': {
                'title': 'Musicians',
                'image': 'images/banners/wedding-bands-hero.png',
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
        context['location_value'] = self.request.GET.get('location', '').strip()
        context['location_choices'] = UK_COUNTIES
        context['sort_option'] = self.request.GET.get('sort', 'alphabetical')
        context['today_iso'] = timezone.localdate().isoformat()
        context['available_date'] = available_date.isoformat() if available_date else available_date_raw
        context['availability_filter_active'] = bool(available_date)
        context['show_unavailable_search_message'] = self.show_unavailable_search_message
        context['event_type_value'] = self.request.GET.get('event_type', '').strip()
        quick_enquiry_payload = {
            'event_date': context['available_date'],
            'county': dict(UK_COUNTIES).get(context['location_value'], ''),
        }
        quick_enquiry_payload = {k: v for k, v in quick_enquiry_payload.items() if v}
        context['quick_enquiry_query'] = urlencode(quick_enquiry_payload)
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
        vendor_slug = self.kwargs.get('slug')
        queryset = _get_vendor_queryset(vendor_type)

        if queryset is None:
            return None

        return get_object_or_404(queryset, slug=vendor_slug)
    
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

        reviews = list(vendor.reviews.filter(is_approved=True).select_related('customer', 'enquiry').all())
        testimonial_reviews = []

        for index in range(1, 4):
            name = getattr(vendor, f'testimonial_{index}_name', '').strip()
            event_type = getattr(vendor, f'testimonial_{index}_event_type', '').strip()
            comment = getattr(vendor, f'testimonial_{index}_text', '').strip()
            if not (name or event_type or comment):
                continue
            testimonial_reviews.append({
                'customer_name': name or 'Client',
                'event_type': event_type or 'Event',
                'title': '',
                'comment': comment,
                'rating': 5,
                'is_testimonial': True,
            })

        review_cards = []
        for review in reviews:
            review_cards.append({
                'customer_name': review.customer_name or (review.customer.first_name if review.customer else 'Customer'),
                'event_type': getattr(review.enquiry, 'event_type', None) or 'Event',
                'title': review.title or 'Client review',
                'comment': review.comment,
                'rating': review.rating,
                'is_testimonial': False,
            })
        review_cards.extend(testimonial_reviews)

        context['vendor_type'] = self.kwargs.get('vendor_type')
        context['enquiry_form'] = EnquiryForm(initial=_build_enquiry_initial(self.request))
        context['gallery_images'] = gallery_images
        context['main_gallery_image'] = main_gallery_image
        context['gallery_video_embeds'] = gallery_video_embeds
        context['reviews'] = review_cards
        context['visible_reviews'] = review_cards[:3]
        context['more_reviews'] = review_cards[3:]
        context['display_review_count'] = len(review_cards)
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
        notification_sent = self._send_notifications(enquiry)
        if not notification_sent:
            messages.warning(
                self.request,
                'Your enquiry was received, but email notifications could not be sent right now. Please contact us directly if needed.'
            )
        
        return super().form_valid(form)
    
    def _send_mail_with_fallback(self, subject, message, recipient_list):
        """Send an email and log failures without breaking the enquiry flow."""
        try:
            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                html_message=message,
                fail_silently=False,
            )
            return True
        except Exception as exc:
            logger.exception(
                'Failed to send enquiry email to %s with subject "%s": %s',
                recipient_list,
                subject,
                exc,
            )
            return False
    
    def _send_notifications(self, enquiry, selected_acts=None):
        """Send notifications to vendor and admin"""
        selected_acts = selected_acts or []
        sent_any = False
        
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
            'venue_name': enquiry.venue_name,
            'county': enquiry.county,
            'details': enquiry.details,
            'special_requirements': enquiry.special_requirements,
            'selected_acts': selected_acts,
        }
        
        vendor_subject = f"New Enquiry: {enquiry.customer_name} - {enquiry.event_date}"
        vendor_message = render_to_string('bookings/emails/vendor_enquiry.html', vendor_context)
        
        vendor_sent = self._send_mail_with_fallback(vendor_subject, vendor_message, [vendor_email])
        sent_any = sent_any or vendor_sent
        
        # Create notification record for vendor
        EnquiryNotification.objects.create(
            enquiry=enquiry,
            notification_type='vendor_new_enquiry',
            recipient_email=vendor_email,
            recipient_name=enquiry.vendor.business_name,
            sent=vendor_sent,
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
        
        admin_sent = self._send_mail_with_fallback(admin_subject, admin_message, [settings.ADMIN_EMAIL])
        sent_any = sent_any or admin_sent
        
        # Create notification record for admin
        EnquiryNotification.objects.create(
            enquiry=enquiry,
            notification_type='admin_new_enquiry',
            recipient_email=settings.ADMIN_EMAIL,
            recipient_name='Admin',
            sent=admin_sent,
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
        
        customer_sent = self._send_mail_with_fallback(customer_subject, customer_message, [enquiry.customer_email])
        sent_any = sent_any or customer_sent
        
        return sent_any


class MultiActEnquiryView(EnquiryCreateView):
    """Submit one enquiry form for multiple selected acts."""
    template_name = 'bookings/enquiry_form.html'

    def get(self, request, *args, **kwargs):
        selected_acts = _parse_multi_act_token(request.GET.get('acts', ''))
        if len(selected_acts) < 2:
            messages.warning(request, 'Please like at least two acts before using Enquire for all.')
            return redirect('home')

        context = {
            'form': EnquiryForm(initial=_build_enquiry_initial(request)),
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


@csrf_exempt
@require_POST
def capture_funnel_event(request):
    """Receive lightweight funnel events from frontend tracking."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    event_name = str(payload.get('event', '')).strip()
    if event_name not in ALLOWED_FUNNEL_EVENTS:
        return JsonResponse({'ok': False, 'error': 'invalid_event'}, status=400)

    path = str(payload.get('path', '')).strip()[:500]
    context = str(payload.get('context', '')).strip()[:120]
    vendor_name = str(payload.get('vendor', '')).strip()[:200]
    vendor_type = str(payload.get('vendorType', '')).strip()[:50]
    href = str(payload.get('href', '')).strip()[:500]

    session_key = request.session.session_key or ''
    if not session_key:
        request.session.create()
        session_key = request.session.session_key or ''

    metadata = {}
    for key in ('destination', 'timestamp'):
        value = payload.get(key)
        if value is not None:
            metadata[key] = str(value)[:300]

    FunnelEvent.objects.create(
        event=event_name,
        path=path,
        context=context,
        vendor_name=vendor_name,
        vendor_type=vendor_type,
        href=href,
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None,
        metadata=metadata,
    )

    return JsonResponse({'ok': True})


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


def submit_review(request, token):
    """Allow customers to submit a review through a secure review-request link."""
    review_request = get_object_or_404(ReviewRequest, token=token)
    existing_review = VendorReview.objects.filter(enquiry=review_request.enquiry).first()

    if review_request.review_submitted_at or existing_review is not None:
        return render(
            request,
            'bookings/review_submission.html',
            {
                'review_request': review_request,
                'already_submitted': True,
                'form': None,
            },
        )

    if request.method == 'POST':
        form = ReviewSubmissionForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.vendor = review_request.vendor
            review.enquiry = review_request.enquiry
            review.customer = review_request.enquiry.customer_user
            review.customer_name = review_request.customer_name
            review.customer_email = review_request.customer_email
            review.is_approved = False
            review.save()

            review_request.review_submitted_at = timezone.now()
            review_request.save(update_fields=['review_submitted_at'])

            return render(
                request,
                'bookings/review_submission.html',
                {
                    'review_request': review_request,
                    'submitted': True,
                    'form': None,
                },
            )
    else:
        form = ReviewSubmissionForm()

    return render(
        request,
        'bookings/review_submission.html',
        {
            'review_request': review_request,
            'form': form,
        },
    )
