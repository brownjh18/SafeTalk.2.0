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


@login_required
def chat_view(request):
    """Chat interface view"""
    return render(request, 'chat.html')


@login_required
def ai_chat_view(request):
    """AI Chat interface view"""
    return render(request, 'chat.html')


@login_required
def user_management_view(request):
    """User management page view with enhanced dashboard-style design"""
    if request.user.role not in ['admin', 'counselor']:
        from django.contrib import messages
        messages.error(request, "You don't have permission to view user management.")
        from django.shortcuts import redirect
        return redirect('profile')

    from django.db.models import Count
    from accounts.models import User

    # Get user statistics for the dashboard cards
    users = User.objects.all().order_by('username')
    total_users = users.count()
    admin_count = users.filter(role='admin').count()
    counselor_count = users.filter(role='counselor').count()
    client_count = users.filter(role='client').count()
    today_users = users.filter(date_joined__date=timezone.now().date()).count()

    context = {
        'users': users,
        'total_users': total_users,
        'admin_count': admin_count,
        'counselor_count': counselor_count,
        'client_count': client_count,
        'today_users': today_users,
        'active_sessions': 0,  # Placeholder for session counting
        'pending_actions': 0,  # Placeholder for pending actions count
    }

    return render(request, 'users.html', context)


@login_required
def all_users_view(request):
    """Comprehensive view of all users with detailed information"""
    if request.user.role not in ['admin', 'counselor']:
        from django.contrib import messages
        messages.error(request, "You don't have permission to view all users.")
        from django.shortcuts import redirect
        return redirect('profile')

    from django.db.models import Count, Q
    from accounts.models import User

    # Get all users with enhanced filtering
    users = User.objects.all().order_by('-date_joined')

    # Apply filters if provided
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter:
        users = users.filter(is_active=(status_filter == 'active'))

    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )

    # Get comprehensive statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    admin_users = User.objects.filter(role='admin').count()
    counselor_users = User.objects.filter(role='counselor').count()
    client_users = User.objects.filter(role='client').count()
    new_users_this_month = User.objects.filter(
        date_joined__year=timezone.now().year,
        date_joined__month=timezone.now().month
    ).count()

    context = {
        'users': users,
        'filtered_users': users,  # For template compatibility
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'admin_users': admin_users,
        'counselor_users': counselor_users,
        'client_users': client_users,
        'new_users_this_month': new_users_this_month,
        'current_filters': {
            'role': role_filter,
            'status': status_filter,
            'search': search_query,
        }
    }

    return render(request, 'all_users.html', context)


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