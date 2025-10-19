from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.messages_view, name='messages'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('search-users/', views.search_users, name='search_users'),
    path('create-conversation/', views.create_conversation, name='create_conversation'),
    path('start-chat/<int:user_id>/', views.start_chat_with_user, name='start_chat_with_user'),

    # API endpoints
    path('api/conversations/', views.conversations_api, name='conversations_api'),
    path('conversation/<int:conversation_id>/messages/', views.conversation_messages_api, name='conversation_messages_api'),
    path('conversation/<int:conversation_id>/mark-read/', views.mark_conversation_read, name='mark_conversation_read'),
    path('message/<int:message_id>/mark-read/', views.mark_message_read, name='mark_message_read'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('notification/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/unread/', views.unread_notifications_api, name='unread_notifications_api'),
    path('api/notifications/unread/count/', views.unread_notifications_count_api, name='unread_notifications_count_api'),
    path('presence/update/', views.update_presence, name='update_presence'),
    path('presence/user/<int:user_id>/', views.get_user_presence, name='get_user_presence'),
    path('presence/conversation/<int:conversation_id>/', views.get_conversation_presence, name='get_conversation_presence'),
    path('upload-attachment/', views.upload_attachment, name='upload_attachment'),
    path('attachment/<int:attachment_id>/delete/', views.delete_attachment, name='delete_attachment'),
    path('conversation/<int:conversation_id>/search/', views.search_messages, name='search_messages'),
    path('conversation/<int:conversation_id>/archive/', views.archive_conversation, name='archive_conversation'),
    path('conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('conversation/<int:conversation_id>/mute/', views.mute_conversation, name='mute_conversation'),
    path('conversation/<int:conversation_id>/unmute/', views.unmute_conversation, name='unmute_conversation'),
    path('notifications/', views.notifications_page, name='notifications_page'),
]