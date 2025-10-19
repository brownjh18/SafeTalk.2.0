from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from accounts.models import MoodEntry, User
from chat.models import AIMessage, AIConversation
from .services import AnalyticsService
from .ml_models import SentimentAnalysisModel
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MoodEntry)
def update_mood_analytics(sender, instance, created, **kwargs):
    """Update mood analytics when mood entries are saved"""
    try:
        if created:
            # Analyze mood patterns for the user
            AnalyticsService.analyze_mood_patterns(instance.user)

            # Update user analytics
            AnalyticsService.update_user_analytics(instance.user)

    except Exception as e:
        logger.error(f"Error updating mood analytics: {str(e)}")


@receiver(post_save, sender=AIMessage)
def analyze_chat_sentiment(sender, instance, created, **kwargs):
    """Analyze sentiment when AI messages are saved"""
    try:
        if created:
            # Analyze sentiment for the conversation
            AnalyticsService.analyze_chat_sentiment(instance.conversation.user, instance.conversation)

            # Update user analytics
            AnalyticsService.update_user_analytics(instance.conversation.user)

    except Exception as e:
        logger.error(f"Error analyzing chat sentiment: {str(e)}")


@receiver(post_save, sender=User)
def create_user_analytics(sender, instance, created, **kwargs):
    """Create initial analytics record when user is created"""
    try:
        if created:
            AnalyticsService.update_user_analytics(instance)

            # Generate initial personalized insights
            AnalyticsService.get_personalized_insights(instance)

    except Exception as e:
        logger.error(f"Error creating user analytics: {str(e)}")


# Periodic analytics updates (would be handled by Celery tasks in production)
def update_all_user_analytics():
    """Batch update analytics for all users (for periodic tasks)"""
    try:
        users = User.objects.all()
        for user in users:
            AnalyticsService.update_user_analytics(user)
            AnalyticsService.analyze_mood_patterns(user)
            AnalyticsService.get_personalized_insights(user)

        logger.info(f"Updated analytics for {users.count()} users")

    except Exception as e:
        logger.error(f"Error in batch analytics update: {str(e)}")


def generate_weekly_reports():
    """Generate weekly analytics reports for all users"""
    try:
        users = User.objects.all()
        report_count = 0

        for user in users:
            report = AnalyticsService.generate_user_report(user, 'weekly')
            if report:
                report_count += 1

        logger.info(f"Generated {report_count} weekly reports")

    except Exception as e:
        logger.error(f"Error generating weekly reports: {str(e)}")


def perform_risk_assessments():
    """Perform risk assessments for high-risk users"""
    try:
        from .models import UserAnalytics

        # Get users with high risk scores
        high_risk_users = UserAnalytics.objects.filter(
            risk_score__gte=60
        ).values_list('user', flat=True)

        assessment_count = 0
        for user_id in high_risk_users:
            try:
                user = User.objects.get(id=user_id)
                assessment = AnalyticsService.assess_user_risk(user)
                if assessment:
                    assessment_count += 1
            except User.DoesNotExist:
                continue

        logger.info(f"Performed risk assessments for {assessment_count} users")

    except Exception as e:
        logger.error(f"Error performing risk assessments: {str(e)}")


def cleanup_old_analytics():
    """Clean up old analytics data to manage database size"""
    try:
        from .models import MoodAnalytics, ChatAnalytics, BehaviorMetrics

        # Keep only last 6 months of detailed analytics
        cutoff_date = timezone.now() - timedelta(days=180)

        mood_deleted = MoodAnalytics.objects.filter(date__lt=cutoff_date).delete()[0]
        chat_deleted = ChatAnalytics.objects.filter(created_at__lt=cutoff_date).delete()[0]
        behavior_deleted = BehaviorMetrics.objects.filter(period_end__lt=cutoff_date).delete()[0]

        logger.info(f"Cleaned up analytics: {mood_deleted} mood, {chat_deleted} chat, {behavior_deleted} behavior records")

    except Exception as e:
        logger.error(f"Error cleaning up analytics: {str(e)}")