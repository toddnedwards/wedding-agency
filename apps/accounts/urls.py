from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    # Customer signup and login
    path('signup/', views.CustomerSignupView.as_view(), name='customer_signup'),
    path('login/', views.customer_login, name='customer_login'),
    path('logout/', views.customer_logout, name='customer_logout'),
    
    # Vendor signup choice
    path('vendor/signup/choose/', views.VendorSignupChoiceView.as_view(), name='vendor_signup_choice'),
]
