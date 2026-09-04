import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "unsafe-development-key",
)

DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() == "true"


# ============================================================
# SECURITY
# ============================================================

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "myproject.apps.MongoAdminConfig",
    "myproject.apps.MongoAuthConfig",
    "myproject.apps.MongoContentTypesConfig",

    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django_mongodb_backend",

    "accounts.apps.AccountsConfig",

    "payables.apps.PayablesConfig",

    "school_config",

    "students",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "myproject.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django.DjangoTemplates"
        ),

        "DIRS": [
            BASE_DIR / "myproject" / "templates",
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                (
                    "django.contrib.messages."
                    "context_processors.messages"
                ),

                # Added from teammate branch.
                (
                    "accounts.context_processors."
                    "unread_notifications"
                ),
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "myproject.wsgi.application"


# ============================================================
# MONGODB ATLAS
# ============================================================

MONGO_URI = os.getenv("MONGO_URI")

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "edufinance",
)

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is missing from the .env file."
    )


DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        "HOST": MONGO_URI,
        "NAME": MONGO_DB_NAME,
    }
}


# ============================================================
# MONGODB OBJECT IDS
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django_mongodb_backend.fields.ObjectIdAutoField"
)


# ============================================================
# MONGODB-COMPATIBLE DJANGO MIGRATIONS
# ============================================================

MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Beirut"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
)


# ============================================================
# AUTHENTICATION BACKENDS
# ============================================================

# Application login authenticates using email.
# ModelBackend remains available for Django admin and
# standard Django authentication behavior.
AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]


# ============================================================
# AUTHENTICATION ROUTES
# ============================================================

LOGIN_URL = "login"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/login/"