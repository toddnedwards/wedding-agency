from django.template import Context, Template
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage


class AgencyPriceFilterTests(SimpleTestCase):
    def test_adds_agency_fee_and_rounds_up_to_a_whole_pound(self):
        template = Template('{% load pricing %}{{ price|agency_price }}')

        self.assertEqual(template.render(Context({'price': '100.00'})), '120')
        self.assertEqual(template.render(Context({'price': '100.01'})), '121')


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
        self.assertEqual(mail.outbox[0].to, ['info@thebestentertainment.com'])
        self.assertEqual(mail.outbox[0].reply_to, ['taylor@example.com'])