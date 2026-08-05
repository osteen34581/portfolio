import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Read secret key from environment in production
SECRET_KEY = os.getenv('SECRET_KEY', 'replace-this-in-production')

# Use environment variable to toggle debug in production; default to True for now
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://localhost:8000', 'http://localhost:8000']

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    from urllib.parse import urlparse, unquote

    parsed_url = urlparse(DATABASE_URL)
    if parsed_url.scheme in ('postgres', 'postgresql'):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': parsed_url.path[1:],
                'USER': parsed_url.username or '',
                'PASSWORD': parsed_url.password or '',
                'HOST': parsed_url.hostname or '',
                'PORT': parsed_url.port or '',
            }
        }
    elif parsed_url.scheme == 'sqlite':
        db_path = unquote(parsed_url.path)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            }
        }
    else:
        raise RuntimeError(f'Unsupported DATABASE_URL scheme: {parsed_url.scheme}')
else:
    # Use a writable path in production environments like Vercel.
    default_db = BASE_DIR / 'db.sqlite3'
    if not DEBUG and os.getenv('VERCEL') == '1':
        default_db = Path('/tmp/db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': default_db,
        }
    }

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'notes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'voice_notes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'voice_notes.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Production static files (for collectstatic)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
