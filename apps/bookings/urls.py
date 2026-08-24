from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Vendor listing
    path('vendors/<str:vendor_type>/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/<str:vendor_type>/<slug:slug>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('vendors/<str:vendor_type>/<int:pk>/', views.vendor_detail_legacy_redirect, name='vendor_detail_legacy'),
    
    # Enquiries
    path('vendors/<str:vendor_type>/<int:vendor_id>/enquiry/', views.EnquiryCreateView.as_view(), name='create_enquiry'),
    path('enquiry/multi/', views.MultiActEnquiryView.as_view(), name='multi_act_enquiry'),
    path('enquiry/confirmation/', views.enquiry_confirmation, name='enquiry_confirmation'),
    path('funnel/event/', views.capture_funnel_event, name='capture_funnel_event'),
    path('review/<uuid:token>/', views.submit_review, name='submit_review'),
]
