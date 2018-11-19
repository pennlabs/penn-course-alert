# Settings when deployed to Dokku
from .base import *  # noqa

# Disable Django's own staticfiles handling in favour of WhiteNoise, for
# greater consistency between gunicorn and `./manage.py runserver`. See:
# http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development

BASE_URL = 'https://penncoursealert.com'

INSTALLED_APPS.remove('django.contrib.staticfiles')
INSTALLED_APPS.extend([
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
])

MIDDLEWARE.remove('django.middleware.security.SecurityMiddleware')
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers (feel free to make this more specific)
ALLOWED_HOSTS = ['penncoursealert.com', 'www.penncoursealert.com']

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
