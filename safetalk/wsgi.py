"""
WSGI config for safetalk project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

# Determine settings module based on environment
environment = os.getenv('DJANGO_ENV', 'development')

if environment == 'production':
    settings_module = 'safetalk.settings.production'
else:
    settings_module = 'safetalk.settings.development'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
