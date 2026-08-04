from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.bookings.models import Enquiry
from apps.vendors.models import Musician
from apps.accounts.models import CustomUser


class EnquiryEmailFailureTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='vendor@example.com',
            email='vendor@example.com',
            password='testpass123',
            first_name='Vendor',
            last_name='User',
        )
        image = SimpleUploadedFile(
            'test.png',
            BytesIO(b'fake-image-content').getvalue(),
            content_type='image/png',
        )
        self.vendor = Musician.objects.create(
            user=self.user,
            vendor_type='musician',
            business_name='Test Band',
            bio='A test musician',
            profile_image=image,
            experience_years=3,
            hourly_rate='100.00',
            location='Test Location',
            phone='0123456789',
            is_active=True,
            is_approved=True,
        )

    @patch('apps.bookings.views.send_mail', side_effect=Exception('smtp failed'))
    def test_enquiry_submission_does_not_crash_when_email_fails(self, mock_send_mail):
        url = reverse('bookings:create_enquiry', kwargs={'vendor_type': 'musicians', 'vendor_id': self.vendor.id})
        response = self.client.post(
            url,
            {
                'customer_name': 'Test Customer',
                'customer_email': 'customer@example.com',
                'customer_phone': '0123456789',
                'event_date': '2026-10-01',
                'event_time': '19:00',
                'event_type': 'wedding',
                'event_location': 'Test Location',
                'venue_name': 'Test Venue',
                'county': 'Test County',
                'details': 'A test enquiry',
                'special_requirements': 'No special requirements',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your enquiry was received')
        self.assertTrue(Enquiry.objects.filter(customer_email='customer@example.com').exists())
