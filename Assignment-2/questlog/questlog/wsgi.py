"""
WSGI config for questlog project.

It exposes the WSGI callable as a module-level variable named ``application``.
This is the entry point for production web servers (like Gunicorn or uWSGI).
For development, `python manage.py runserver` uses this automatically.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'questlog.settings')
application = get_wsgi_application()
