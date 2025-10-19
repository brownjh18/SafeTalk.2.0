import os
import logging
import requests
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from .models import SocialMediaIntegration, SocialMediaPost, MoodDataShare, MoodEntry, Achievement

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Base class for social media integrations"""

    def __init__(self, social_integration):
        self.social_integration = social_integration

    def is_connected(self, platform):
        """Check if a platform is connected"""
        return self.social_integration.is_platform_connected(platform)

    def post_content(self, platform, content, image_url=None):
        """Post content to a social media platform"""
        raise NotImplementedError("Subclasses must implement post_content")

    def share_achievement(self, achievement):
        """Share an achievement on social media"""
        if not self.social_integration.sharing_enabled or not self.social_integration.auto_share_achievements:
            return False

        content = f"🏆 Achievement Unlocked: {achievement.get_achievement_type_display()}!\n\n{achievement.description}"

        success = False
        if self.is_connected('facebook'):
            success |= self.post_content('facebook', content)
        if self.is_connected('twitter'):
            success |= self.post_content('twitter', content)

        return success

    def share_mood_data(self, mood_entry):
        """Share mood tracking data on social media"""
        if not self.social_integration.sharing_enabled:
            return False

        mood_emoji = mood_entry.get_mood_display().split(' ')[0]  # Get emoji
        content = f"{mood_emoji} Feeling {mood_entry.get_mood_display()} today"

        if mood_entry.note:
            content += f"\n\n{mood_entry.note}"

        content += "\n\n#MentalHealth #MoodTracking #SafeTalk"

        # Create MoodDataShare record
        share = MoodDataShare.objects.create(
            user=mood_entry.user,
            mood_entry=mood_entry,
            platform='multiple',  # Will be updated per platform
            shared_content=content
        )

        success = False
        if self.is_connected('facebook'):
            if self.post_content('facebook', content):
                MoodDataShare.objects.create(
                    user=mood_entry.user,
                    mood_entry=mood_entry,
                    platform='facebook',
                    shared_content=content,
                    is_successful=True
                )
                success = True

        if self.is_connected('twitter'):
            if self.post_content('twitter', content):
                MoodDataShare.objects.create(
                    user=mood_entry.user,
                    mood_entry=mood_entry,
                    platform='twitter',
                    shared_content=content,
                    is_successful=True
                )
                success = True

        return success


class FacebookService(SocialMediaService):
    """Facebook social media integration"""

    GRAPH_API_BASE = "https://graph.facebook.com/v18.0"

    def post_content(self, platform, content, image_url=None):
        """Post content to Facebook"""
        if not self.is_connected('facebook'):
            return False

        try:
            access_token = self.social_integration.facebook_access_token
            url = f"{self.GRAPH_API_BASE}/me/feed"

            data = {
                'message': content,
                'access_token': access_token
            }

            if image_url:
                data['link'] = image_url

            response = requests.post(url, data=data)
            response.raise_for_status()

            result = response.json()
            post_id = result.get('id')

            # Update last post time
            self.social_integration.last_facebook_post = timezone.now()
            self.social_integration.save()

            logger.info(f"Posted to Facebook for user {self.social_integration.user.username}")
            return post_id

        except requests.RequestException as e:
            logger.error(f"Facebook API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error posting to Facebook: {str(e)}")
            return False


class TwitterService(SocialMediaService):
    """Twitter/X social media integration"""

    API_BASE = "https://api.twitter.com/2"

    def post_content(self, platform, content, image_url=None):
        """Post content to Twitter"""
        if not self.is_connected('twitter'):
            return False

        try:
            access_token = self.social_integration.twitter_access_token
            access_token_secret = self.social_integration.twitter_token_secret

            # For simplicity, using requests with Bearer token
            # In production, you'd want to use Tweepy or similar library
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            data = {'text': content}

            response = requests.post(
                f"{self.API_BASE}/tweets",
                headers=headers,
                json=data
            )
            response.raise_for_status()

            result = response.json()
            tweet_id = result.get('data', {}).get('id')

            # Update last post time
            self.social_integration.last_twitter_post = timezone.now()
            self.social_integration.save()

            logger.info(f"Posted to Twitter for user {self.social_integration.user.username}")
            return tweet_id

        except requests.RequestException as e:
            logger.error(f"Twitter API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error posting to Twitter: {str(e)}")
            return False


class SocialMediaScheduler:
    """Service for scheduling social media posts"""

    @staticmethod
    def process_scheduled_posts():
        """Process all posts that are ready to be published"""
        ready_posts = SocialMediaPost.objects.filter(
            status='scheduled',
            scheduled_time__lte=timezone.now()
        )

        processed_count = 0
        for post in ready_posts:
            if SocialMediaScheduler._publish_post(post):
                processed_count += 1

        logger.info(f"Processed {processed_count} scheduled social media posts")
        return processed_count

    @staticmethod
    def _publish_post(post):
        """Publish a single social media post"""
        try:
            social_integration = post.user.social_integration

            if post.platform == 'facebook' and social_integration.is_platform_connected('facebook'):
                service = FacebookService(social_integration)
                post_id = service.post_content('facebook', post.content, post.image_url)
                if post_id:
                    post.post_id = post_id
                    post.status = 'posted'
                    post.posted_at = timezone.now()
                else:
                    post.status = 'failed'
                    post.error_message = "Failed to post to Facebook"

            elif post.platform == 'twitter' and social_integration.is_platform_connected('twitter'):
                service = TwitterService(social_integration)
                post_id = service.post_content('twitter', post.content, post.image_url)
                if post_id:
                    post.post_id = post_id
                    post.status = 'posted'
                    post.posted_at = timezone.now()
                else:
                    post.status = 'failed'
                    post.error_message = "Failed to post to Twitter"

            else:
                post.status = 'failed'
                post.error_message = f"{post.platform} not connected or not supported"

            post.save()
            return post.status == 'posted'

        except Exception as e:
            logger.error(f"Error publishing post {post.id}: {str(e)}")
            post.status = 'failed'
            post.error_message = str(e)
            post.save()
            return False


class MentalHealthContentScheduler:
    """Service for scheduling mental health awareness content"""

    MENTAL_HEALTH_CONTENT = [
        {
            'content': "🌟 Remember: Your mental health matters. Taking small steps each day can make a big difference. #MentalHealthAwareness #SafeTalk",
            'hashtags': ['MentalHealth', 'SelfCare', 'Wellbeing']
        },
        {
            'content': "💪 Building resilience takes time. Be patient with yourself and celebrate small victories. #MentalHealth #Resilience",
            'hashtags': ['MentalHealth', 'Resilience', 'Growth']
        },
        {
            'content': "🗣️ It's okay to ask for help. Reaching out is a sign of strength, not weakness. #MentalHealth #AskForHelp",
            'hashtags': ['MentalHealth', 'Support', 'Strength']
        },
        {
            'content': "😌 Practice mindfulness: Take a moment to breathe and be present. Your mind will thank you. #Mindfulness #MentalHealth",
            'hashtags': ['Mindfulness', 'MentalHealth', 'Wellness']
        },
        {
            'content': "🤝 You're not alone in this journey. Connect with others who understand. #MentalHealth #Community",
            'hashtags': ['MentalHealth', 'Community', 'Support']
        }
    ]

    @staticmethod
    def schedule_weekly_awareness_posts(user):
        """Schedule weekly mental health awareness posts for a user"""
        try:
            social_integration = user.social_integration
            if not social_integration.sharing_enabled:
                return 0

            scheduled_count = 0
            now = timezone.now()

            # Schedule one post per week for the next month
            for i in range(4):
                scheduled_time = now + timezone.timedelta(days=7 * (i + 1))

                # Randomly select content
                content_data = MentalHealthContentScheduler.MENTAL_HEALTH_CONTENT[
                    i % len(MentalHealthContentScheduler.MENTAL_HEALTH_CONTENT)
                ]

                # Create posts for connected platforms
                if social_integration.is_platform_connected('facebook'):
                    SocialMediaPost.objects.create(
                        user=user,
                        platform='facebook',
                        content=content_data['content'],
                        scheduled_time=scheduled_time,
                        status='scheduled'
                    )
                    scheduled_count += 1

                if social_integration.is_platform_connected('twitter'):
                    SocialMediaPost.objects.create(
                        user=user,
                        platform='twitter',
                        content=content_data['content'],
                        scheduled_time=scheduled_time,
                        status='scheduled'
                    )
                    scheduled_count += 1

            logger.info(f"Scheduled {scheduled_count} awareness posts for user {user.username}")
            return scheduled_count

        except Exception as e:
            logger.error(f"Error scheduling awareness posts for user {user.username}: {str(e)}")
            return 0