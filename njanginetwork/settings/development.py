from .base import *

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.get('NJANGINETWORK', 'SECRET_KEY')

ALLOWED_HOSTS = ['127.0.0.1', 'cm.localhost', 'localhost', 'e21c2aab.ngrok.io']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'njanginetwork',
        'USER': config.get('DATABASE_DEV', 'DB_USERNAME'),
        'PASSWORD': config.get('DATABASE_DEV', 'DB_PASSWORD'),
        'HOST': config.get('DATABASE_DEV', 'DB_HOST'),
        'PORT': config.get('DATABASE_DEV', 'DB_PORT'),
        'CONN_MAX_AGE': 5,
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/


PROFILE_PICTURE_PATH = 'media/main/profile/%Y/%m/%d/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = "/var/www/html/njangi.network/static/"
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
DEFAULT_FROM_EMAIL = 'njanginetwork@gmail.com'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'njanginetwork@gmail.com'
EMAIL_HOST_PASSWORD = config.get('EMAIL', 'EMAIL_HOST_PASSWORD')
EMAIL_PORT = 587
ADMIN_EMAIL = 'njanginetwork@gmail.com'
CONTACT_EMAIL = 'njanginetwork@gmail.com'
SUPPORT_EMAIL = 'njanginetwork@gmail.com'

# sms configurations (www.1s2u.com)
ONE_S_2_U_USERNAME = config.get('SMS', 'ONE_S_2_U_USERNAME')
ONE_S_2_U_PASSWORD = config.get('SMS', 'ONE_S_2_U_PASSWORD')
ONE_S_2_U_SEND_URL = config.get('SMS', 'ONE_S_2_U_SEND_URL')

# REDIS related settings
REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'

RECAPTCHA_PUBLIC_KEY = config.get('RECAPTCHA', 'RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = config.get('RECAPTCHA', 'RECAPTCHA_PRIVATE_KEY')
RECAPTCHA_REQUIRED_SCORE = config.get('RECAPTCHA', 'RECAPTCHA_REQUIRED_SCORE')

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar', ]
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
