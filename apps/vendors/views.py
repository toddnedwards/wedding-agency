from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from .models import Musician, Caricaturist, Photographer
from .forms import MusicianSignupForm, CaricaturistSignupForm, PhotographerSignupForm
from apps.accounts.models import CustomUser


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
        vendor.save()
        
        # Log user in
        user = authenticate(email=user.email, password=password)
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
        # Get vendor based on user type
        vendor_type = self.request.user.user_type
        
        if vendor_type == 'musician':
            vendor = get_object_or_404(Musician, user=self.request.user)
        elif vendor_type == 'caricaturist':
            vendor = get_object_or_404(Caricaturist, user=self.request.user)
        elif vendor_type == 'photographer':
            vendor = get_object_or_404(Photographer, user=self.request.user)
        else:
            return []
        
        from apps.bookings.models import Enquiry
        return Enquiry.objects.filter(vendor=vendor).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get vendor object
        vendor_type = self.request.user.user_type
        if vendor_type == 'musician':
            context['vendor'] = get_object_or_404(Musician, user=self.request.user)
        elif vendor_type == 'caricaturist':
            context['vendor'] = get_object_or_404(Caricaturist, user=self.request.user)
        elif vendor_type == 'photographer':
            context['vendor'] = get_object_or_404(Photographer, user=self.request.user)
        
        # Get stats
        from apps.bookings.models import Enquiry
        enquiries = Enquiry.objects.filter(vendor=context['vendor'])
        context['total_enquiries'] = enquiries.count()
        context['viewed_enquiries'] = enquiries.filter(vendor_viewed=True).count()
        context['pending_enquiries'] = enquiries.filter(vendor_response='pending').count()
        
        return context


@method_decorator(login_required, name='dispatch')
class VendorProfileUpdateView(UpdateView):
    """Allow vendor to update their profile"""
    template_name = 'vendors/profile_edit.html'
    
    def get_object(self):
        vendor_type = self.request.user.user_type
        
        if vendor_type == 'musician':
            return get_object_or_404(Musician, user=self.request.user)
        elif vendor_type == 'caricaturist':
            return get_object_or_404(Caricaturist, user=self.request.user)
        elif vendor_type == 'photographer':
            return get_object_or_404(Photographer, user=self.request.user)
    
    def get_form_class(self):
        vendor_type = self.request.user.user_type
        
        if vendor_type == 'musician':
            return MusicianSignupForm
        elif vendor_type == 'caricaturist':
            return CaricaturistSignupForm
        elif vendor_type == 'photographer':
            return PhotographerSignupForm
    
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
