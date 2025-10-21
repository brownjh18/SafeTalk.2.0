"""
URL configuration for safetalk project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from safetalk import views
from accounts import views as accounts_views

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('', views.welcome_view, name='welcome'),
    path('accounts/', include('accounts.urls')),
    path('resources/', include('resources.urls')),
    path('analytics/', include('analytics.urls')),
    path('messaging/', include('messaging.urls')),
    path('subscriptions/', include('accounts.urls')),  # Subscription routes
    path('dashboard/', views.dashboard_redirect_view, name='dashboard'),  # Main dashboard with auth
    path('dashboard/', include('accounts.urls')),  # Dashboard routes
    path('appointments/', include('accounts.urls')),  # Appointments routes
    path('users/', views.user_management_view, name='user_management'),  # User management page
    path('users/all/', views.all_users_view, name='all_users'),  # Comprehensive user list page
    path('profile/', accounts_views.profile_view, name='profile'),
    path('profile/<int:user_id>/', accounts_views.profile_view, name='user_profile'),
    path('profile/edit/', accounts_views.edit_profile_view, name='edit_profile'),
    path('settings/', accounts_views.account_settings_view, name='settings'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/ai/', views.ai_chat_view, name='ai_chat'),

    # Payment webhooks
    path('stripe/webhook/', accounts_views.stripe_webhook, name='stripe_webhook'),

    # API endpoints
    path('api/health/', views.health_check, name='health_check'),
    path('api/status/', views.system_status, name='system_status'),
    path('api/performance/', views.performance_metrics, name='performance_metrics'),
    path('api/logs/', views.error_logs, name='error_logs'),
    prefix_default_language=False
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
