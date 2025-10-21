"""
ASGI config for safetalk project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

# Determine settings module based on environment
environment = os.getenv('DJANGO_ENV', 'development')

if environment == 'production':
    settings_module = 'safetalk.settings.production'
else:
    settings_module = 'safetalk.settings.development'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

from django.core.asgi import get_asgi_application

# Temporarily using standard Django ASGI application
# WebSocket support can be added later with proper chat.routing implementation
application = get_asgi_application()
