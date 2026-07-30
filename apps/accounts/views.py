from django.shortcuts import render, redirect
from django.views.generic import CreateView, FormView
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy
from .forms import CustomerSignupForm, CustomerLoginForm, VendorTypeChoiceForm
from .models import CustomUser


class CustomerSignupView(CreateView):
    """Handle customer signup"""
    form_class = CustomerSignupForm
    template_name = 'accounts/customer_signup.html'
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        password = form.cleaned_data.get('password')
        
        # Create user
        user = CustomUser.objects.create_user(
            email=form.cleaned_data.get('email'),
            username=form.cleaned_data.get('email'),
            first_name=form.cleaned_data.get('first_name'),
            last_name=form.cleaned_data.get('last_name'),
            password=password,
            user_type='customer',
            phone=form.cleaned_data.get('phone'),
        )
        
        # Log user in
        user = authenticate(email=user.email, password=password)
        if user is None:
            user = authenticate(username=user.email, password=password)
        if user is not None:
            login(self.request, user)
        
        return super().form_valid(form)


class VendorSignupChoiceView(FormView):
    """Let user choose vendor type before signup"""
    form_class = VendorTypeChoiceForm
    template_name = 'accounts/vendor_signup_choice.html'
    
    def form_valid(self, form):
        vendor_type = form.cleaned_data.get('vendor_type')
        return redirect('vendors:vendor_signup', vendor_type=vendor_type)


def customer_login(request):
    """Handle customer login"""
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            user = authenticate(request, email=email, password=password)
            if user is None:
                user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid email or password.')
    else:
        form = CustomerLoginForm()
    
    return render(request, 'accounts/customer_login.html', {'form': form})


def customer_logout(request):
    """Handle customer logout"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')
