from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Enquiry, EnquiryNotification, ReviewRequest


class Command(BaseCommand):
    help = 'Send post-event review request emails 3 days after booked event dates.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        eligible_date = today - timedelta(days=3)
        sent_count = 0

        enquiries = (
            Enquiry.objects
            .filter(status='booked', event_date__lte=eligible_date)
            .select_related('vendor', 'customer_user')
        )

        for enquiry in enquiries:
            scheduled_dt = timezone.make_aware(
                datetime.combine(enquiry.event_date + timedelta(days=3), datetime.min.time())
            )
            review_request, _ = ReviewRequest.objects.get_or_create(
                enquiry=enquiry,
                defaults={
                    'vendor': enquiry.vendor,
                    'customer_name': enquiry.customer_name,
                    'customer_email': enquiry.customer_email,
                    'scheduled_send_at': scheduled_dt,
                },
            )

            if review_request.email_sent:
                continue

            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
            review_link = f"{site_url}{reverse('bookings:submit_review', kwargs={'token': review_request.token})}"

            html_message = render_to_string(
                'bookings/emails/review_request.html',
                {
                    'customer_name': review_request.customer_name,
                    'vendor_name': enquiry.vendor.public_name,
                    'event_date': enquiry.event_date,
                    'review_link': review_link,
                },
            )

            try:
                send_mail(
                    subject=f"How was your event with {enquiry.vendor.public_name}?",
                    message='',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[review_request.customer_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                now = timezone.now()
                review_request.email_sent = True
                review_request.sent_at = now
                review_request.save(update_fields=['email_sent', 'sent_at'])

                EnquiryNotification.objects.create(
                    enquiry=enquiry,
                    notification_type='customer_review_request',
                    recipient_email=review_request.customer_email,
                    recipient_name=review_request.customer_name,
                    sent=True,
                    sent_date=now,
                )

                sent_count += 1
            except Exception as exc:
                self.stderr.write(
                    self.style.WARNING(
                        f"Failed to send review request for enquiry #{enquiry.id}: {exc}"
                    )
                )

        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} review request email(s).'))
