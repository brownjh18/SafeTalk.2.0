import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import MoodEntry, Achievement, UserSubscription, SubscriptionPlan

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )

    def test_user_creation(self):
        """Test that a user can be created with proper attributes"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'client')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_str_method(self):
        """Test the string representation of User model"""
        expected = f"{self.user.username} ({self.user.get_role_display()})"
        self.assertEqual(str(self.user), expected)


class MoodEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_mood_entry_creation(self):
        """Test that mood entries can be created"""
        mood_entry = MoodEntry.objects.create(
            user=self.user,
            mood='happy',
            note='Feeling great today!'
        )
        self.assertEqual(mood_entry.user, self.user)
        self.assertEqual(mood_entry.mood, 'happy')
        self.assertEqual(mood_entry.note, 'Feeling great today!')

    def test_mood_entry_unique_constraint(self):
        """Test that only one mood entry per user per date is allowed"""
        from django.utils import timezone
        today = timezone.now().date()

        MoodEntry.objects.create(user=self.user, mood='happy', date=today)

        with self.assertRaises(Exception):  # Should raise IntegrityError
            MoodEntry.objects.create(user=self.user, mood='sad', date=today)


class SubscriptionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='basic',
            display_name='Basic Plan',
            description='Basic subscription plan',
            price_monthly=9.99,
            features=['Feature 1', 'Feature 2']
        )

    def test_subscription_creation(self):
        """Test that subscriptions can be created"""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active'
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, 'active')
        self.assertTrue(subscription.is_active())


class ViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_view(self):
        """Test login view"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')


class GamificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_achievement_creation(self):
        """Test that achievements can be created"""
        achievement = Achievement.objects.create(
            user=self.user,
            achievement_type='first_mood_log',
            description='Logged your first mood entry',
            icon='📝'
        )
        self.assertEqual(achievement.user, self.user)
        self.assertEqual(achievement.achievement_type, 'first_mood_log')
        self.assertEqual(str(achievement), f"{self.user.username} - First Mood Log")


class IntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_complete_user_journey(self):
        """Test a complete user journey from registration to mood logging"""
        # Login
        self.client.login(username='testuser', password='testpass123')

        # Access profile
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

        # Log mood
        response = self.client.post(reverse('log_mood'), {
            'mood': 'happy',
            'note': 'Test mood entry'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check mood was logged
        mood_entry = MoodEntry.objects.filter(user=self.user).first()
        self.assertIsNotNone(mood_entry)
        self.assertEqual(mood_entry.mood, 'happy')
        self.assertEqual(mood_entry.note, 'Test mood entry')

        # Check achievements were awarded
        achievement = Achievement.objects.filter(
            user=self.user,
            achievement_type='first_mood_log'
        ).first()
        self.assertIsNotNone(achievement)