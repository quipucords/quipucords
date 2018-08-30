#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""
Django settings for quipucords project.

Generated by 'django-admin startproject' using Django 1.11.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import datetime
import os
import django.db

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

PRODUCTION = bool(os.environ.get('PRODUCTION', False))

if PRODUCTION:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    DJANGO_SECRET_PATH = os.environ.get('DJANGO_SECRET_PATH',
                                        os.path.join(BASE_DIR, 'secret.txt'))
    if not os.path.exists(DJANGO_SECRET_PATH):
        import random
        import string
        SECRET_KEY = ''.join([random.SystemRandom().choice(
            '{}{}{}'.format(string.ascii_letters,
                            string.digits,
                            string.punctuation)) for i in range(50)])
        with open(DJANGO_SECRET_PATH, 'w') as secret_file:
            secret_file.write(SECRET_KEY)
    else:
        with open(DJANGO_SECRET_PATH, 'r') as secret_file:
            SECRET_KEY = secret_file.read().splitlines()[0]
else:
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = '79vtvq2r0m20a4$%#iyzabn#*(7&!&%60aoga@m4(in3-*ys8)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get('DJANGO_DEBUG', True))
if isinstance(DEBUG, str):
    DEBUG = DEBUG.lower() == 'true'

ALLOWED_HOST_LIST = os.environ.get('DJANGO_ALLOWED_HOST_LIST', '*').split(',')
ALLOWED_HOSTS = ALLOWED_HOST_LIST

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_expiring_authtoken',
    'filters',
    'django_filters',
    'drf_generators',
    'api',
]

if not PRODUCTION:
    INSTALLED_APPS.append('coverage')


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'quipucords.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(os.path.dirname(__file__),
                         'templates').replace('\\', '/'),
        ],
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

LOGIN_REDIRECT_URL = '/client/'

WSGI_APPLICATION = 'quipucords.wsgi.application'

DEFAULT_PAGINATION_CLASS = 'api.common.pagination.StandardResultsSetPagination'

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS':
        ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PAGINATION_CLASS': DEFAULT_PAGINATION_CLASS
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# Database Management System could be 'sqlite3' or 'postgresql'
QPC_DBMS = os.getenv('QPC_DBMS', 'sqlite3').lower()

if QPC_DBMS == 'postgresql':
    # The following variables are only relevant when using a postgres database:
    PGDATABASE = os.getenv('PGDATABASE', 'postgres')
    PGUSER = os.getenv('PGUSER', 'postgres')
    PGPASSWORD = os.getenv('PGPASSWORD', 'postgres')
    PGHOST = os.getenv('PGHOST', 'localhost' or '::')  # :: means localhost but allows IPv4
    PGPORT = os.getenv('PGPORT', 5432)    # and IPv6 connections
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': PGDATABASE,
            'USER': PGUSER,
            'PASSWORD': PGPASSWORD,
            'HOST': PGHOST,
            'PORT': PGPORT,
        }
    }
else:
    QPC_DBMS = 'sqlite3' # If user enters an invalid QPC_DBMS, just use default sqlite3
    DEV_DB = os.path.join(BASE_DIR, 'db.sqlite3')
    PROD_DB = os.path.join(os.environ.get('DJANGO_DB_PATH', BASE_DIR),
                           'db.sqlite3')
    DB_PATH = PROD_DB if PRODUCTION else DEV_DB
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DB_PATH,
        }
    }


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
NAME = 'NAME'
USER_ATTRIBUTE_SIMILARITY_VALIDATOR = \
    'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
MINIMUM_LENGTH_VALIDATOR = \
    'django.contrib.auth.password_validation.MinimumLengthValidator'
COMMON_PASSWORD_VALIDATOR = \
    'django.contrib.auth.password_validation.CommonPasswordValidator'
NUMERIC_PASSWORD_VALIDATOR = \
    'django.contrib.auth.password_validation.NumericPasswordValidator'
AUTH_PASSWORD_VALIDATORS = [
    {
        NAME: USER_ATTRIBUTE_SIMILARITY_VALIDATOR,
    },
    {
        NAME: MINIMUM_LENGTH_VALIDATOR,
    },
    {
        NAME: COMMON_PASSWORD_VALIDATOR,
    },
    {
        NAME: NUMERIC_PASSWORD_VALIDATOR,
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATIC_URL = '/client/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'client'),
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGGING_FORMATTER = os.getenv('DJANGO_LOG_FORMATTER', 'simple')
DJANGO_LOGGING_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')
QUIPUCORDS_LOGGING_LEVEL = os.getenv('QUIPUCORDS_LOG_LEVEL', 'INFO')
LOGGING_HANDLERS = os.getenv('DJANGO_LOG_HANDLERS', 'console').split(',')
VERBOSE_FORMATTING = '%(levelname)s %(asctime)s %(module)s ' \
    '%(process)d %(thread)d %(message)s'

LOG_DIRECTORY = os.getenv('LOG_DIRECTORY', BASE_DIR)
DEFAULT_LOG_FILE = os.path.join(LOG_DIRECTORY, 'app.log')
LOGGING_FILE = os.getenv('DJANGO_LOG_FILE', DEFAULT_LOG_FILE)

DEFAULT_SCAN_DATA_LOG_FILE = os.path.join(LOG_DIRECTORY, 'scan_data.log')
SCAN_DATA_LOG_FILE = os.getenv('SCAN_DATA_LOG_FILE',
                               DEFAULT_SCAN_DATA_LOG_FILE)
SCAN_DATA_LOG_MAX_BYTES = os.getenv('SCAN_DATA_LOG_MAX_BYTES',
                                    1 << 30)  # default 1 GB
DISABLE_SCAN_DATA_LOG = os.getenv('DISABLE_SCAN_DATA_LOG', True)
if isinstance(DISABLE_SCAN_DATA_LOG, str):
    DISABLE_SCAN_DATA_LOG = DISABLE_SCAN_DATA_LOG.lower() == 'true'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': VERBOSE_FORMATTING
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': LOGGING_FORMATTER
        },
        'file': {
            'level': QUIPUCORDS_LOGGING_LEVEL,
            'class': 'logging.FileHandler',
            'filename': LOGGING_FILE,
            'formatter': LOGGING_FORMATTER
        },
    },
    'loggers': {
        'django': {
            'handlers': LOGGING_HANDLERS,
            'level': DJANGO_LOGGING_LEVEL,
        },
        'api.fact': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'api.scan': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'api.scantasks': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'api.scanjob': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'api.status': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'fingerprinter': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'api.signals.scanjob_signal': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.callback': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.manager': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.job': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.task': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.network': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.vcenter': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'scanner.satellite': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
        'quipucords.environment': {
            'handlers': LOGGING_HANDLERS,
            'level': QUIPUCORDS_LOGGING_LEVEL,
        },
    },
}

# Reverse default behavior to avoid host key checking
os.environ.setdefault('ANSIBLE_HOST_KEY_CHECKING', 'False')


# Token lifespan
EXPIRING_TOKEN_LIFESPAN = datetime.timedelta(days=1)

QPC_EXCLUDE_INTERNAL_FACTS = os.getenv('QPC_EXCLUDE_INTERNAL_FACTS', True)
if isinstance(QPC_EXCLUDE_INTERNAL_FACTS, str):
    QPC_EXCLUDE_INTERNAL_FACTS = QPC_EXCLUDE_INTERNAL_FACTS.lower() == 'true'
