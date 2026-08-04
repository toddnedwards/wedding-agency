from django import template
from django.urls import reverse

from apps.bookings.models import Enquiry
from apps.vendors.models import VendorProfileUpdateRequest

register = template.Library()


@register.inclusion_tag("admin/includes/notifications_panel.html", takes_context=True)
def admin_notifications_panel(context):
    """Render admin dashboard alerts for fresh enquiries and pending profile updates."""
    new_enquiries = (
        Enquiry.objects.filter(admin_notified=False)
        .select_related("vendor")
        .order_by("-created_at")
    )
    pending_updates = (
        VendorProfileUpdateRequest.objects.filter(status=VendorProfileUpdateRequest.STATUS_PENDING)
        .select_related("vendor")
        .order_by("-submitted_at")
    )

    return {
        "new_enquiries_count": new_enquiries.count(),
        "pending_updates_count": pending_updates.count(),
        "recent_new_enquiries": new_enquiries[:5],
        "recent_pending_updates": pending_updates[:5],
        "enquiries_url": f"{reverse('admin:bookings_enquiry_changelist')}?admin_notified__exact=0",
        "updates_url": f"{reverse('admin:vendors_vendorprofileupdaterequest_changelist')}?status__exact=pending",
        "request": context.get("request"),
    }
