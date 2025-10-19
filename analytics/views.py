import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from django.core.cache import cache
from accounts.models import User, MoodEntry, Achievement, Appointment, VideoCall
# from chat.models import Message, Session  # Commented out as chat app doesn't exist
from .models import UserAnalytics, MoodAnalytics
from .services import AnalyticsService, CounselorAnalyticsService


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    # Get dashboard data
    dashboard_data = AnalyticsService.get_dashboard_overview()

    context = {
        'dashboard_data': dashboard_data,
        'user': request.user,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def user_analytics(request):
    """User analytics view"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    # User engagement metrics
    user_stats = User.objects.aggregate(
        total_users=Count('id'),
        active_users=Count('id', filter=Q(last_login__gte=timezone.now() - timedelta(days=30))),
        new_users=Count('id', filter=Q(date_joined__gte=timezone.now() - timedelta(days=30))),
    )

    # Mood tracking analytics
    mood_stats = MoodEntry.objects.aggregate(
        total_entries=Count('id'),
        avg_mood=Avg('mood'),
        entries_last_30=Count('id', filter=Q(date__gte=timezone.now() - timedelta(days=30))),
    )

    # User activity over time
    user_activity = User.objects.annotate(
        mood_count=Count('mood_entries'),
        achievement_count=Count('achievements'),
        appointment_count=Count('appointments'),
    ).values(
        'username', 'mood_count', 'achievement_count', 'appointment_count'
    ).order_by('-mood_count')[:20]

    context = {
        'user_stats': user_stats,
        'mood_stats': mood_stats,
        'user_activity': user_activity,
    }
    return render(request, 'analytics/user_analytics.html', context)


@login_required
def mood_analytics(request):
    """Mood analytics view"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    # Mood distribution
    mood_distribution = MoodEntry.objects.values('mood').annotate(
        count=Count('id')
    ).order_by('mood')

    # Mood trends over time (last 90 days)
    mood_trends = MoodEntry.objects.filter(
        date__gte=timezone.now() - timedelta(days=90)
    ).annotate(
        date_trunc=TruncDate('date')
    ).values('date_trunc').annotate(
        avg_mood=Avg('mood'),
        count=Count('id')
    ).order_by('date_trunc')

    # Mood by day of week
    mood_by_day = MoodEntry.objects.annotate(
        day_of_week=TruncDate('date')
    ).extra(
        select={'day': 'EXTRACT(DOW FROM date)'}
    ).values('day').annotate(
        avg_mood=Avg('mood'),
        count=Count('id')
    ).order_by('day')

    context = {
        'mood_distribution': mood_distribution,
        'mood_trends': mood_trends,
        'mood_by_day': mood_by_day,
    }
    return render(request, 'analytics/mood_analytics.html', context)


@login_required
def counselor_analytics(request):
    """Counselor performance analytics"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    counselor_service = CounselorAnalyticsService()

    # Get all counselors
    counselors = User.objects.filter(role='counselor', is_active=True)

    counselor_stats = []
    for counselor in counselors:
        stats = counselor_service.get_counselor_stats(counselor)
        counselor_stats.append({
            'counselor': counselor,
            'stats': stats,
        })

    context = {
        'counselor_stats': counselor_stats,
    }
    return render(request, 'analytics/counselor_analytics.html', context)


@login_required
def chat_analytics(request):
    """Chat and messaging analytics"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    # Chat session statistics
    chat_stats = Session.objects.aggregate(
        total_sessions=Count('id'),
        total_messages=Count('messages'),
    )

    # Message trends
    message_trends = Message.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).annotate(
        date_trunc=TruncDate('timestamp')
    ).values('date_trunc').annotate(
        count=Count('id')
    ).order_by('date_trunc')

    # Most active chat sessions
    active_sessions = Session.objects.annotate(
        message_count=Count('messages')
    ).values('title', 'message_count').order_by('-message_count')[:10]

    context = {
        'chat_stats': chat_stats,
        'message_trends': message_trends,
        'active_sessions': active_sessions,
    }
    return render(request, 'analytics/chat_analytics.html', context)


