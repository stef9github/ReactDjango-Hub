from pathlib import Path
import environ
import os
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))
SECRET_KEY = env('SECRET_KEY', default='change-me-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])
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
'apps.analytics',
]
MIDDLEWARE = [
'django.middleware.security.SecurityMiddleware',
'debug_toolbar.middleware.DebugToolbarMiddleware',
'corsheaders.middleware.CorsMiddleware',
'django.contrib.sessions.middleware.SessionMiddleware',
'django.middleware.locale.LocaleMiddleware',
'silk.middleware.SilkMiddleware',
'django.middleware.common.CommonMiddleware',
'django.middleware.csrf.CsrfViewMiddleware',
'django.contrib.auth.middleware.AuthenticationMiddleware',
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
'default': env.db('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/main_database')
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
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
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:5173'])

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
