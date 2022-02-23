"""
Django settings for acceptor project.

Generated by 'django-admin startproject' using Django 4.0.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load dotenv
dotenv.load_dotenv(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'django_q',

    'submissions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'acceptor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'acceptor.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Task queue
# used for running scheduled tasks

Q_CLUSTER = {
    "name": "default",
    "orm": "default",
    "label": "Úlohy ve frontě",
    "timeout": 60,
    "max_attempts": 2,
}


# Authentication

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'APP': {
            'client_id': '824128145343-nlm3r9b8ivh12mkmol2s2esd2gl1v9lp.apps.googleusercontent.com',
            'secret': os.environ["GOOGLE_AUTH_SECRET"],
            'key': '',
        }
    }
}

SOCIALACCOUNT_ADAPTER = "acceptor.accounts.SubmissionAccountAdapter"


LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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

if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []


# Emails

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.environ["EMAIL_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_PASS"]
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "Odevzdávací systém maturitních prací <acceptor@gjk.cz>"


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'cs-cz'

TIME_ZONE = 'Europe/Prague'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "static/"

# Media files

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Application related config

EMAIL_SUBJECT_PREFIX = "[Odevzdávací systém] "
EMAIL_DOMAIN = "gjk.cz"
IS_STUDENT_USERNAME = lambda username: username.startswith("x") and username[-1].isdigit()
USE_UNACCENT = False

CONSULTATION_EMAIL_DAYS_LEFT = 7
CONSULTATION_EMAIL_SUBJECT = f"{EMAIL_SUBJECT_PREFIX}Povinné konzultace"
CONSULTATION_EMAIL_TEMPLATE = "\
Zbývá Vám pouze {remaining_days} dní na splnění \
povinných konzultací v tomto období. \
Máte splněno {have} konzultací z požadovaných {required}."

ADMINS = [("Lukáš Veškrna", "lukas.veskrna@gmail.com")]
