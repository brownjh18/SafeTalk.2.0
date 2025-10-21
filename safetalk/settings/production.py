"""
Production settings for SafeTalk project.

This file contains settings specific to the production environment.
"""

import os
from .base import *

# Production-specific settings
DEBUG = False

# Production allowed hosts (will be overridden by environment variable)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else ['localhost', '127.0.0.1']

# Production database (PostgreSQL required)
import dj_database_url

if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
else:
    # Fallback for when DATABASE_URL is not set (like in local development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'safetalk'),
            'USER': os.getenv('DB_USER', 'safetalk_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'safetalk_pass'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True,
        }
    }

# Production caching (Redis if available, otherwise fallback to local memory)
if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        },
        'query_results': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Fallback to local memory cache when Redis is not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        },
        'query_results': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'TIMEOUT': 600,
            'OPTIONS': {
                'MAX_ENTRIES': 500,
                'CULL_FREQUENCY': 2,
            }
        }
    }

# Production logging (less verbose, more secure)
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
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_error.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',  # Less console output in production
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'chat': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Production email backend (Celery)
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'

# Production site URL (required)
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# Production Google Calendar redirect URI
GOOGLE_CALENDAR_REDIRECT_URI = os.getenv('GOOGLE_CALENDAR_REDIRECT_URI', f"{SITE_URL}/accounts/google/login/callback/")

# Production security headers (disabled for development compatibility)
SECURITY_HEADERS = {
    'CSP_ENABLED': False,
    'HSTS_ENABLED': False,
    'X_FRAME_OPTIONS': 'SAMEORIGIN',
    'X_CONTENT_TYPE_OPTIONS': 'nosniff',
    'X_XSS_PROTECTION': '1; mode=block',
    'REFERRER_POLICY': 'strict-origin-when-cross-origin',
}

# Production channel layers (Redis if available, otherwise in-memory)
if os.getenv('REDIS_URL'):
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')],
            },
        },
    }
else:
    # Fallback to in-memory channel layer when Redis is not available
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Production Celery settings (Redis if available, otherwise disabled)
if os.getenv('REDIS_URL'):
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
else:
    # Disable Celery when Redis is not available
    CELERY_BROKER_URL = None
    CELERY_RESULT_BACKEND = None
    CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously

# Production session settings (less strict for development)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Production CSRF settings (less strict for development)
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Production SSL/HTTPS settings (disabled for development)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'