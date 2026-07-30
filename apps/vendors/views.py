from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from django.http import Http404
from django.contrib import messages
from django.db import transaction
from django.db import IntegrityError
from decimal import Decimal
from .models import (
    Musician,
    Caricaturist,
    Photographer,
    VendorMediaImage,
    VendorMediaVideo,
    VendorProfileUpdateRequest,
    VendorProfileImageDraft,
    VendorProfileVideoDraft,
)
from .forms import MusicianSignupForm, CaricaturistSignupForm, PhotographerSignupForm
from apps.accounts.models import CustomUser


def get_vendor_for_user(user):
    """Return vendor profile for user regardless of user_type value."""
    for model in (Musician, Caricaturist, Photographer):
        vendor = model.objects.filter(user=user).first()
        if vendor is not None:
            return vendor
    return None


def get_profile_completion(vendor):
    """Return profile completeness details for dashboard prompts."""
    if vendor is None:
        return {
            'profile_complete': False,
            'missing_profile_fields': ['Create a vendor profile'],
        }

    required_checks = [
        ('Act name', bool(vendor.act_name and str(vendor.act_name).strip())),
        ('Act type', bool(vendor.act_types and str(vendor.act_types).strip())),
        ('County', bool(vendor.home_county and str(vendor.home_county).strip())),
        ('Country', bool(vendor.home_country and str(vendor.home_country).strip())),
        ('Starting price', vendor.start_price is not None and vendor.start_price >= 0),
        ('Bio', bool(vendor.bio and str(vendor.bio).strip())),
        ('Profile image', bool(vendor.profile_image)),
        ('Phone', bool(vendor.phone and str(vendor.phone).strip())),
    ]

    has_gallery = vendor.media_images.exists()
    has_videos = vendor.media_videos.exists()
    required_checks.append(('Gallery images', has_gallery))
    required_checks.append(('YouTube videos', has_videos))

    missing = [label for label, ok in required_checks if not ok]
    return {
        'profile_complete': len(missing) == 0,
        'missing_profile_fields': missing,
    }


class VendorSignupView(CreateView):
    """Handle vendor signup based on vendor type"""
    template_name = 'vendors/signup.html'
    
    def get_form_class(self):
        vendor_type = self.kwargs.get('vendor_type')
        if vendor_type == 'musician':
            return MusicianSignupForm
        elif vendor_type == 'caricaturist':
            return CaricaturistSignupForm
        elif vendor_type == 'photographer':
            return PhotographerSignupForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor_type'] = self.kwargs.get('vendor_type')
        return context
    
    def form_valid(self, form):
        vendor_type = self.kwargs.get('vendor_type')
        password = form.cleaned_data.get('password')

        try:
            with transaction.atomic():
                # Create user account
                user = CustomUser.objects.create_user(
                    email=form.cleaned_data.get('email'),
                    username=form.cleaned_data.get('email'),
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name'),
                    password=password,
                    user_type='vendor',
                    is_vendor=True,
                    phone=form.cleaned_data.get('phone'),
                )

                # Create vendor profile
                vendor = form.save(commit=False)
                vendor.user = user
                vendor.vendor_type = vendor_type
                vendor.save()
        except IntegrityError:
            form.add_error('email', 'An account with this email already exists. Please log in instead.')
            return self.form_invalid(form)
        
        # Log user in
        user = authenticate(email=user.email, password=password)
        if user is None:
            user = authenticate(username=user.email, password=password)
        if user is not None:
            login(self.request, user)
        
        return redirect('vendors:vendor_dashboard')


@method_decorator(login_required, name='dispatch')
class VendorDashboardView(ListView):
    """Display vendor dashboard with enquiries"""
    template_name = 'vendors/dashboard.html'
    context_object_name = 'enquiries'
    paginate_by = 10
    
    def get_queryset(self):
        vendor = get_vendor_for_user(self.request.user)
        if vendor is None:
            from apps.bookings.models import Enquiry
            return Enquiry.objects.none()
        
        from apps.bookings.models import Enquiry
        return Enquiry.objects.filter(vendor=vendor).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vendor = get_vendor_for_user(self.request.user)
        context['vendor'] = vendor
        completion = get_profile_completion(vendor)
        context['profile_complete'] = completion['profile_complete']
        context['missing_profile_fields'] = completion['missing_profile_fields']

        from apps.bookings.models import Enquiry
        enquiries = Enquiry.objects.filter(vendor=vendor) if vendor is not None else Enquiry.objects.none()
        context['total_enquiries'] = enquiries.count()
        context['viewed_enquiries'] = enquiries.filter(vendor_viewed=True).count()
        context['pending_enquiries'] = enquiries.filter(vendor_response='pending').count()
        context['pending_profile_request'] = (
            VendorProfileUpdateRequest.objects
            .filter(vendor=vendor, status=VendorProfileUpdateRequest.STATUS_PENDING)
            .first() if vendor is not None else None
        )
        context['gallery_images'] = vendor.media_images.all()[:10] if vendor is not None else []
        context['gallery_videos'] = vendor.media_videos.all()[:4] if vendor is not None else []
        video_links = [item.youtube_url for item in context['gallery_videos']]
        while len(video_links) < 4:
            video_links.append('')
        context['video_links'] = video_links
        
        return context


