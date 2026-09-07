from django.template import Context, Template
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .email_backend import IPv4SMTP
from .models import ContactMessage


class AgencyPriceFilterTests(SimpleTestCase):
    def test_adds_agency_fee_and_rounds_up_to_a_whole_pound(self):
        template = Template('{% load pricing %}{{ price|agency_price }}')

        self.assertEqual(template.render(Context({'price': '100.00'})), '120')
        self.assertEqual(template.render(Context({'price': '100.01'})), '121')


class IPv4SMTPTests(SimpleTestCase):
    @patch('apps.core.email_backend.socket.create_connection')
    @patch('apps.core.email_backend.socket.gethostbyname', return_value='172.65.255.143')
    def test_connects_to_the_ipv4_address(self, gethostbyname, create_connection):
        client = IPv4SMTP()
        gethostbyname.reset_mock()
        client._get_socket('smtp.hostinger.com', 587, 30)

        gethostbyname.assert_called_once_with('smtp.hostinger.com')
        create_connection.assert_called_once_with(('172.65.255.143', 587), 30, None)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ContactViewTests(TestCase):
    def test_contact_form_sends_to_contact_address(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Taylor Smith',
            'email': 'taylor@example.com',
            'phone': '01234567890',
            'subject': 'Wedding entertainment',
            'message': 'Please send over some options.',
        })

        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['info@thebestentertainment.co.uk'])
        self.assertEqual(mail.outbox[0].reply_to, ['taylor@example.com'])

    def test_contact_form_rejects_invalid_input_without_creating_message(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Taylor Smith',
            'email': 'not-an-email',
            'phone': '01234567890',
            'subject': 'Wedding entertainment',
            'message': 'Please send over some options.',
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)