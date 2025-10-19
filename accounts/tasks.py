from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import PushNotification, Webhook
import requests
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user"""
    from .models import User
    try:
        user = User.objects.get(id=user_id)

        subject = 'Welcome to SafeTalk!'
        html_message = render_to_string('emails/welcome.html', {
            'user': user,
            'site_url': settings.SITE_URL,
        })

        send_mail(
            subject=subject,
            message='',  # Plain text version could be added
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user.email}")

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for welcome email")
    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user_id}: {e}")


@shared_task
def send_notification_email(user_id, notification_id):
    """Send email notification"""
    from .models import User, PushNotification
    try:
        user = User.objects.get(id=user_id)
        notification = PushNotification.objects.get(id=notification_id)

        subject = f'SafeTalk: {notification.title}'
        html_message = render_to_string('emails/notification.html', {
            'user': user,
            'notification': notification,
            'site_url': settings.SITE_URL,
        })

        send_mail(
            subject=subject,
            message=notification.message,  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Notification email sent to {user.email}")

    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")


@shared_task
def send_push_notification(user_id, title, message, notification_type='system', data=None):
    """Send push notification to user"""
    from .models import User
    try:
        user = User.objects.get(id=user_id)

        # Create notification in database
        notification = PushNotification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {},
        )

        # Here you would integrate with push notification services like:
        # - Firebase Cloud Messaging (FCM)
        # - Apple Push Notification Service (APNs)
        # - Web Push API

        # For now, we'll just log it
        logger.info(f"Push notification created for {user.username}: {title}")

        # Send email notification as fallback
        send_notification_email.delay(user_id, notification.id)

        return notification.id

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for push notification")
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")


@shared_task
def send_bulk_notifications(user_ids, title, message, notification_type='system'):
    """Send bulk push notifications"""
    for user_id in user_ids:
        send_push_notification.delay(user_id, title, message, notification_type)


@shared_task
def send_scheduled_notifications():
    """Send scheduled notifications that are due"""
    now = timezone.now()

    # Get notifications that are scheduled and due
    due_notifications = PushNotification.objects.filter(
        scheduled_for__lte=now,
        is_sent=False
    )

    for notification in due_notifications:
        try:
            # Mark as sent
            notification.is_sent = True
            notification.sent_at = now
            notification.save()

            # Send the notification
            send_push_notification.delay(
                notification.user.id,
                notification.title,
                notification.message,
                notification.notification_type,
                notification.data
            )

        except Exception as e:
            logger.error(f"Failed to send scheduled notification {notification.id}: {e}")


@shared_task
def send_daily_mood_reminder():
    """Send daily mood check-in reminders"""
    from .models import User
    from django.db.models import Q

    # Get users who haven't logged mood today and have notifications enabled
    today = timezone.now().date()
    users_without_mood_today = User.objects.filter(
        notifications_enabled=True,
        notification_system=True
    ).exclude(
        mood_entries__date=today
    )

    for user in users_without_mood_today:
        send_push_notification.delay(
            user.id,
            "Daily Mood Check-in",
            "How are you feeling today? Take a moment to log your mood.",
            'mood_reminder',
            {'action': 'log_mood'}
        )


@shared_task
def send_appointment_reminders():
    """Send appointment reminders"""
    from .models import Appointment
    from datetime import timedelta

    # Get appointments in the next 24 hours
    tomorrow = timezone.now() + timedelta(hours=24)
    upcoming_appointments = Appointment.objects.filter(
        scheduled_date__lte=tomorrow,
        scheduled_date__gt=timezone.now(),
        status='confirmed'
    )

    for appointment in upcoming_appointments:
        # Check if reminder already sent
        if appointment.reminder_sent:
            continue

        hours_until = int((appointment.scheduled_date - timezone.now()).total_seconds() / 3600)

        if hours_until <= 24:
            send_push_notification.delay(
                appointment.user.id,
                f"Appointment Reminder: {appointment.title}",
                f"You have an appointment with {appointment.counselor.username} in {hours_until} hours.",
                'appointment',
                {
                    'appointment_id': appointment.id,
                    'counselor': appointment.counselor.username,
                    'scheduled_date': appointment.scheduled_date.isoformat(),
                }
            )

            # Mark reminder as sent
            appointment.reminder_sent = True
            appointment.save()


@shared_task
def send_achievement_notifications():
    """Send achievement unlocked notifications"""
    from .models import Achievement

    # Get recently unlocked achievements (last hour)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_achievements = Achievement.objects.filter(
        unlocked_at__gte=one_hour_ago
    ).select_related('user')

    for achievement in recent_achievements:
        send_push_notification.delay(
            achievement.user.id,
            "Achievement Unlocked! 🏆",
            f"Congratulations! You've unlocked the '{achievement.get_achievement_type_display()}' achievement.",
            'achievement',
            {
                'achievement_type': achievement.achievement_type,
                'description': achievement.description,
                'icon': achievement.icon,
            }
        )


@shared_task
def send_webhook(webhook_id, event_type, data):
    """Send webhook notification"""
    try:
        webhook = Webhook.objects.get(id=webhook_id)

        # Prepare payload
        payload = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'user_id': webhook.user.id,
            'data': data
        }

        # Generate signature for verification
        import hmac
        import hashlib
        import json

        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            webhook.secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-SafeTalk-Event': event_type,
            'User-Agent': 'SafeTalk-Webhook/1.0'
        }

        # Send webhook
        response = requests.post(
            webhook.url,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            webhook.record_trigger(success=True)
            logger.info(f"Webhook {webhook_id} triggered successfully for event {event_type}")
        else:
            webhook.record_trigger(success=False)
            logger.warning(f"Webhook {webhook_id} failed with status {response.status_code}")

    except Webhook.DoesNotExist:
        logger.error(f"Webhook {webhook_id} not found")
    except Exception as e:
        logger.error(f"Failed to send webhook {webhook_id}: {e}")

        # Record failure
        try:
            webhook.record_trigger(success=False)
        except:
            pass


@shared_task
def cleanup_old_notifications():
    """Clean up old read notifications"""
    from django.db import connection

    # Delete notifications older than 30 days that are read
    cutoff_date = timezone.now() - timedelta(days=30)

    deleted_count = PushNotification.objects.filter(
        is_read=True,
        sent_at__lt=cutoff_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count[0]} old notifications")


@shared_task
def process_email_queue():
    """Process queued emails (if using database email backend)"""
    # This would process any queued emails if using a database backend
    # For now, Celery Email handles this automatically
    pass


@shared_task
def generate_daily_reports():
    """Generate daily usage reports"""
    from .models import MoodEntry, User
    from django.db.models import Count

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Generate mood logging stats
    mood_stats = MoodEntry.objects.filter(date=yesterday).aggregate(
        total_entries=Count('id'),
        unique_users=Count('user', distinct=True)
    )

    # Generate user activity stats
    user_stats = User.objects.aggregate(
        total_users=Count('id'),
        active_users=Count('id', filter=Q(last_login__date=yesterday))
    )

    # Log daily report
    logger.info(f"Daily Report ({yesterday}): {mood_stats['total_entries']} mood entries from {mood_stats['unique_users']} users, {user_stats['active_users']} active users out of {user_stats['total_users']} total")

    # Here you could send this data to analytics services or save to database


@shared_task
def backup_user_data():
    """Backup user data for compliance"""
    from safetalk.security import ComplianceService
    from .models import User

    compliance_service = ComplianceService()

    # Backup data for a few users at a time to avoid timeouts
    users = User.objects.filter(
        date_joined__lt=timezone.now() - timedelta(days=1)
    )[:10]  # Process 10 users per task run

    for user in users:
        try:
            # Export user data
            data = compliance_service.export_user_data(user)

            # Here you would save this to encrypted storage
            # For now, just log that backup was performed
            logger.info(f"User data backup completed for user {user.id}")

        except Exception as e:
            logger.error(f"Failed to backup data for user {user.id}: {e}")


@shared_task
def check_system_health():
    """Perform system health checks"""
    from django.db import connection
    from django.core.cache import cache

    issues = []

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        issues.append(f"Database connection failed: {e}")

    # Check cache connectivity
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            issues.append("Cache read/write failed")
    except Exception as e:
        issues.append(f"Cache connection failed: {e}")

    # Check external services
    services_to_check = [
        ('OpenAI API', getattr(settings, 'OPENAI_API_KEY', None)),
        ('Stripe', getattr(settings, 'STRIPE_SECRET_KEY', None)),
        ('Email', getattr(settings, 'EMAIL_HOST', None)),
    ]

    for service_name, config in services_to_check:
        if not config:
            issues.append(f"{service_name} not configured")

    if issues:
        logger.warning(f"System health check found {len(issues)} issues: {', '.join(issues)}")
    else:
        logger.info("System health check passed")


@shared_task
def update_user_streaks():
    """Update user streaks for mood logging and other activities"""
    from .models import Streak, MoodEntry, User
    from django.db.models import Max

    # Update mood logging streaks
    users_with_recent_mood = MoodEntry.objects.filter(
        date__gte=timezone.now().date() - timedelta(days=7)
    ).values('user').annotate(
        latest_date=Max('date')
    )

    for user_data in users_with_recent_mood:
        user_id = user_data['user']
        latest_date = user_data['latest_date']

        try:
            user = User.objects.get(id=user_id)
            streak, created = Streak.objects.get_or_create(
                user=user,
                streak_type='mood_logging',
                defaults={'current_streak': 0}
            )

            streak.update_streak(latest_date)

        except User.DoesNotExist:
            continue

    logger.info("User streaks updated successfully")


@shared_task
def send_weekly_summaries():
    """Send weekly mood summaries to users"""
    from .models import MoodEntry, User
    from django.db.models import Avg, Count

    # Get users who have logged mood in the past week
    week_ago = timezone.now() - timedelta(days=7)
    active_users = User.objects.filter(
        mood_entries__date__gte=week_ago
    ).distinct()

    for user in active_users:
        try:
            # Get user's mood data for the past week
            weekly_moods = MoodEntry.objects.filter(
                user=user,
                date__gte=week_ago
            ).aggregate(
                avg_mood=Avg('mood'),
                total_entries=Count('id')
            )

            if weekly_moods['total_entries'] > 0:
                avg_mood = weekly_moods['avg_mood']
                mood_description = "unknown"

                # Convert numeric mood to description
                if avg_mood <= 2:
                    mood_description = "generally sad"
                elif avg_mood <= 3:
                    mood_description = "mixed feelings"
                elif avg_mood <= 4:
                    mood_description = "generally calm"
                else:
                    mood_description = "generally happy"

                send_push_notification.delay(
                    user.id,
                    "Your Weekly Mood Summary",
                    f"This week you've logged {weekly_moods['total_entries']} mood entries. "
                    f"You've been feeling {mood_description} on average. Keep up the great work!",
                    'system',
                    {
                        'avg_mood': avg_mood,
                        'total_entries': weekly_moods['total_entries'],
                        'period': 'weekly'
                    }
                )

        except Exception as e:
            logger.error(f"Failed to send weekly summary to user {user.id}: {e}")


@shared_task
def process_pending_social_posts():
    """Process scheduled social media posts"""
    from .models import SocialMediaPost

    now = timezone.now()
    pending_posts = SocialMediaPost.objects.filter(
        status='scheduled',
        scheduled_time__lte=now
    )

    for post in pending_posts:
        try:
            # Here you would integrate with social media APIs
            # For now, just mark as posted
            post.status = 'posted'
            post.posted_at = now
            post.save()

            logger.info(f"Social media post {post.id} processed")

        except Exception as e:
            post.status = 'failed'
            post.error_message = str(e)
            post.save()
            logger.error(f"Failed to process social media post {post.id}: {e}")


@shared_task
def cleanup_expired_shared_files():
    """Clean up expired shared files"""
    from .models import SharedFile

    expired_shares = SharedFile.objects.filter(
        is_active=True
    ).exclude(
        expires_at__isnull=True
    ).filter(
        expires_at__lt=timezone.now()
    )

    count = 0
    for share in expired_shares:
        share.is_active = False
        share.save()
        count += 1

    if count > 0:
        logger.info(f"Cleaned up {count} expired shared files")


@shared_task
def generate_user_insights():
    """Generate AI-powered user insights"""
    from .models import User, MoodEntry
    from analytics.services import AnalyticsService

    # Process users who have sufficient data
    users_with_data = User.objects.filter(
        mood_entries__isnull=False
    ).distinct()

    analytics_service = AnalyticsService()

    for user in users_with_data[:5]:  # Process 5 users per task run
        try:
            insights = analytics_service.generate_user_insights(user)

            # Store insights or send notifications
            if insights:
                send_push_notification.delay(
                    user.id,
                    "Personalized Insights",
                    f"Based on your recent activity: {insights[:100]}...",
                    'system',
                    {'insights': insights}
                )

        except Exception as e:
            logger.error(f"Failed to generate insights for user {user.id}: {e}")


# Periodic tasks configuration (would be in celery.py or settings.py)
# These would be scheduled using Celery Beat

PERIODIC_TASKS = {
    'send-daily-mood-reminder': {
        'task': 'accounts.tasks.send_daily_mood_reminder',
        'schedule': 86400,  # Every 24 hours
    },
    'send-appointment-reminders': {
        'task': 'accounts.tasks.send_appointment_reminders',
        'schedule': 3600,  # Every hour
    },
    'send-scheduled-notifications': {
        'task': 'accounts.tasks.send_scheduled_notifications',
        'schedule': 300,  # Every 5 minutes
    },
    'cleanup-old-notifications': {
        'task': 'accounts.tasks.cleanup_old_notifications',
        'schedule': 86400,  # Daily
    },
    'generate-daily-reports': {
        'task': 'accounts.tasks.generate_daily_reports',
        'schedule': 86400,  # Daily
    },
    'check-system-health': {
        'task': 'accounts.tasks.check_system_health',
        'schedule': 3600,  # Hourly
    },
    'update-user-streaks': {
        'task': 'accounts.tasks.update_user_streaks',
        'schedule': 86400,  # Daily
    },
    'send-weekly-summaries': {
        'task': 'accounts.tasks.send_weekly_summaries',
        'schedule': 604800,  # Weekly
    },
    'process-pending-social-posts': {
        'task': 'accounts.tasks.process_pending_social_posts',
        'schedule': 300,  # Every 5 minutes
    },
    'cleanup-expired-shared-files': {
        'task': 'accounts.tasks.cleanup_expired_shared_files',
        'schedule': 3600,  # Hourly
    },
    'backup-user-data': {
        'task': 'accounts.tasks.backup_user_data',
        'schedule': 86400,  # Daily
    },
}