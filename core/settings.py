from pathlib import Path
import os
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ON_VERCEL = bool(os.getenv('VERCEL'))
DEBUG = os.getenv('DJANGO_DEBUG', 'false').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if ON_VERCEL:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY is required on Vercel')
    SECRET_KEY = 'local-development-only-not-for-production'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,desonebackend.vercel.app').split(',')
if os.getenv('VERCEL_URL'):
    ALLOWED_HOSTS.append(os.environ['VERCEL_URL'])

INSTALLED_APPS = [
    'modeltranslation', 'django.contrib.admin', 'django.contrib.auth',
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
    'corsheaders', 'rest_framework', 'core',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'core.middleware.QueryParamsLocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'https://desone.vercel.app,http://localhost:5173,http://127.0.0.1:5173').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://desonebackend.vercel.app').split(',')
ROOT_URLCONF = 'core.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'core.wsgi.application'
if ON_VERCEL and not os.getenv('DATABASE_URL'):
    raise ImproperlyConfigured('DATABASE_URL is required; production cannot use SQLite')
DATABASES = {'default': dj_database_url.config(
    default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=0,
    conn_health_checks=True,
)}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
LANGUAGES = [('jp', 'Japanese'), ('en', 'English'), ('ru', 'Russian'), ('uz', 'Uzbek')]
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
if os.getenv('S3_ENDPOINT_URL'):
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'endpoint_url': os.environ['S3_ENDPOINT_URL'],
            'access_key': os.environ['S3_ACCESS_KEY_ID'],
            'secret_key': os.environ['S3_SECRET_ACCESS_KEY'],
            'bucket_name': os.getenv('S3_BUCKET_NAME', 'portfolio-media'),
            'region_name': os.getenv('S3_REGION_NAME', 'eu-central-1'),
            'signature_version': 's3v4', 'addressing_style': 'path',
            'default_acl': None, 'file_overwrite': False,
            'querystring_auth': True, 'querystring_expire': 3600,
        },
    }
elif ON_VERCEL:
    raise ImproperlyConfigured('S3_ENDPOINT_URL is required for persistent media')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = ON_VERCEL
CSRF_COOKIE_SECURE = ON_VERCEL
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@localhost')
EMAIL_BACKEND = ('django.core.mail.backends.smtp.EmailBackend' if EMAIL_HOST_PASSWORD
                 else 'django.core.mail.backends.dummy.EmailBackend')
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['core.authentication.AdminTokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['core.authentication.PublicReadAdminWrite'],
}
