import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import (
    User, MoodEntry, Achievement, Appointment, VideoCall,
    SubscriptionPlan, UserSubscription, Payment, Invoice
)
from chat.models import Message, Session, Notification
from analytics.models import UserAnalytics, MoodAnalytics, ChatAnalytics

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )

    def test_user_creation(self):
        """Test user creation with proper attributes"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'client')
        self.assertTrue(self.user.is_active)

    def test_user_str_method(self):
        """Test user string representation"""
        expected = f"{self.user.username} ({self.user.get_role_display()})"
        self.assertEqual(str(self.user), expected)

    def test_notification_preferences_defaults(self):
        """Test notification preferences default values"""
        self.assertTrue(self.user.notifications_enabled)
        self.assertTrue(self.user.notification_message)
        self.assertTrue(self.user.notification_appointment)


class MoodEntryModelTest(TestCase):
    """Test MoodEntry model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='mooduser',
            email='mood@example.com',
            password='testpass123'
        )

    def test_mood_entry_creation(self):
        """Test mood entry creation"""
        mood_entry = MoodEntry.objects.create(
            user=self.user,
            mood='happy',
            note='Feeling great today!'
        )

        self.assertEqual(mood_entry.user, self.user)
        self.assertEqual(mood_entry.mood, 'happy')
        self.assertEqual(mood_entry.note, 'Feeling great today!')

    def test_mood_entry_str_method(self):
        """Test mood entry string representation"""
        mood_entry = MoodEntry.objects.create(
            user=self.user,
            mood='sad',
            date=timezone.now().date()
        )

        expected = f"{self.user.username} - {mood_entry.get_mood_display()} on {mood_entry.date}"
        self.assertEqual(str(mood_entry), expected)

    def test_unique_together_constraint(self):
        """Test unique together constraint for user and date"""
        MoodEntry.objects.create(user=self.user, mood='happy')

        with self.assertRaises(Exception):
            MoodEntry.objects.create(user=self.user, mood='sad')


class AchievementModelTest(TestCase):
    """Test Achievement model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='achievement_user',
            email='achievement@example.com',
            password='testpass123'
        )

    def test_achievement_creation(self):
        """Test achievement creation"""
        achievement = Achievement.objects.create(
            user=self.user,
            achievement_type='first_mood_log',
            description='Logged your first mood entry!',
            icon='🏆'
        )

        self.assertEqual(achievement.user, self.user)
        self.assertEqual(achievement.achievement_type, 'first_mood_log')
        self.assertEqual(achievement.icon, '🏆')

    def test_achievement_str_method(self):
        """Test achievement string representation"""
        achievement = Achievement.objects.create(
            user=self.user,
            achievement_type='consistent_logger',
            description='Logged mood for 7 consecutive days'
        )

        expected = f"{self.user.username} - {achievement.get_achievement_type_display()}"
        self.assertEqual(str(achievement), expected)


class AppointmentModelTest(TestCase):
    """Test Appointment model functionality"""

    def setUp(self):
        self.counselor = User.objects.create_user(
            username='counselor',
            email='counselor@example.com',
            password='testpass123',
            role='counselor'
        )
        self.client = User.objects.create_user(
            username='client',
            email='client@example.com',
            password='testpass123',
            role='client'
        )

    def test_appointment_creation(self):
        """Test appointment creation"""
        appointment = Appointment.objects.create(
            counselor=self.counselor,
            client=self.client,
            title='Initial Consultation',
            description='First meeting to discuss goals',
            scheduled_date=timezone.now() + timedelta(days=1),
            duration_minutes=60,
            status='scheduled',
            notes='Counselor notes'
        )

        self.assertEqual(appointment.counselor, self.counselor)
        self.assertEqual(appointment.client, self.client)
        self.assertEqual(appointment.title, 'Initial Consultation')
        self.assertEqual(appointment.status, 'scheduled')

    def test_appointment_str_method(self):
        """Test appointment string representation"""
        appointment = Appointment.objects.create(
            counselor=self.counselor,
            client=self.client,
            title='Follow-up Session',
            scheduled_date=timezone.now(),
            notes='Follow-up notes'
        )

        expected = f"{self.client.username} with {self.counselor.username} - {appointment.scheduled_date}"
        self.assertEqual(str(appointment), expected)


class VideoCallModelTest(TestCase):
    """Test VideoCall model functionality"""

    def setUp(self):
        self.host = User.objects.create_user(
            username='host',
            email='host@example.com',
            password='testpass123',
            role='counselor'
        )
        self.participant = User.objects.create_user(
            username='participant',
            email='participant@example.com',
            password='testpass123',
            role='client'
        )

    def test_video_call_creation(self):
        """Test video call creation"""
        video_call = VideoCall.objects.create(
            title='Group Therapy Session',
            description='Weekly group therapy meeting',
            call_type='group',
            provider='twilio',
            host=self.host,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            max_participants=10,
            recording_enabled=False,
            chat_enabled=True,
            waiting_room=True
        )

        # Add participant
        video_call.participants.add(self.participant)

        self.assertEqual(video_call.title, 'Group Therapy Session')
        self.assertEqual(video_call.host, self.host)
        self.assertEqual(video_call.call_type, 'group')
        self.assertEqual(video_call.provider, 'twilio')
        self.assertTrue(video_call.participants.filter(id=self.participant.id).exists())

    def test_video_call_str_method(self):
        """Test video call string representation"""
        video_call = VideoCall.objects.create(
            title='Individual Session',
            call_type='counseling',
            host=self.host,
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1),
            status='scheduled'
        )

        expected = f"{video_call.title} - {video_call.get_call_type_display()} ({video_call.get_status_display()})"
        self.assertEqual(str(video_call), expected)

    def test_can_join_method(self):
        """Test can_join method"""
        video_call = VideoCall.objects.create(
            title='Test Call',
            host=self.host,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            status='scheduled'
        )

        # Host should be able to join
        self.assertTrue(video_call.can_join(self.host))

        # Participant should be able to join if added
        video_call.participants.add(self.participant)
        self.assertTrue(video_call.can_join(self.participant))

        # Random user should not be able to join
        random_user = User.objects.create_user(
            username='random',
            email='random@example.com',
            password='testpass123'
        )
        self.assertFalse(video_call.can_join(random_user))

        # Cannot join if call is completed
        video_call.status = 'completed'
        video_call.save()
        self.assertFalse(video_call.can_join(self.host))


class SubscriptionModelTest(TestCase):
    """Test subscription-related models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='subscriber',
            email='subscriber@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='premium',
            display_name='Premium Plan',
            description='Full access to all features',
            price_monthly=29.99,
            features=['video_calls', 'unlimited_chat', 'priority_support']
        )

    def test_subscription_plan_creation(self):
        """Test subscription plan creation"""
        self.assertEqual(self.plan.name, 'premium')
        self.assertEqual(self.plan.display_name, 'Premium Plan')
        self.assertEqual(float(self.plan.price_monthly), 29.99)
        self.assertIn('video_calls', self.plan.features)

    def test_user_subscription_creation(self):
        """Test user subscription creation"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            payment_method='card',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            auto_renew=True
        )

        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, 'active')
        self.assertTrue(subscription.is_active())

    def test_payment_creation(self):
        """Test payment record creation"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active'
        )

        payment = Payment.objects.create(
            subscription=subscription,
            amount=29.99,
            payment_method='card',
            transaction_id='txn_1234567890',
            status='completed'
        )

        self.assertEqual(payment.subscription, subscription)
        self.assertEqual(float(payment.amount), 29.99)
        self.assertEqual(payment.status, 'completed')


