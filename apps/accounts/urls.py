from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = 'accounts'

urlpatterns = [
    # Legacy customer signup path now redirects to vendor onboarding
    path('signup/', RedirectView.as_view(pattern_name='accounts:vendor_signup_choice', permanent=False), name='customer_signup'),
    path('login/', views.customer_login, name='customer_login'),
    path('vendor/login/', views.customer_login, name='vendor_login'),
    path('logout/', views.customer_logout, name='customer_logout'),
    
    # Vendor signup choice
    path('vendor/signup/choose/', views.VendorSignupChoiceView.as_view(), name='vendor_signup_choice'),
]
