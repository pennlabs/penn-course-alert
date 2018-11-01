# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
from django.conf import settings

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

__all__ = ('celery_app',)

sentry_url = 'https://786a5e2228a148808739b860cf792ce4@sentry.pennlabs.org/10'

if len(settings.SENTRY_KEY) > 0:
    sentry_url = 'https://786a5e2228a148808739b860cf792ce4:%s@sentry.pennlabs.org/10' % settings.SENTRY_KEY

sentry_sdk.init(sentry_url,
                integrations=[CeleryIntegration(), DjangoIntegration()])
