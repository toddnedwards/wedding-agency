import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMessage


def send_contact_notification(contact_message):
    subject = f'New Contact Form Submission: {contact_message.subject}'
    body = (
        f'From: {contact_message.name} ({contact_message.email})\n'
        f'Phone: {contact_message.phone}\n\n{contact_message.message}'
    )

    if not settings.RESEND_API_KEY:
        EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
            reply_to=[contact_message.email],
        ).send(fail_silently=False)
        return

    payload = json.dumps({
        'from': settings.RESEND_FROM_EMAIL,
        'to': [settings.CONTACT_EMAIL],
        'subject': subject,
        'text': body,
        'reply_to': [contact_message.email],
    }).encode()
    request = Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {settings.RESEND_API_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f'Resend returned HTTP {response.status}.')
    except HTTPError as error:
        details = error.read().decode(errors='replace')
        raise RuntimeError(f'Resend returned HTTP {error.code}: {details}') from error
    except URLError as error:
        raise RuntimeError(f'Could not reach Resend: {error.reason}') from error