from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Achievement, MoodEntry
from .social_integrations import FacebookService, TwitterService


@receiver(post_save, sender=Achievement)
def share_achievement_on_social_media(sender, instance, created, **kwargs):
    """Automatically share achievements on social media when unlocked"""
    if not created:
        return  # Only share new achievements

    try:
        social_integration = instance.user.social_integration

        if not social_integration.sharing_enabled or not social_integration.auto_share_achievements:
            return

        # Share on connected platforms
        if social_integration.is_platform_connected('facebook'):
            service = FacebookService(social_integration)
            service.share_achievement(instance)

        if social_integration.is_platform_connected('twitter'):
            service = TwitterService(social_integration)
            service.share_achievement(instance)

    except Exception as e:
        # Log error but don't break the achievement creation
        print(f"Error sharing achievement: {e}")


@receiver(post_save, sender=MoodEntry)
def share_mood_data_on_social_media(sender, instance, created, **kwargs):
    """Automatically share mood data on social media when logged"""
    if not created:
        return  # Only share new mood entries

    try:
        social_integration = instance.user.social_integration

        if not social_integration.sharing_enabled or not social_integration.auto_share_milestones:
            return

        # Share on connected platforms
        if social_integration.is_platform_connected('facebook'):
            service = FacebookService(social_integration)
            service.share_mood_data(instance)

        if social_integration.is_platform_connected('twitter'):
            service = TwitterService(social_integration)
            service.share_mood_data(instance)

    except Exception as e:
        # Log error but don't break the mood entry creation
        print(f"Error sharing mood data: {e}")