@login_required
def appointment_analytics(request):
    """Appointment and session analytics"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    # Appointment statistics
    appointment_stats = Appointment.objects.aggregate(
        total_appointments=Count('id'),
        completed_appointments=Count('id', filter=Q(status='completed')),
        upcoming_appointments=Count('id', filter=Q(
            scheduled_date__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        )),
        cancelled_appointments=Count('id', filter=Q(status='cancelled')),
    )

    # Appointments by type
    appointments_by_type = Appointment.objects.values('appointment_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Appointments over time
    appointment_trends = Appointment.objects.filter(
        scheduled_date__gte=timezone.now() - timedelta(days=90)
    ).annotate(
        month=TruncMonth('scheduled_date')
    ).values('month').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    ).order_by('month')

    context = {
        'appointment_stats': appointment_stats,
        'appointments_by_type': appointments_by_type,
        'appointment_trends': appointment_trends,
    }
    return render(request, 'analytics/appointment_analytics.html', context)


@login_required
def video_call_analytics(request):
    """Video call analytics"""
    if request.user.role not in ['admin', 'counselor']:
        return render(request, 'analytics/access_denied.html')

    # Video call statistics
    video_stats = VideoCall.objects.aggregate(
        total_calls=Count('id'),
        completed_calls=Count('id', filter=Q(status='completed')),
        scheduled_calls=Count('id', filter=Q(status='scheduled')),
        total_duration=Sum('actual_end') - Sum('actual_start'),  # This needs refinement
    )

    # Calls by type
    calls_by_type = VideoCall.objects.values('call_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Calls by provider
    calls_by_provider = VideoCall.objects.values('provider').annotate(
        count=Count('id')
    ).order_by('-count')

    # Average call duration (simplified)
    avg_duration = VideoCall.objects.filter(
        status='completed',
        actual_start__isnull=False,
        actual_end__isnull=False
    ).aggregate(
        avg_duration=Avg('actual_end') - Avg('actual_start')  # This needs better calculation
    )

    context = {
        'video_stats': video_stats,
        'calls_by_type': calls_by_type,
        'calls_by_provider': calls_by_provider,
        'avg_duration': avg_duration,
    }
    return render(request, 'analytics/video_call_analytics.html', context)


@login_required
def export_analytics(request):
    """Export analytics data"""
    if request.user.role not in ['admin', 'counselor']:
        return JsonResponse({'error': 'Access denied'})

    export_type = request.GET.get('type', 'dashboard')
    format_type = request.GET.get('format', 'json')

    if export_type == 'dashboard':
        data = AnalyticsService.get_dashboard_overview()
    elif export_type == 'users':
        data = AnalyticsService.get_user_analytics()
    elif export_type == 'mood':
        data = AnalyticsService.get_mood_analytics()
    else:
        return JsonResponse({'error': 'Invalid export type'})

    if format_type == 'json':
        return JsonResponse(data)
    else:
        # For CSV export, we'd implement CSV generation here
        return JsonResponse({'error': 'CSV export not implemented yet'})


# AJAX endpoints for real-time analytics
@login_required
def get_realtime_metrics(request):
    """Get real-time analytics metrics"""
    if request.user.role not in ['admin', 'counselor']:
        return JsonResponse({'error': 'Access denied'})

    # Cache key for real-time data
    cache_key = 'realtime_analytics'
    cached_data = cache.get(cache_key)

    if cached_data:
        return JsonResponse(cached_data)

    # Calculate real-time metrics
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    realtime_data = {
        'active_users': User.objects.filter(
            last_login__gte=now - timedelta(hours=1)
        ).count(),
        'mood_entries_today': MoodEntry.objects.filter(
            date=today_start.date()
        ).count(),
        'active_chat_rooms': ChatRoom.objects.filter(
            is_active=True,
            updated_at__gte=now - timedelta(minutes=30)
        ).count(),
        'upcoming_appointments': Appointment.objects.filter(
            scheduled_date__gte=now,
            scheduled_date__lte=now + timedelta(hours=24),
            status__in=['scheduled', 'confirmed']
        ).count(),
        'active_video_calls': VideoCall.objects.filter(
            status='active'
        ).count(),
    }

    # Cache for 5 minutes
    cache.set(cache_key, realtime_data, 300)

    return JsonResponse(realtime_data)


@login_required
def get_analytics_chart_data(request):
    """Get chart data for analytics dashboard"""
    if request.user.role not in ['admin', 'counselor']:
        return JsonResponse({'error': 'Access denied'})

    chart_type = request.GET.get('type', 'mood_trends')
    days = int(request.GET.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)

    if chart_type == 'mood_trends':
        data = MoodEntry.objects.filter(
            date__gte=start_date
        ).annotate(
            date_str=TruncDate('date')
        ).values('date_str').annotate(
            avg_mood=Avg('mood'),
            count=Count('id')
        ).order_by('date_str')

        chart_data = {
            'labels': [item['date_str'].strftime('%Y-%m-%d') for item in data],
            'datasets': [{
                'label': 'Average Mood',
                'data': [float(item['avg_mood']) if item['avg_mood'] else 0 for item in data],
                'borderColor': 'rgb(75, 192, 192)',
                'tension': 0.1
            }, {
                'label': 'Entries Count',
                'data': [item['count'] for item in data],
                'borderColor': 'rgb(255, 99, 132)',
                'tension': 0.1
            }]
        }

    elif chart_type == 'user_growth':
        data = User.objects.filter(
            date_joined__gte=start_date
        ).annotate(
            join_date=TruncDate('date_joined')
        ).values('join_date').annotate(
            count=Count('id')
        ).order_by('join_date')

        chart_data = {
            'labels': [item['join_date'].strftime('%Y-%m-%d') for item in data],
            'datasets': [{
                'label': 'New Users',
                'data': [item['count'] for item in data],
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgb(54, 162, 235)',
                'borderWidth': 1
            }]
        }

    else:
        return JsonResponse({'error': 'Invalid chart type'})

    return JsonResponse(chart_data)