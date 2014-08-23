"""
Django settings for project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'unsafe-value'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'ws4redis',
    'smoke',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "ws4redis.context_processors.default",
)

ROOT_URLCONF = 'smoke.urls'

WSGI_APPLICATION = 'smoke.wsgi.application'
WSGI_APPLICATION = 'ws4redis.django_runserver.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root')


#==============================================================================
# Django
#==============================================================================

STATIC_ROOT = os.path.join(BASE_DIR, 'smoke', 'dev', 'static_root')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)-15s [%(levelname)7s] '
                '%(name)20s - %(message)s')
        },
    },
    'filters': {
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'south': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'requests': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
}


#==============================================================================
# Web Sockets
#==============================================================================

WEBSOCKET_URL = '/ws/'

WS4REDIS_CONNECTION = {
    'host': '127.0.0.1',
    'db': 4,
}

# avoid name clashes
WS4REDIS_PREFIX = 'dhc'

WSGI_APPLICATION = 'ws4redis.django_runserver.application'

WS4REDIS_EXPIRE = None


#==============================================================================
# Celery
#==============================================================================

BROKER_URL = 'redis://127.0.0.1/4'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


#==============================================================================
# Set required settings
#==============================================================================

SSH_BASE_ARGS = None

REDIS_PUBLISHER_FACILITY_LABEL = 'liveLogsAndEvents'

REMOTE_SPARK_SHELL_PATH = "$SPARK_PREFIX/bin/spark-shell"
"""Path (may use environment variables) of the `spark-shell`
script on the remote srever
"""

REMOTE_SPARK_SHELL_PATH_OPTS = ""
"""Options for the spark-shell command executed on the server"""

#==============================================================================
# Import de `smoke_settings_local`
#==============================================================================

try:
    from smoke_settings_local import *
except ImportError as e:
    print "# "
    print "# ERROR"
    print "# "
    print "#   Couldn't import module"
    print "#       `smoke_settings_local`"
    print "# "
    raise Exception("Couldn't import module smoke_settings_local")

assert SSH_BASE_ARGS is not None, \
    "SSH_BASE_ARGS must be defined, check your 'smoke_settings_local.py' file"
