"""
Django settings for config project.
"""

from pathlib import Path
import os
import sys

def clean_env_bool(val, default=False):
    """Limpia y castea de forma ultra-robusta valores booleanos desde variables de entorno (p. ej. en Dokploy)."""
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    cleaned = str(val).strip().strip('\'"').lower()
    if cleaned in ('1', 'true', 't', 'yes', 'y', 'on', 'si', 's', 'activo', 'habilitado'):
        return True
    if cleaned in ('0', 'false', 'f', 'no', 'n', 'off', 'inactivo', 'deshabilitado', ''):
        return False
    return default

# Limpiamos posibles comillas accidentales de variables de entorno (p. ej. en Dokploy)
def clean_env_list(env_val):
    if not env_val:
        return []
    if isinstance(env_val, list):
        return env_val
    return [item.strip().strip('\'"[]') for item in str(env_val).split(',') if item.strip()]

try:
    from decouple import config, Csv
except ImportError:
    def config(name, default=None, cast=None):
        val = os.environ.get(name, default)
        if cast == clean_env_bool or cast == bool:
            return clean_env_bool(val, default=default if isinstance(default, bool) else False)
        if cast == list or (isinstance(cast, type) and cast.__name__ == '<lambda>'):
             return clean_env_list(val)
        if cast == Csv:
            return clean_env_list(val)
        return val
    def Csv():
        return list
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=clean_env_bool)
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

ALLOWED_HOSTS = clean_env_list(config('ALLOWED_HOSTS', default='jardines.gobiernoriocuarto.gob.ar,jardinesdev.gobiernoriocuarto.gob.ar,localhost,127.0.0.1,*'))

CSRF_TRUSTED_ORIGINS = clean_env_list(config('CSRF_TRUSTED_ORIGINS', default='https://jardines.gobiernoriocuarto.gob.ar,https://jardinesdev.gobiernoriocuarto.gob.ar,https://datos.riocuarto.gov.ar'))

# Configuración para permitir incrustación en iFrames / Tableros
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='ALLOWALL')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    # 'django_cron',
    'users',
    'jardines',
    'alumnos',
    'formularios',
    'cobros',
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "config.middleware.MaintenanceModeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "users.middleware.BloquearAdminADocentesMiddleware",
    "users.middleware_audit.CurrentUserMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default=''),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=3306, cast=int),
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'ssl': {'ssl_disabled': True},
            'connect_timeout': 5,
            'init_command': "SET SESSION sql_mode=CONCAT(@@sql_mode, ',STRICT_TRANS_TABLES')",
        }
    }
}


# Support DATABASE_URL if provided (ej: sqlite:///db.sqlite3 para dev)
db_url = config('DATABASE_URL', default='')
if db_url:
    DATABASES['default'] = dj_database_url.parse(db_url, conn_max_age=60, ssl_require=False)

# Blindar estos valores — dj_database_url.parse puede pisar CONN_MAX_AGE
DATABASES['default']['CONN_MAX_AGE'] = 0

# Garantizar charset, SSL y strict mode para MySQL/MariaDB
if DATABASES['default'].get('ENGINE') == 'django.db.backends.mysql':
    opts = DATABASES['default'].setdefault('OPTIONS', {})
    opts['charset'] = 'utf8mb4'
    opts.setdefault('ssl', {})['ssl_disabled'] = True
    opts.setdefault('connect_timeout', 5)
    opts.setdefault('init_command', "SET SESSION sql_mode=CONCAT(@@sql_mode, ',STRICT_TRANS_TABLES')")


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_USER_MODEL = 'users.Usuario'
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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security Settings for Production
if not DEBUG and not TESTING:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=clean_env_bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=clean_env_bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=clean_env_bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=clean_env_bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=clean_env_bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging — siempre a stdout para que Dokploy/Docker capture los errores
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Google Apps Script API URLs para los costos del Dashboard (Hoja 1 RUL_long y Hoja 2 Database RRHH_2026)
GOOGLE_APPS_SCRIPT_COSTOS_URL = config('GOOGLE_APPS_SCRIPT_COSTOS_URL', default='https://script.google.com/macros/s/AKfycbwGeKMUcjaWUbFBxzxoXYDfSxnmVpmsbt-gYsxOY3pXiAGwIPl3KgcrduDbkC2HA-cl/exec')
GOOGLE_APPS_SCRIPT_COSTOS_URL_2 = config('GOOGLE_APPS_SCRIPT_COSTOS_URL_2', default='https://script.google.com/macros/s/AKfycbwCS0hm5FK-19Gm-RlzFEU17spWJ2IT4-AuJcguzjxQt9TxhLb2_nV8NQICzgzNZ-eq/exec')

# Modo mantenimiento programado (10:00 hs a 12:00 hs - Trabajos en bases de datos)
MAINTENANCE_MODE = False if TESTING else config('MAINTENANCE_MODE', default=False, cast=bool)





