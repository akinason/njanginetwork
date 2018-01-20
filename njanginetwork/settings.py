"""
Django settings for njanginetwork project.

Generated by 'django-admin startproject' using Django 2.0.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qibts7+4ws=xwy3%s2sku2g_^vuooodqzy_l%x9c5qj0n=$k$i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']



# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',
    'main.apps.MainConfig',
    'mptt',
    'njangi.apps.NjangiConfig',
    'purse.apps.PurseConfig',
    'django.contrib.admin',
    'mailer.apps.MailerConfig',
    'django.contrib.humanize',
    'phonenumber_field',
]

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'njanginetwork.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages',
                'njangi.context_processors.njangi_context_processors',
                'main.context_processors.main_context_processors',
            ],
        },
    },
]

WSGI_APPLICATION = 'njanginetwork.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'njangi',
        'USER': 'viicha',
        'PASSWORD': 'viicha',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Authentication user model
AUTH_USER_MODEL = 'main.User'


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

LOGIN_REDIRECT_URL = reverse_lazy('njangi:dashboard')
LOGIN_URL = '/login'
# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)

ugettext = lambda s: s
LANGUAGES = (
   ('en', _('English')),
   ('fr', _('French')),
)

PHONENUMBER_DB_FORMAT = 'E164'
PHONENUMBER_DEFAULT_REGION = 'CM'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

PROFILE_PICTURE_PATH = 'media/main/profile/%Y/%m/%d/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (BASE_DIR + '/static/',)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# Email Configurations.
DEFAULT_FROM_EMAIL = 'contact@njanginetwork.com'
EMAIL_USE_TLS = True
EMAIL_HOST = 'mail.privateemail.com'
EMAIL_HOST_USER = 'contact@njanginetwork.com'
EMAIL_HOST_PASSWORD = '*45H0KRs$1.F.'
EMAIL_PORT = 587
ADMIN_EMAIL = 'admin@njanginetwork.com'
CONTACT_EMAIL = 'contact@njanginetwork.com'
SUPPORT_EMAIL = 'contact@njanginetwork.com'


# MTN Mobile Money API configuration by webshinobis.com
# APIs return JSON response. params = {status, message, amount, phoneNumber, transactionId, transactionDate}
MOMO_CHECKOUT_URL = 'http://api.webshinobis.com/api/v1/momo/checkout'
MOMO_PAYMENT_URL = 'http://api.webshinobis.com/api/v1/momo/pay'
MOMO_AUTH_EMAIL = 'fenn25.fn@gmail.com'
MOMO_AUTH_PASSWORD = 'secret'

# REDIS related settings
REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'

#*******************************
# Twilio Configurations
#*******************************

TWILIO_ACCOUNT_SID ='AC31b924ed5ed23f93f3a66ae17ad86690'
TWILIO_AUTH_TOKEN = 'b0f9c38904c0ad7fb8a126e75e3b019f'
TWILIO_PHONE_NUMBER = '+14154293468'
TWILIO_VERIFIED_NUMBER = '+237675397307'


if DEBUG:
    INSTALLED_APPS += ['debug_toolbar',]
    INTERNAL_IPS = ['localhost', '127.0.0.1']
    # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware',]
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
    SHOW_TOOLBAR_CALLBACK = True