from pathlib import Path
from decouple import config
import os
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = config('SECRET_KEY', default='change-me-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=lambda v: [s.strip() for s in v.split(',')])
INSTALLED_APPS = [
'django.contrib.admin',
'django.contrib.auth',
'django.contrib.contenttypes',
'django.contrib.sessions',
'django.contrib.messages',
'django.contrib.staticfiles',
# Third party
'corsheaders',
'ninja',
'django_filters',
'health_check',
'health_check.db',
'health_check.cache',
'health_check.storage',
'auditlog',
'guardian',
'cachalot',
'silk',
'django_extensions',
'debug_toolbar',

# Local apps
'apps.core',
'apps.business',
'apps.analytics',
]
MIDDLEWARE = [
'django.middleware.security.SecurityMiddleware',
'debug_toolbar.middleware.DebugToolbarMiddleware',
'corsheaders.middleware.CorsMiddleware',
'django.contrib.sessions.middleware.SessionMiddleware',
'django.middleware.locale.LocaleMiddleware',
'silk.middleware.SilkyMiddleware',
'django.middleware.common.CommonMiddleware',
'django.middleware.csrf.CsrfViewMiddleware',
'django.contrib.auth.middleware.AuthenticationMiddleware',
'apps.core.middleware.IdentityServiceMiddleware',  # JWT validation
'apps.core.middleware.AuditMiddleware',  # Audit fields population
'django.contrib.messages.middleware.MessageMiddleware',
'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
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
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='main_database'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
    }
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Guardian Configuration
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)
AUTH_PASSWORD_VALIDATORS = [
{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Internationalization - French primary market with German and English support
LANGUAGES = [
    ('fr', 'Français'),      # Primary language - French market
    ('de', 'Deutsch'),       # German support
    ('en', 'English'),       # English translation
]

# Localization paths
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:5173', cast=lambda v: [s.strip() for s in v.split(',')])

# Django Ninja Configuration
# API configuration is handled in config/ninja_api.py

# Debug Toolbar Configuration (only show in DEBUG mode)
if DEBUG:
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    
# Silk Configuration
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True

# Identity Service Configuration
IDENTITY_SERVICE_URL = config('IDENTITY_SERVICE_URL', default='http://localhost:8001')
JWT_CACHE_TIMEOUT = config('JWT_CACHE_TIMEOUT', default=300, cast=int)  # 5 minutes
JWT_SKIP_PATHS = [
    '/admin/',
    '/health/',
    '/api/docs/',
    '/api/openapi.json',
    '/static/',
    '/media/',
    '/silk/',
    '__debug__/',
]