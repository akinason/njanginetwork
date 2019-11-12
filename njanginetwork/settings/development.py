from .base import *

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qibts7+4ws=xwy3%s2sku2g_^vuooodqzy_l%x9c5qj0n=$k$i'

ALLOWED_HOSTS = ['127.0.0.1', 'cm.localhost', 'localhost', 'e21c2aab.ngrok.io']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'njanginetwork',
        'USER': 'kinason',
        'PASSWORD': 'panama245',
        'HOST': '127.0.0.1',
        'PORT': '5432',
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
EMAIL_HOST_PASSWORD = 'panama245@'
EMAIL_PORT = 587
ADMIN_EMAIL = 'njanginetwork@gmail.com'
CONTACT_EMAIL = 'njanginetwork@gmail.com'
SUPPORT_EMAIL = 'njanginetwork@gmail.com'

# sms configurations (www.1s2u.com)
ONE_S_2_U_USERNAME = 'kinason42'
ONE_S_2_U_PASSWORD = 'web54126'
ONE_S_2_U_SEND_URL = 'https://api.1s2u.io/bulksms'

# REDIS related settings
REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
BROKER_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'

RECAPTCHA_PUBLIC_KEY = '6Ldsar4UAAAAAPwZVvUDylqognmnGUL01dEZ5Ygi'
RECAPTCHA_PRIVATE_KEY = '6Ldsar4UAAAAAGfvo9t5XvPopfOD2Dx0TNe7-6pI'
RECAPTCHA_REQUIRED_SCORE = 0.85

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
