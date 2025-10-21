"""
Development settings for SafeTalk project.

This file contains settings specific to the development environment.
"""

from .base import *

# Development-specific settings
DEBUG = True

# Allow localhost and testserver for development
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver', '0.0.0.0']

# Development database (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Connection timeout in seconds
            'check_same_thread': False,  # Allow connections from multiple threads
        },
        'CONN_MAX_AGE': 60,  # Keep connections open for 60 seconds
        'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
    }
}

# Development caching (in-memory)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # 5 minutes default timeout
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Maximum number of entries in cache
            'CULL_FREQUENCY': 3,  # 1/3 of entries removed when max reached
        }
    },
    'query_results': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 600,  # 10 minutes for query results
        'OPTIONS': {
            'MAX_ENTRIES': 500,
            'CULL_FREQUENCY': 2,
        }
    }
}

# Development logging (more verbose)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',  # Less verbose for development
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',  # More verbose console logging
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'chat': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Development email backend (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development site URL
SITE_URL = 'http://localhost:8000'

# Development Google Calendar redirect URI
GOOGLE_CALENDAR_REDIRECT_URI = 'http://localhost:8000/accounts/google/login/callback/'

# Disable some security features for development
SECURITY_HEADERS = {
    'CSP_ENABLED': False,  # Disable CSP for development
    'HSTS_ENABLED': False,  # Disable HSTS for development
    'X_FRAME_OPTIONS': 'SAMEORIGIN',  # Allow same origin frames
    'X_CONTENT_TYPE_OPTIONS': 'nosniff',
    'X_XSS_PROTECTION': '1; mode=block',
    'REFERRER_POLICY': 'strict-origin-when-cross-origin',
}

# Development channel layers (in-memory)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Development Celery settings (if needed)
# CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously for development