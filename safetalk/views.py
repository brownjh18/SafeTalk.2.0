"""
General views for SafeTalk application
"""
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def welcome_view(request):
    """Welcome page view"""
    return render(request, 'welcome.html')


def dashboard_view(request):
    """Main dashboard view"""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('login')

    # Get user role and redirect to appropriate dashboard
    if request.user.role == 'admin':
        from accounts.views import admin_dashboard
        return admin_dashboard(request)
    elif request.user.role == 'counselor':
        from accounts.views import counselor_dashboard
        return counselor_dashboard(request)
    else:  # client
        from accounts.views import client_dashboard
        return client_dashboard(request)


@login_required
def dashboard_redirect_view(request):
    """Dashboard redirect view that handles authentication"""
    from django.contrib.auth.decorators import login_required
    from django.utils.decorators import method_decorator

    # This view is decorated with login_required, so unauthenticated users will be redirected to login
    return dashboard_view(request)


@login_required
def sessions_redirect_view(request):
    """Redirect to chat sessions page"""
    from django.shortcuts import redirect
    return redirect('sessions_list')


@login_required
def conversations_view(request):
    """Conversations page view"""
    return render(request, 'conversations.html')


@require_GET
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
    })


@require_GET
@cache_page(300)  # Cache for 5 minutes
def system_status(request):
    """
    System status endpoint with basic metrics
    """
    try:
        from django.db import connection
        from django.core.cache import cache

        # Database health check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"

        # Cache health check
        cache.set('health_check', 'ok', 10)
        cache_status = "healthy" if cache.get('health_check') == 'ok' else "unhealthy"

        return JsonResponse({
            'status': 'healthy',
            'database': db_status,
            'cache': cache_status,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error(f'System status check failed: {str(e)}')
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)


@require_GET
def performance_metrics(request):
    """
    Performance metrics endpoint for monitoring
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        # Get performance data from cache
        metrics = {}
        cache_keys = cache.keys('perf_*')

        for key in cache_keys[:10]:  # Limit to first 10 paths
            path_metrics = cache.get(key, [])
            if path_metrics:
                avg_duration = sum(m['duration'] for m in path_metrics) / len(path_metrics)
                metrics[key.replace('perf_', '')] = {
                    'average_duration_ms': round(avg_duration, 2),
                    'request_count': len(path_metrics),
                    'last_request': path_metrics[-1]['timestamp'].isoformat() if path_metrics else None,
                }

        return JsonResponse({
            'metrics': metrics,
            'timestamp': timezone.now().isoformat(),
        })

    except Exception as e:
        logger.error(f'Performance metrics error: {str(e)}')
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)


@require_GET
def error_logs(request):
    """
    Error logs endpoint for debugging
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        # Read recent error logs
        log_file = settings.BASE_DIR / 'logs' / 'django_error.log'
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()[-50:]  # Last 50 lines
            return JsonResponse({
                'logs': lines,
                'timestamp': timezone.now().isoformat(),
            })
        else:
            return JsonResponse({
                'logs': [],
                'message': 'No error logs found',
                'timestamp': timezone.now().isoformat(),
            })

    except Exception as e:
        logger.error(f'Error logs retrieval failed: {str(e)}')
        return JsonResponse({
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)