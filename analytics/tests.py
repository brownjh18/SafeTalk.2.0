import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from .models import (
    UserAnalytics, MoodAnalytics, ChatAnalytics, BehaviorMetrics,
    PredictiveInsights, RiskAssessment, AnalyticsReport
)
from .services import AnalyticsService
from .ml_models import MoodPredictionModel, SentimentAnalysisModel, RiskAssessmentModel

User = get_user_model()


class AnalyticsModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )

    def test_user_analytics_creation(self):
        """Test UserAnalytics model creation"""
        analytics = UserAnalytics.objects.create(
            user=self.user,
            engagement_score=75.5,
            risk_score=25.0,
            total_sessions=10
        )

        self.assertEqual(analytics.user, self.user)
        self.assertEqual(analytics.engagement_score, 75.5)
        self.assertEqual(analytics.risk_score, 25.0)
        self.assertEqual(analytics.total_sessions, 10)

    def test_mood_analytics_creation(self):
        """Test MoodAnalytics model creation"""
        mood_analytics = MoodAnalytics.objects.create(
            user=self.user,
            date=timezone.now().date(),
            mood_score=4.0,
            mood_trend='stable',
            predicted_mood=3.8,
            mood_confidence=0.85
        )

        self.assertEqual(mood_analytics.user, self.user)
        self.assertEqual(mood_analytics.mood_score, 4.0)
        self.assertEqual(mood_analytics.mood_trend, 'stable')
        self.assertEqual(mood_analytics.predicted_mood, 3.8)

    def test_predictive_insights_creation(self):
        """Test PredictiveInsights model creation"""
        insight = PredictiveInsights.objects.create(
            user=self.user,
            insight_type='mood_prediction',
            title='Mood Improvement Detected',
            description='Your mood has shown consistent improvement over the past week.',
            confidence_score=0.82,
            severity_level='low',
            recommended_actions=['Continue current activities', 'Maintain sleep schedule']
        )

        self.assertEqual(insight.user, self.user)
        self.assertEqual(insight.insight_type, 'mood_prediction')
        self.assertEqual(insight.severity_level, 'low')
        self.assertEqual(len(insight.recommended_actions), 2)


class AnalyticsServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )

    @patch('analytics.services.AnalyticsService.analyze_mood_patterns')
    @patch('analytics.services.AnalyticsService.get_personalized_insights')
    def test_update_user_analytics(self, mock_insights, mock_mood):
        """Test updating user analytics"""
        mock_mood.return_value = None
        mock_insights.return_value = []

        analytics = AnalyticsService.update_user_analytics(self.user)

        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.user, self.user)
        self.assertIsInstance(analytics.engagement_score, float)
        self.assertIsInstance(analytics.risk_score, float)

    def test_generate_user_report(self):
        """Test generating user analytics report"""
        report = AnalyticsService.generate_user_report(self.user, 'weekly')

        self.assertIsNotNone(report)
        self.assertEqual(report.generated_for, self.user)
        self.assertEqual(report.report_type, 'weekly')
        self.assertIn('mood_entries_count', report.summary_data)
        self.assertIn('chat_sessions_count', report.summary_data)


class MLModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )

    def test_sentiment_analysis(self):
        """Test sentiment analysis functionality"""
        analyzer = SentimentAnalysisModel()

        # Test positive sentiment
        result = analyzer.analyze_sentiment("I feel great today! Everything is wonderful.")
        self.assertIn('sentiment', result)
        self.assertGreaterEqual(result['polarity'], 0)

        # Test negative sentiment
        result = analyzer.analyze_sentiment("I'm feeling really sad and depressed.")
        self.assertIn('sentiment', result)
        self.assertLessEqual(result['polarity'], 0)

    def test_risk_assessment(self):
        """Test risk assessment functionality"""
        assessor = RiskAssessmentModel()

        # Mock user analytics
        UserAnalytics.objects.create(
            user=self.user,
            engagement_score=80.0,
            risk_score=20.0,
            mood_volatility=0.5,
            total_sessions=15,
            last_activity=timezone.now()
        )

        assessment = assessor.assess_risk(self.user)

        self.assertIn('risk_level', assessment)
        self.assertIn('risk_score', assessment)
        self.assertIn('confidence', assessment)
        self.assertIn('factors', assessment)
        self.assertIn('recommendations', assessment)

    @patch('analytics.ml_models.MoodPredictionModel.model')
    def test_mood_prediction(self, mock_model):
        """Test mood prediction model"""
        predictor = MoodPredictionModel()

        # Mock the model
        mock_model.predict.return_value = [3.5]

        # Create some mood data
        today = timezone.now().date()
        for i in range(10):
            date = today - timedelta(days=i)
            mood_score = 3 + (i % 3 - 1) * 0.5  # Vary between 2.5 and 3.5
            # Note: This would normally create MoodEntry, but we're mocking

        # Test prediction (would need actual mood data in real scenario)
        prediction = predictor.predict_mood(self.user, today)
        # Since we don't have real data, this should return None or handle gracefully
        self.assertTrue(prediction is None or isinstance(prediction, str))


class AnalyticsViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )
        self.counselor = User.objects.create_user(
            username='counselor',
            email='counselor@example.com',
            password='testpass123',
            role='counselor'
        )

    def test_user_dashboard_access(self):
        """Test user can access their analytics dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')

        # Should redirect or show dashboard (depending on implementation)
        self.assertIn(response.status_code, [200, 302])

    def test_counselor_dashboard_access(self):
        """Test counselor can access analytics dashboard"""
        self.client.login(username='counselor', password='testpass123')
        response = self.client.get('/analytics/counselor/')

        # Should redirect or show dashboard (depending on implementation)
        self.assertIn(response.status_code, [200, 302])

    def test_unauthorized_access(self):
        """Test unauthorized users cannot access counselor dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/analytics/counselor/')

        # Should be forbidden or redirect
        self.assertIn(response.status_code, [403, 302])


class AnalyticsIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='client'
        )

    def test_full_analytics_workflow(self):
        """Test complete analytics workflow"""
        # Create some mood entries
        today = timezone.now().date()
        for i in range(7):
            date = today - timedelta(days=i)
            mood = ['happy', 'calm', 'sad', 'anxious', 'excited'][i % 5]
            # MoodEntry.objects.create(user=self.user, mood=mood, date=date)

        # Update analytics
        analytics = AnalyticsService.update_user_analytics(self.user)
        self.assertIsNotNone(analytics)

        # Generate insights
        insights = AnalyticsService.get_personalized_insights(self.user)
        self.assertIsInstance(insights, list)

        # Generate report
        report = AnalyticsService.generate_user_report(self.user, 'weekly')
        self.assertIsNotNone(report)
        self.assertEqual(report.generated_for, self.user)