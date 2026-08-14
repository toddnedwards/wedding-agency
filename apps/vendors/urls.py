from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Vendor signup
    path('registration-guide/', views.VendorRequirementsGuideView.as_view(), name='requirements_guide'),
    path('signup/<str:vendor_type>/', views.VendorSignupView.as_view(), name='vendor_signup'),
    
    # Vendor dashboard
    path('dashboard/', views.VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('dashboard/toggle-date/', views.toggle_unavailable_date, name='toggle_unavailable_date'),
    
    # Vendor profile
    path('profile/edit/', views.VendorProfileUpdateView.as_view(), name='profile_edit'),
    
    # Public vendor list
    path('list/', views.vendor_list_public, name='vendor_list_public'),
]
