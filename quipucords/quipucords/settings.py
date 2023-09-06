"""
Django settings for quipucords project.

Generated by 'django-admin startproject' using Django 1.11.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import logging
import os
import random
import string
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

from .featureflag import FeatureFlag

logger = logging.getLogger(__name__)

env = environ.Env()

# BASE_DIR is ./quipucords/quipucords
BASE_DIR = Path(__file__).absolute().parent.parent
# DEFAULT_DATA_DIR is ./var, which is on .gitignore
DEFAULT_DATA_DIR = BASE_DIR.parent / "var"

PRODUCTION = env.bool("PRODUCTION", False)

# This suppresses warnings for models where an explicit primary key is not defined.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


def create_random_key():
    """Create a randomized string."""
    return "".join(
        [
            random.SystemRandom().choice(
                string.ascii_letters + string.digits + string.punctuation
            )
            for _ in range(50)
        ]
    )


def app_secret_key_and_path():
    """Return the SECRET_KEY and related DJANGO_SECRET_PATH to use."""
    # We need to support DJANGO_SECRET_KEY from the Environment.
    # This is necessary when the application keys are coming from
    # OpenShift project secrets through the environment.
    #
    # We also update the DJANGO_SECRET_PATH file accordingly
    # as it is also used as the Ansible password vault.
    django_secret_path = Path(
        env.str("DJANGO_SECRET_PATH", str(DEFAULT_DATA_DIR / "secret.txt"))
    )

    django_secret_key = env("DJANGO_SECRET_KEY", default=None)

    if django_secret_key:
        django_secret_path.write_text(django_secret_key, encoding="utf-8")
    elif not django_secret_path.exists():
        django_secret_key = create_random_key()
        django_secret_path.write_text(django_secret_key, encoding="utf-8")
    else:
        django_secret_key = django_secret_path.read_text(encoding="utf-8").strip()
    return django_secret_key, django_secret_path


QPC_SSH_CONNECT_TIMEOUT = env.int("QPC_SSH_CONNECT_TIMEOUT", 60)
QPC_SSH_INSPECT_TIMEOUT = env.int("QPC_SSH_INSPECT_TIMEOUT", 120)

NETWORK_INSPECT_JOB_TIMEOUT = env.int("NETWORK_INSPECT_JOB_TIMEOUT", 10800)  # 3 hours
NETWORK_CONNECT_JOB_TIMEOUT = env.int("NETWORK_CONNECT_JOB_TIMEOUT", 600)  # 10 minutes

QPC_CONNECT_TASK_TIMEOUT = env.int("QPC_CONNECT_TASK_TIMEOUT", 30)
QPC_INSPECT_TASK_TIMEOUT = env.int("QPC_INSPECT_TASK_TIMEOUT", 600)

QPC_HTTP_RETRY_MAX_NUMBER = env.int("QPC_HTTP_RETRY_MAX_NUMBER", 5)
QPC_HTTP_RETRY_BACKOFF = env.float("QPC_HTTP_RETRY_BACKOFF", 0.1)

ANSIBLE_LOG_LEVEL = env.int("ANSIBLE_LOG_LEVEL", 3)

if PRODUCTION:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SECRET_KEY, DJANGO_SECRET_PATH = app_secret_key_and_path()

# SECURITY WARNING: Running with DEBUG=True is a *BAD IDEA*, but this is unfortunately
# necessary because in some cases we still need to serve static files through Django.
# Please consider this note from the official Django docs:
# > This view will only work if DEBUG is True.
# > That’s because this view is grossly inefficient and probably insecure. This is only
# > intended for local development, and should never be used in production.
# TODO FIXME Remove this dangerous default.
DEBUG = env.bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOST_LIST", default=["*"])

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "api",
]

if env.bool("QPC_ENABLE_DJANGO_EXTENSIONS", False):
    INSTALLED_APPS.append("django_extensions")

if not PRODUCTION:
    INSTALLED_APPS.append("coverage")


MIDDLEWARE = [
    "api.common.middleware.ServerVersionMiddle",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "quipucords.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path(__file__).parent / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGIN_REDIRECT_URL = "/client/"

WSGI_APPLICATION = "quipucords.wsgi.application"

DEFAULT_PAGINATION_CLASS = "api.common.pagination.StandardResultsSetPagination"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": DEFAULT_PAGINATION_CLASS,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.user.authentication.QuipucordsExpiringTokenAuthentication",
    ),
}

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# Database Management System could be 'sqlite' or 'postgresql'
QPC_DBMS = env.str("QPC_DBMS", "postgres").lower()
allowed_db_engines = ["sqlite", "postgres"]
if QPC_DBMS not in allowed_db_engines:
    raise ImproperlyConfigured(f"QPC_DBMS must be one of {allowed_db_engines}")

if QPC_DBMS == "sqlite":
    # If user enters an invalid QPC_DBMS, use default postgresql
    DEV_DB = DEFAULT_DATA_DIR / "db.sqlite3"
    PROD_DB = Path(env.str("DJANGO_DB_PATH", str(DEFAULT_DATA_DIR))) / "db.sqlite3"
    DB_PATH = PROD_DB if PRODUCTION else DEV_DB
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DB_PATH,
            "TEST": {"NAME": ":memory:"},
        }
    }
elif QPC_DBMS == "postgres":
    # The following variables are only relevant when using a postgres database:
    QPC_DBMS_DATABASE = env.str("QPC_DBMS_DATABASE", "qpc")
    QPC_DBMS_USER = env.str("QPC_DBMS_USER", "qpc")
    QPC_DBMS_PASSWORD = env.str("QPC_DBMS_PASSWORD", "qpc")
    QPC_DBMS_HOST = env.str("QPC_DBMS_HOST", "localhost")
    QPC_DBMS_PORT = env.int("QPC_DBMS_PORT", 5432)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": QPC_DBMS_DATABASE,
            "USER": QPC_DBMS_USER,
            "PASSWORD": QPC_DBMS_PASSWORD,
            "HOST": QPC_DBMS_HOST,
            "PORT": QPC_DBMS_PORT,
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
NAME = "NAME"
USER_ATTRIBUTE_SIMILARITY_VALIDATOR = (
    "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
)
MINIMUM_LENGTH_VALIDATOR = (
    "django.contrib.auth.password_validation.MinimumLengthValidator"
)
COMMON_PASSWORD_VALIDATOR = (
    "django.contrib.auth.password_validation.CommonPasswordValidator"
)
NUMERIC_PASSWORD_VALIDATOR = (
    "django.contrib.auth.password_validation.NumericPasswordValidator"
)
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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATIC_URL = "/client/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "client"),
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }
}

LOGGING_FORMATTER = env.str("DJANGO_LOG_FORMATTER", "simple")
DJANGO_LOGGING_LEVEL = env.str("DJANGO_LOG_LEVEL", "INFO")
CELERY_LOGGING_LEVEL = env.str("CELERY_LOGGING_LEVEL", "INFO")
QUIPUCORDS_LOGGING_LEVEL = env.str("QUIPUCORDS_LOG_LEVEL", "INFO")
LOGGING_HANDLERS = env.list("DJANGO_LOG_HANDLERS", default=["console"])
VERBOSE_FORMATTING = (
    "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
)
LOG_DIRECTORY = Path(env.str("QPC_LOG_DIRECTORY", str(DEFAULT_DATA_DIR / "logs")))
LOGGING_FILE = Path(env.str("DJANGO_LOG_FILE", str(LOG_DIRECTORY / "app.log")))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": VERBOSE_FORMATTING},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": LOGGING_FORMATTER},
        "file": {
            "level": QUIPUCORDS_LOGGING_LEVEL,
            "class": "logging.FileHandler",
            "filename": LOGGING_FILE,
            "formatter": LOGGING_FORMATTER,
        },
    },
    "loggers": {
        "django": {
            "handlers": LOGGING_HANDLERS,
            "level": DJANGO_LOGGING_LEVEL,
        },
        "celery": {
            "handlers": LOGGING_HANDLERS,
            "level": CELERY_LOGGING_LEVEL,
            "propagate": False,
        },
        "api.details_report": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.deployments_report": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.scan": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.scantask": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.scanjob": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.status": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "fingerprinter": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "api.signal.scanjob_signal": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.callback": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.manager": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.job": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.task": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.network": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.vcenter": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "scanner.satellite": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
        "quipucords.environment": {
            "handlers": LOGGING_HANDLERS,
            "level": QUIPUCORDS_LOGGING_LEVEL,
        },
    },
}

# Reverse default behavior to avoid host key checking
os.environ.setdefault("ANSIBLE_HOST_KEY_CHECKING", "False")
# Reverse default behavior for better readability in log files
os.environ.setdefault("ANSIBLE_NOCOLOR", "False")

QPC_EXCLUDE_INTERNAL_FACTS = env.bool("QPC_EXCLUDE_INTERNAL_FACTS", False)
QPC_TOKEN_EXPIRE_HOURS = env.int("QPC_TOKEN_EXPIRE_HOURS", 24)
QPC_INSIGHTS_REPORT_SLICE_SIZE = env.int("QPC_INSIGHTS_REPORT_SLICE_SIZE", 10000)
QPC_INSIGHTS_DATA_COLLECTOR_LABEL = env.str("QPC_INSIGHTS_DATA_COLLECTOR_LABEL", "qpc")

QPC_LOG_ALL_ENV_VARS_AT_STARTUP = env.bool("QPC_LOG_ALL_ENV_VARS_AT_STARTUP", True)

# Redis configuration

REDIS_USERNAME = env.str("REDIS_USERNAME", "")
REDIS_PASSWORD = env.str("REDIS_PASSWORD", "")
REDIS_HOST = env.str("REDIS_HOST", "localhost")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_AUTH = f"{REDIS_USERNAME}:{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
REDIS_URL = f"redis://{REDIS_AUTH}{REDIS_HOST}:{REDIS_PORT}"

# Celery configuration

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", False)

# Load Feature Flags
QPC_FEATURE_FLAGS = FeatureFlag()

# Enable or disable various behaviors
QPC_DISABLE_THREADED_SCAN_MANAGER = env.bool("QPC_DISABLE_THREADED_SCAN_MANAGER", False)
QPC_DISABLE_MULTIPROCESSING_SCAN_JOB_RUNNER = env.bool(
    "QPC_DISABLE_MULTIPROCESSING_SCAN_JOB_RUNNER", False
)
QPC_ENABLE_CELERY_SCAN_MANAGER = env.bool("QPC_ENABLE_CELERY_SCAN_MANAGER", False)

# Old hidden/buried configurations that should be removed or renamed
MAX_TIMEOUT_ORDERLY_SHUTDOWN = env.int("MAX_TIMEOUT_ORDERLY_SHUTDOWN", 30)
QUIPUCORDS_MANAGER_HEARTBEAT = env.int("QUIPUCORDS_MANAGER_HEARTBEAT", 60 * 15)
