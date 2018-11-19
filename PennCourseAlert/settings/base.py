"""
Django settings for PennCourseAlert project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v*l-%3la#%a_)r8m4%5oz9l#v+b&$r)0lje8%gj5&7_uk!0@3@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('MODE', 'dev') != 'prod'

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pca.apps.PcaConfig',
    'shortener.apps.ShortenerConfig',
    'options.apps.OptionsConfig',
    'django_extensions',
    'django_celery_results',
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'PennCourseAlert.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PennCourseAlert.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(default='mysql://pca:password@127.0.0.1:3306/pca')
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

API_KEY = os.environ.get('API_KEY', '')
API_SECRET = os.environ.get('API_SECRET', '')
API_URL = 'https://esb.isc-seo.upenn.edu/8091/open_data/course_section_search'

BASE_URL = 'https://penncoursealert.com'

SMTP_HOST = os.environ.get('SMTP_HOST', 'email-smtp.us-east-1.amazonaws.com')
SMTP_PORT = os.environ.get('SMTP_PORT', 587)
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

TWILIO_SID = os.environ.get('TWILIO_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_TOKEN', '')
TWILIO_NUMBER = os.environ.get('TWILIO_NUMBER', '+12153984277')

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost')

MESSAGE_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost')
CELERY_RESULT_BACKEND = 'django-db'
task_routes = {
    'pca.tasks.load_courses': 'default',
    'pca.tasks.prepare_alerts': 'default',
    'pca.tasks.send_alerts_for': 'default',
    'pca.tasks.demo_task': 'default',
    'pca.tasks.demo_alert': 'alerts',
    'pca.tasks.send_alert': 'alerts',  # run alerts off a different queue so we can SCALE
}

SENTRY_KEY = os.environ.get('SENTRY_KEY', '')
