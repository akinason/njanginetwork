from .base import *

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qibts7+4ws=xwy3%s2sku2g_^vuooodqzy_l%x9c5qj0n=$k$i'

ALLOWED_HOSTS = ['104.236.225.69', 'www.njanginetwork.com', 'njanginetwork.com', '127.0.0.1', 'localhost']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'njangi',
        'USER': 'mihma',
        'PASSWORD': 'mihmaworld',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
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
EMAIL_HOST_PASSWORD = 'scoolings245'
EMAIL_PORT = 587
ADMIN_EMAIL = 'njanginetwork@gmail.com'
CONTACT_EMAIL = 'njanginetwork@gmail.com'
SUPPORT_EMAIL = 'njanginetwork@gmail.com'

# sms configurations (www.1s2u.com)
ONE_S_2_U_USERNAME = 'kinason42'
ONE_S_2_U_PASSWORD = 'web54126'
ONE_S_2_U_SEND_URL = 'https://api.1s2u.io/bulksms'

# CELERY related settings
CELERY_BROKER_URL = 'amqp://localhost'

RECAPTCHA_PUBLIC_KEY = '6Ldsar4UAAAAAPwZVvUDylqognmnGUL01dEZ5Ygi'
RECAPTCHA_PRIVATE_KEY = '6Ldsar4UAAAAAGfvo9t5XvPopfOD2Dx0TNe7-6pI'
RECAPTCHA_REQUIRED_SCORE = 0.85
