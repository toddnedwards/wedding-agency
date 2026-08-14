from django.template import Context, Template
from django.test import SimpleTestCase


class AgencyPriceFilterTests(SimpleTestCase):
    def test_adds_agency_fee_and_rounds_up_to_a_whole_pound(self):
        template = Template('{% load pricing %}{{ price|agency_price }}')

        self.assertEqual(template.render(Context({'price': '100.00'})), '120')
        self.assertEqual(template.render(Context({'price': '100.01'})), '121')