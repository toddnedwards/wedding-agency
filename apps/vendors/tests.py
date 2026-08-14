from django.contrib import admin
from django.test import SimpleTestCase

from apps.vendors.admin import VendorProfileUpdateRequestAdmin
from apps.vendors.models import VendorProfileUpdateRequest


class VendorProfileUpdateRequestAdminTests(SimpleTestCase):
    def test_field_data_summary_renders_separate_cards_for_each_value(self):
        admin_instance = VendorProfileUpdateRequestAdmin(VendorProfileUpdateRequest, admin.site)
        obj = VendorProfileUpdateRequest(field_data={
            'business_name': 'Sunset Events',
            'act_types': ['DJ', 'Singer'],
        })

        html = admin_instance.field_data_summary(obj)

        self.assertIn('Business Name', html)
        self.assertIn('Act Types', html)
        self.assertIn('Sunset Events', html)
        self.assertIn('DJ', html)
        self.assertIn('Singer', html)
        self.assertIn('vendor-update-field-card', html)
        self.assertNotIn("')('<div", html)
        self.assertNotIn("(',)", html)
