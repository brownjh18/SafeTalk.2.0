from django.urls import path
from . import views

urlpatterns = [
    # Main analytics dashboard
    path('', views.analytics_dashboard, name='analytics_dashboard'),

    # Specific analytics views
    path('users/', views.user_analytics, name='user_analytics'),
    path('mood/', views.mood_analytics, name='mood_analytics'),
    path('counselors/', views.counselor_analytics, name='counselor_analytics'),
    path('chat/', views.chat_analytics, name='chat_analytics'),
    path('appointments/', views.appointment_analytics, name='appointment_analytics'),
    path('video-calls/', views.video_call_analytics, name='video_call_analytics'),

    # Data export
    path('export/', views.export_analytics, name='export_analytics'),

    # AJAX endpoints for real-time data
    path('api/realtime/', views.get_realtime_metrics, name='realtime_metrics'),
    path('api/chart-data/', views.get_analytics_chart_data, name='chart_data'),
]