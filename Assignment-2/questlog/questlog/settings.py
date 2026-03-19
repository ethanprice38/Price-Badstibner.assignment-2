"""
Django settings for the QuestLog project.

This is a standard Django settings file. The most important things to know:
- We use SQLite (the default), so no database setup is needed.
- Static files (CSS, images) are served by Django in development mode.
- Templates are found automatically inside each app's 'templates/' folder.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# For a class project this is fine, but never commit a real secret key to git.
SECRET_KEY = 'django-insecure-questlog-class-project-do-not-use-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# ─────────────────────────────────────────────────────────────────────
# Installed Applications
# ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',       # The /admin interface
    'django.contrib.auth',        # Django's built-in authentication system
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Serves CSS/JS in development

    'campaign_manager',           # Our main app
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

ROOT_URLCONF = 'questlog.urls'


# ─────────────────────────────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        # APP_DIRS=True tells Django to look for a 'templates/' folder
        # inside each installed app. So campaign_manager/templates/ is found
        # automatically — no need to list it explicitly.
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

WSGI_APPLICATION = 'questlog.wsgi.application'


# ─────────────────────────────────────────────────────────────────────
# Database — SQLite (default, no setup needed)
# ─────────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # The database file lives in questlog/
    }
}


# ─────────────────────────────────────────────────────────────────────
# Password validation (Django's built-in validators)
# ─────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────────────────────────────
# Internationalization
# ─────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────────────────────────────────
# Static files (CSS, JavaScript, Images)
# ─────────────────────────────────────────────────────────────────────
# Django automatically finds static files in each app's 'static/' folder.
# In templates, use {% load static %} and {% static 'campaign_manager/style.css' %}
STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────────────────────────────
# Authentication redirects
# ─────────────────────────────────────────────────────────────────────
# After a successful login, redirect to the dashboard (root URL).
LOGIN_REDIRECT_URL = '/'

# After logout, go to the login page.
LOGOUT_REDIRECT_URL = '/accounts/login/'

# If a view requires login and the user isn't logged in, send them here.
LOGIN_URL = '/accounts/login/'
