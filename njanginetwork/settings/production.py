from .base import *

DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'qibts7+4ws=xwy3%s2sku2g_^vuooodqzy_l%x9c5qj0n=$k$i'

ALLOWED_HOSTS = ['104.236.225.69', 'www.njanginetwork.com',
                 'njanginetwork.com', '127.0.0.1', 'localhost']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'njangi',
        'USER': config.get('DATABASE_PRO', 'DB_USERNAME'),
        'PASSWORD': config.get('DATABASE_PRO', 'DB_PASSWORD'),
        'HOST': config.get('DATABASE_PRO', 'DB_HOST'),
        'PORT': config.get('DATABASE_PRO', 'DB_PORT'),
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
EMAIL_HOST_PASSWORD = config.get('EMAIL', 'EMAIL_HOST_PASSWORD')
EMAIL_PORT = 587
ADMIN_EMAIL = 'njanginetwork@gmail.com'
CONTACT_EMAIL = 'njanginetwork@gmail.com'
SUPPORT_EMAIL = 'njanginetwork@gmail.com'

# sms configurations (www.1s2u.com)
ONE_S_2_U_USERNAME = config.get('SMS', 'ONE_S_2_U_USERNAME')
ONE_S_2_U_PASSWORD = config.get('SMS', 'ONE_S_2_U_PASSWORD')
ONE_S_2_U_SEND_URL = config.get('SMS', 'ONE_S_2_U_SEND_URL')

# CELERY related settings
CELERY_BROKER_URL = 'amqp://localhost'

RECAPTCHA_PUBLIC_KEY = config.get('RECAPTCHA', 'RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = config.get('RECAPTCHA', 'RECAPTCHA_PRIVATE_KEY')
RECAPTCHA_REQUIRED_SCORE = config.get('RECAPTCHA', 'RECAPTCHA_REQUIRED_SCORE')
