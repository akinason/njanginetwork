import os
from njanginetwork import BASE_DIR
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy
import environment
import configparser

config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'config.ini'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',
    'captcha',

    'main.apps.MainConfig',
    'feedback.apps.FeedbackConfig',
    'mptt',
    'njangi.apps.NjangiConfig',
    'purse.apps.PurseConfig',
    'marketplace',
    'jet.dashboard',
    'jet',
    'django.contrib.admin',
    'mailer.apps.MailerConfig',
    'django.contrib.humanize',
    'phonenumber_field',
    'mptt_graph.apps.MpttGraphConfig',
    'blog.apps.BlogConfig',
    'administration.apps.AdministrationConfig',
]

MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_session_timeout.middleware.SessionTimeoutMiddleware',
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
                'django.template.context_processors.media',
                # 'feedback.context_processor.post_feedback_response',
            ],
        },
    },
]

WSGI_APPLICATION = 'njanginetwork.wsgi.application'

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
    {
        'NAME': 'main.validators.ValidatePassword',
    },
]

LOGIN_REDIRECT_URL = reverse_lazy('njangi:dashboard')
LOGIN_URL = '/login'
# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)


def ugettext(s): return s


LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
)

SESSION_EXPIRE_SECONDS = 300  # 30 mins
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True

PHONENUMBER_DB_FORMAT = 'E164'

PHONENUMBER_DEFAULT_REGION = 'CM'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# These configuration will be deprecated sooner or later.
# START ===============================================

# MTN Mobile Money API configuration by webshinobis.com
# APIs return JSON response. params = {status, message, amount, phoneNumber, transactionId, transactionDate}

MOMO_CHECKOUT_URL = 'https://api.webshinobis.com/api/v1/momo/checkout'
MOMO_PAYMENT_URL = 'https://api.webshinobis.com/api/v1/momo/pay'
MOMO_AUTH_EMAIL = config.get('PAYMENT_GATEWAY', 'MOMO_AUTH_EMAIL')
MOMO_AUTH_PASSWORD = config.get('PAYMENT_GATEWAY', 'MOMO_AUTH_PASSWORD')

# ORANGE MONEY API Configurations
ORANGE_MONEY_CHECKOUT_URL = ''
ORANGE_MONEY_PAYMENT_URL = ''
ORANGE_MONEY_AUTH_EMAIL = ''
ORANGE_MONEY_AUTH_PASSWORD = ''

AFKANERD_MOMO_URL = 'https://gsmtools.afkanerd.com/api/'
AFKANERD_BASE_CALLBACK_URL = 'https://njanginetwork.com/purse/gsmtools/afkanerd/api/momo/'
AFKANERD_AUTH_SID = config.get('PAYMENT_GATEWAY', 'AFKANERD_AUTH_SID')
AFKANERD_AUTH_EMAIL = config.get('PAYMENT_GATEWAY', 'AFKANERD_AUTH_EMAIL')

# END=========================================================
