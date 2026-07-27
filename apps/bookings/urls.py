from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Vendor listing
    path('vendors/<str:vendor_type>/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/<str:vendor_type>/<int:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    
    # Enquiries
    path('vendors/<str:vendor_type>/<int:vendor_id>/enquiry/', views.EnquiryCreateView.as_view(), name='create_enquiry'),
    path('enquiry/confirmation/', views.enquiry_confirmation, name='enquiry_confirmation'),
    path('my-enquiries/', views.my_enquiries, name='my_enquiries'),
    path('enquiry/<int:pk>/', views.enquiry_detail, name='enquiry_detail'),
]
