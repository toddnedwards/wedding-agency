from django import template
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate

from apps.bookings.models import Enquiry, FunnelEvent
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

    since = timezone.now() - timedelta(days=7)
    recent_funnel = FunnelEvent.objects.filter(created_at__gte=since)

    now = timezone.now()
    last_24h_start = now - timedelta(hours=24)
    prev_24h_start = now - timedelta(hours=48)

    last_24h_funnel = FunnelEvent.objects.filter(created_at__gte=last_24h_start)
    prev_24h_funnel = FunnelEvent.objects.filter(created_at__gte=prev_24h_start, created_at__lt=last_24h_start)

    card_clicks = recent_funnel.filter(event='vendor_card_click').count()
    availability_clicks = recent_funnel.filter(event='check_availability_click').count()
    multi_enquiry_clicks = recent_funnel.filter(event='multi_enquiry_click').count()
    enquiry_submits = recent_funnel.filter(event='enquiry_submit').count()

    conversion_rate = 0.0
    if availability_clicks > 0:
        conversion_rate = (enquiry_submits / availability_clicks) * 100

    last_24h_submits = last_24h_funnel.filter(event='enquiry_submit').count()
    prev_24h_submits = prev_24h_funnel.filter(event='enquiry_submit').count()
    submit_delta = last_24h_submits - prev_24h_submits

    type_breakdown = []
    for vendor_type in ('musicians', 'caricaturists', 'photographers'):
        type_events = recent_funnel.filter(vendor_type=vendor_type)
        type_availability_clicks = type_events.filter(event='check_availability_click').count()
        type_submits = type_events.filter(event='enquiry_submit').count()

        type_rate = 0.0
        if type_availability_clicks > 0:
            type_rate = (type_submits / type_availability_clicks) * 100

        type_breakdown.append(
            {
                'vendor_type': vendor_type,
                'label': vendor_type.replace('_', ' ').title(),
                'availability_clicks': type_availability_clicks,
                'submits': type_submits,
                'rate': type_rate,
            }
        )

    grouped = (
        recent_funnel.filter(event='enquiry_submit')
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )
    grouped_map = {item['day']: item['total'] for item in grouped}

    daily_submit_series = []
    series_max = 1
    start_day = timezone.localdate() - timedelta(days=6)
    for i in range(7):
        day = start_day + timedelta(days=i)
        total = grouped_map.get(day, 0)
        if total > series_max:
            series_max = total
        daily_submit_series.append(
            {
                'day_label': day.strftime('%a'),
                'total': total,
            }
        )

    for point in daily_submit_series:
        point['height_pct'] = int((point['total'] / series_max) * 100) if series_max else 0

    return {
        "new_enquiries_count": new_enquiries.count(),
        "pending_updates_count": pending_updates.count(),
        "recent_new_enquiries": new_enquiries[:5],
        "recent_pending_updates": pending_updates[:5],
        "enquiries_url": f"{reverse('admin:bookings_enquiry_changelist')}?admin_notified__exact=0",
        "updates_url": f"{reverse('admin:vendors_vendorprofileupdaterequest_changelist')}?status__exact=pending",
        "funnel_events_url": reverse('admin:bookings_funnelevent_changelist'),
        "funnel_window_label": "Last 7 days",
        "funnel_card_clicks": card_clicks,
        "funnel_availability_clicks": availability_clicks,
        "funnel_multi_enquiry_clicks": multi_enquiry_clicks,
        "funnel_enquiry_submits": enquiry_submits,
        "funnel_conversion_rate": conversion_rate,
        "funnel_last_24h_submits": last_24h_submits,
        "funnel_prev_24h_submits": prev_24h_submits,
        "funnel_submit_delta": submit_delta,
        "funnel_type_breakdown": type_breakdown,
        "funnel_daily_submit_series": daily_submit_series,
        "request": context.get("request"),
    }
