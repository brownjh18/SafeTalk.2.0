from django.urls import path
from . import views
from safetalk import views as safetalk_views

urlpatterns = [
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    path('register/', views.registration_view, name='register'),
    path('login/', views.login_view, name='login'),
    # Role-based dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/counselor/', views.counselor_dashboard, name='counselor_dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('account-settings/', views.account_settings_view, name='account_settings'),
    path('profile/<int:user_id>/', views.profile_view, name='user_profile'),
    path('profile/<int:user_id>/edit/', views.edit_profile_view, name='edit_user_profile'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('log-mood/', views.log_mood, name='log_mood'),
    path('mood-history/', views.mood_history, name='mood_history'),
    path('logout/', views.logout_view, name='logout'),
    path('add-user/', views.add_user_view, name='add_user'),
    path('manage-users/', views.user_list_view, name='manage_users'),
    path('users/', views.user_list_view, name='user_list'),
    path('counselor-clients/', views.counselor_clients_view, name='counselor_clients'),
    path('content/', views.content_management, name='content_management'),
    path('analytics/', views.user_insights, name='analytics'),
    path('insights/', views.user_insights, name='user_insights'),
    path('export-mood-data/', views.export_mood_data, name='export_mood_data'),
    path('notification-preferences/', views.notification_preferences_api, name='notification_preferences_api'),
    path('subscriptions/', views.admin_plan_management, name='subscriptions'),
    path('subscription-plans/', views.subscription_plans, name='subscription_plans'),
    path('subscribe/<str:plan_name>/', views.subscribe, name='subscribe'),
    path('subscription-status/', views.subscription_status, name='subscription_status'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('renew-subscription/', views.renew_subscription, name='renew_subscription'),
    # Admin subscription management
    path('management/plans/', views.admin_plan_management, name='admin_plan_management'),
    path('management/plans/add/', views.admin_create_plan, name='admin_create_plan'),
    path('management/plans/<int:plan_id>/edit/', views.admin_edit_plan, name='admin_edit_plan'),
    path('management/plans/<int:plan_id>/toggle/', views.admin_toggle_plan_status, name='admin_toggle_plan_status'),
    path('management/subscriptions/', views.admin_subscription_management, name='admin_subscription_management'),
    path('management/subscription/<int:subscription_id>/', views.admin_subscription_detail, name='admin_subscription_detail'),
    path('management/invoices/', views.admin_invoice_management, name='admin_invoice_management'),
    path('management/create-invoice/<int:subscription_id>/', views.admin_create_invoice, name='admin_create_invoice'),
    path('management/send-invoice/<int:invoice_id>/', views.admin_send_invoice, name='admin_send_invoice'),
    path('management/payments/', views.admin_payment_management, name='admin_payment_management'),
    path('management/record-payment/<int:subscription_id>/', views.admin_record_payment, name='admin_record_payment'),
    # Integration URLs
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar-settings/', views.calendar_settings, name='calendar_settings'),
    path('social-settings/', views.social_settings, name='social_settings'),
    path('manage-appointments/', views.appointments_list, name='manage_appointments'),
    path('appointments/', views.appointments_list, name='appointments_list'),
    path('appointments/history/', views.appointments_history, name='appointments_history'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/edit/', views.edit_appointment, name='edit_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/export/', views.export_appointments, name='export_appointments'),
    path('social-posts/', views.social_posts, name='social_posts'),
    path('mood-shares/', views.mood_shares_history, name='mood_shares_history'),
    path('settings/', views.edit_profile_view, name='settings'),
    # AJAX URLs
    path('ajax/share-mood/', views.share_mood_data, name='share_mood_data'),
    path('ajax/sync-calendar/', views.sync_calendar, name='sync_calendar'),
    path('ajax/update-appointment-calendar/<int:appointment_id>/', views.update_appointment_calendar, name='update_appointment_calendar'),

    # Video calling URLs
    path('video-calls/', views.video_calls_list, name='video_calls_list'),
    path('video-calls/create/', views.create_video_call, name='create_video_call'),
    path('video-calls/<int:call_id>/', views.video_call_detail, name='video_call_detail'),
    path('video-calls/<int:call_id>/start/', views.start_video_call, name='start_video_call'),
    path('video-calls/<int:call_id>/end/', views.end_video_call, name='end_video_call'),
    path('video-calls/<int:call_id>/join/', views.join_video_call, name='join_video_call'),

    # File sharing URLs
    path('files/', views.file_list, name='file_list'),
    path('files/upload/', views.upload_file, name='upload_file'),
    path('files/<int:file_id>/share/', views.share_file, name='share_file'),
    path('files/shared/<str:share_id>/download/', views.download_shared_file, name='download_shared_file'),
    path('files/<int:file_id>/delete/', views.delete_file, name='delete_file'),

    # Push notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/test/', views.send_test_notification, name='send_test_notification'),

    # Offline functionality URLs
    path('api/sync-offline-data/', views.sync_offline_data, name='sync_offline_data'),
    path('api/get-offline-data/', views.get_offline_data, name='get_offline_data'),
    path('api/mark-data-synced/', views.mark_data_synced, name='mark_data_synced'),

    # API integration URLs
    path('api/keys/', views.api_keys_list, name='api_keys_list'),
    path('api/keys/create/', views.create_api_key, name='create_api_key'),
    path('api/keys/<str:key_id>/delete/', views.delete_api_key, name='delete_api_key'),
    path('api/webhooks/', views.webhooks_list, name='webhooks_list'),
    path('api/webhooks/create/', views.create_webhook, name='create_webhook'),
    path('api/webhooks/<int:webhook_id>/delete/', views.delete_webhook, name='delete_webhook'),

    # Third-party API endpoints
    path('api/v1/auth/', views.api_authenticate, name='api_auth'),
    path('api/v1/mood-entries/', views.api_mood_entries, name='api_mood_entries'),
    path('api/v1/mood-entries/create/', views.api_create_mood_entry, name='api_create_mood_entry'),
    path('api/v1/appointments/', views.api_appointments, name='api_appointments'),
    path('api/v1/send-notification/', views.api_send_notification, name='api_send_notification'),
]