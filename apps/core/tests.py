from django.template import Context, Template
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from .email_delivery import send_contact_notification
from .email_backend import EmailBackend, IPv4SMTP, IPv4SMTPSSL
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

    def test_uses_ssl_client_when_implicit_ssl_is_enabled(self):
        backend = EmailBackend(use_ssl=True, use_tls=False)

        self.assertIs(backend.connection_class, IPv4SMTPSSL)

    def test_uses_starttls_client_when_implicit_ssl_is_disabled(self):
        backend = EmailBackend(use_ssl=False)

        self.assertIs(backend.connection_class, IPv4SMTP)


@override_settings(
    RESEND_API_KEY='re_test_key',
    RESEND_FROM_EMAIL='The Best Entertainment <info@thebestentertainment.co.uk>',
)
class ResendContactNotificationTests(SimpleTestCase):
    @patch('apps.core.email_delivery.urlopen')
    def test_sends_contact_notification_through_resend(self, urlopen):
        response = MagicMock(status=200)
        urlopen.return_value.__enter__.return_value = response
        contact_message = SimpleNamespace(
            name='Taylor Smith',
            email='taylor@example.com',
            phone='01234567890',
            subject='Wedding entertainment',
            message='Please send over some options.',
        )

        send_contact_notification(contact_message)

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.resend.com/emails')
        self.assertEqual(request.get_header('Authorization'), 'Bearer re_test_key')
        self.assertEqual(urlopen.call_args.kwargs['timeout'], 30)


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