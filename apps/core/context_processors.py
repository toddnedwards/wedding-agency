from django.conf import settings


def site_settings(request):
    return {
        'INDEXING_ENABLED': settings.INDEXING_ENABLED,
    }