@method_decorator(login_required, name='dispatch')
class VendorProfileUpdateView(UpdateView):
    """Allow vendor to update their profile"""
    template_name = 'vendors/profile_edit.html'
    
    def get_object(self):
        vendor = get_vendor_for_user(self.request.user)
        if vendor is None:
            raise Http404('Vendor profile not found for this account.')
        return vendor
    
    def get_form_class(self):
        vendor = get_vendor_for_user(self.request.user)

        if isinstance(vendor, Musician):
            return MusicianSignupForm
        elif isinstance(vendor, Caricaturist):
            return CaricaturistSignupForm
        elif isinstance(vendor, Photographer):
            return PhotographerSignupForm
        raise Http404('Vendor profile not found for this account.')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_profile_edit'] = True
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()
        context['gallery_images'] = vendor.media_images.all()[:10]
        context['main_gallery_image'] = vendor.media_images.filter(is_primary=True).first() or vendor.media_images.first()
        context['gallery_videos'] = vendor.media_videos.all()[:4]
        video_links = [item.youtube_url for item in context['gallery_videos']]
        while len(video_links) < 4:
            video_links.append('')
        context['video_links'] = video_links
        context['pending_profile_request'] = (
            VendorProfileUpdateRequest.objects
            .filter(vendor=vendor, status=VendorProfileUpdateRequest.STATUS_PENDING)
            .first()
        )
        context['locked_profile_values'] = {
            'number_of_members': vendor.number_of_members,
            'home_county': vendor.home_county,
            'home_country': vendor.home_country,
        }
        return context

    @staticmethod
    def _normalize_youtube_url(url):
        url = (url or '').strip()
        if not url:
            return ''
        if 'youtube.com/watch?v=' in url or 'youtu.be/' in url or 'youtube.com/shorts/' in url:
            return url
        return ''

    @staticmethod
    def _json_safe_value(value):
        if isinstance(value, Decimal):
            return str(value)
        if hasattr(value, 'isoformat'):
            try:
                return value.isoformat()
            except TypeError:
                pass
        return value

    def form_valid(self, form):
        vendor = self.get_object()
        editable_field_names = {f.name for f in vendor._meta.fields}
        payload = {}

        for key, value in form.cleaned_data.items():
            if key not in editable_field_names or key in {'id', 'user', 'vendor_ptr'}:
                continue
            if key == 'profile_image':
                continue
            if isinstance(value, list):
                payload[key] = ', '.join(str(item) for item in value)
            else:
                payload[key] = self._json_safe_value(value)

        youtube_links = []
        for raw_link in self.request.POST.getlist('youtube_links'):
            cleaned = self._normalize_youtube_url(raw_link)
            if cleaned:
                youtube_links.append(cleaned)

        if len(youtube_links) > 4:
            form.add_error(None, 'You can add up to 4 YouTube links.')
            return self.form_invalid(form)

        uploaded_gallery = self.request.FILES.getlist('gallery_images')
        if len(uploaded_gallery) > 10:
            form.add_error(None, 'You can upload up to 10 gallery images.')
            return self.form_invalid(form)

        existing_order = [x for x in self.request.POST.get('existing_gallery_order', '').split(',') if x.strip()]
        existing_primary = self.request.POST.get('existing_primary_id', '').strip()
        primary_new_index = self.request.POST.get('new_primary_index', '').strip()

        with transaction.atomic():
            pending_request, _ = VendorProfileUpdateRequest.objects.update_or_create(
                vendor=vendor,
                status=VendorProfileUpdateRequest.STATUS_PENDING,
                defaults={
                    'requested_by': self.request.user,
                    'field_data': payload,
                    'review_notes': '',
                },
            )

            if form.cleaned_data.get('profile_image'):
                pending_request.pending_profile_image = form.cleaned_data['profile_image']
                pending_request.save(update_fields=['pending_profile_image'])

            pending_request.draft_images.all().delete()
            pending_request.draft_videos.all().delete()

            if uploaded_gallery:
                new_files = list(uploaded_gallery)
                ordered_indexes = []
                if self.request.POST.get('new_gallery_order'):
                    for raw_idx in self.request.POST.get('new_gallery_order', '').split(','):
                        raw_idx = raw_idx.strip()
                        if raw_idx.isdigit():
                            ordered_indexes.append(int(raw_idx))
                if not ordered_indexes:
                    ordered_indexes = list(range(len(new_files)))

                valid_indexes = [idx for idx in ordered_indexes if 0 <= idx < len(new_files)]
                seen = set(valid_indexes)
                for idx in range(len(new_files)):
                    if idx not in seen:
                        valid_indexes.append(idx)

                for order, idx in enumerate(valid_indexes):
                    VendorProfileImageDraft.objects.create(
                        update_request=pending_request,
                        image=new_files[idx],
                        sort_order=order,
                        is_primary=str(idx) == primary_new_index,
                    )
            else:
                current_images = {str(item.id): item for item in vendor.media_images.all()}
                ordered_ids = [img_id for img_id in existing_order if img_id in current_images]
                if not ordered_ids:
                    ordered_ids = [str(item.id) for item in vendor.media_images.all()]
                for order, image_id in enumerate(ordered_ids):
                    source = current_images[image_id]
                    VendorProfileImageDraft.objects.create(
                        update_request=pending_request,
                        image=source.image,
                        sort_order=order,
                        is_primary=image_id == existing_primary,
                    )

            for order, link in enumerate(youtube_links):
                VendorProfileVideoDraft.objects.create(
                    update_request=pending_request,
                    youtube_url=link,
                    sort_order=order,
                )

        messages.success(self.request, 'Profile changes submitted for admin approval.')
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('vendors:vendor_dashboard')


def vendor_list_public(request):
    """Display public list of all approved vendors"""
    musicians = Musician.objects.filter(is_active=True, is_approved=True)
    caricaturists = Caricaturist.objects.filter(is_active=True, is_approved=True)
    photographers = Photographer.objects.filter(is_active=True, is_approved=True)
    
    return render(request, 'vendors/vendor_list_public.html', {
        'musicians': musicians,
        'caricaturists': caricaturists,
        'photographers': photographers,
    })
