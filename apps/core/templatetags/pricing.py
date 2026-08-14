from decimal import Decimal, InvalidOperation, ROUND_CEILING

from django import template


register = template.Library()


@register.filter
def agency_price(value):
    """Add the agency fee and round the customer price up to a whole pound."""
    try:
        price = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return ''

    return int((price * Decimal('1.20')).quantize(Decimal('1'), rounding=ROUND_CEILING))