class MessageModelTest(TestCase):
    """Test Message model functionality"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='receiver',
            email='receiver@example.com',
            password='testpass123'
        )
        self.session = Session.objects.create(title='Test Chat')

    def test_message_creation(self):
        """Test message creation"""
        message = Message.objects.create(
            session=self.session,
            sender=self.user1,
            content='Hello, how are you?',
            message_type='text'
        )

        self.assertEqual(message.session, self.session)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, 'Hello, how are you?')
        self.assertEqual(message.message_type, 'text')
        self.assertEqual(message.status, 'sent')

    def test_message_str_method(self):
        """Test message string representation"""
        message = Message.objects.create(
            session=self.session,
            sender=self.user1,
            content='This is a test message with more content than usual'
        )

        expected = f'{self.user1}: {message.content[:50]}'
        self.assertEqual(str(message), expected)


class NotificationModelTest(TestCase):
    """Test Notification model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='notify_user',
            email='notify@example.com',
            password='testpass123'
        )

    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            title='New Message',
            message='You have received a new message',
            notification_type='message'
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'New Message')
        self.assertEqual(notification.notification_type, 'message')
        self.assertFalse(notification.is_read)

    def test_notification_str_method(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            user=self.user,
            title='Appointment Reminder',
            message='Your appointment is tomorrow'
        )

        expected = f"{self.user.username}: {notification.title}"
        self.assertEqual(str(notification), expected)


class AnalyticsModelTest(TestCase):
    """Test analytics models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='analytics_user',
            email='analytics@example.com',
            password='testpass123'
        )

    def test_user_analytics_creation(self):
        """Test user analytics creation"""
        analytics = UserAnalytics.objects.create(
            user=self.user,
            total_sessions=10,
            mood_entries_count=15,
            last_activity=timezone.now()
        )

        self.assertEqual(analytics.user, self.user)
        self.assertEqual(analytics.total_sessions, 10)
        self.assertEqual(analytics.mood_entries_count, 15)

    def test_mood_analytics_creation(self):
        """Test mood analytics creation"""
        mood_analytics = MoodAnalytics.objects.create(
            user=self.user,
            dominant_mood='happy',
            analysis_date=timezone.now().date()
        )

        self.assertEqual(mood_analytics.user, self.user)
        self.assertEqual(mood_analytics.dominant_mood, 'happy')
        self.assertEqual(mood_analytics.mood_stability_score, 8.5)

    def test_chat_analytics_creation(self):
        """Test chat analytics creation"""
        chat_analytics = ChatAnalytics.objects.create(
            user=self.user,
            total_messages_sent=50,
            analysis_date=timezone.now().date()
        )

        self.assertEqual(chat_analytics.user, self.user)
        self.assertEqual(chat_analytics.total_messages_sent, 50)
        self.assertEqual(chat_analytics.total_messages_received, 45)