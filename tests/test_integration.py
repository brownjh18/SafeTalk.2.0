import json
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call
from channels.testing import WebsocketCommunicator
from safetalk.asgi import application
from accounts.models import User, MoodEntry, VideoCall, SubscriptionPlan, UserSubscription
from chat.models import Message, Session
from accounts.payment_integrations import StripePaymentService, PayPalPaymentService
from accounts.video_integrations import TwilioVideoService, ZoomVideoService, VideoCallService

User = get_user_model()


class PaymentIntegrationTest(TestCase):
    """Test payment gateway integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='payuser',
            email='pay@example.com',
            password='testpass123'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='premium',
            display_name='Premium Plan',
            price_monthly=29.99
        )

    @patch('stripe.checkout.Session.create')
    def test_stripe_checkout_creation(self, mock_stripe_session):
        """Test Stripe checkout session creation"""
        mock_session = {
            'id': 'cs_test_123',
            'url': 'https://checkout.stripe.com/test'
        }
        mock_stripe_session.return_value = mock_session

        service = StripePaymentService()
        checkout_session = service.create_subscription_checkout_session(self.user, self.plan)

        self.assertIsNotNone(checkout_session)
        self.assertEqual(checkout_session.url, 'https://checkout.stripe.com/test')
        mock_stripe_session.assert_called_once()

    @patch('requests.post')
    def test_paypal_subscription_creation(self, mock_post):
        """Test PayPal subscription creation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'I-1234567890',
            'status': 'APPROVAL_PENDING',
            'links': [{'href': 'https://paypal.com/approve', 'rel': 'approve'}]
        }
        mock_post.return_value = mock_response

        service = PayPalPaymentService()
        subscription = service.create_subscription(self.user, self.plan)

        self.assertIsNotNone(subscription)
        self.assertEqual(subscription['id'], 'I-1234567890')
        mock_post.assert_called()

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_processing(self, mock_construct_event):
        """Test Stripe webhook event processing"""
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer_email': 'pay@example.com',
                    'metadata': {'plan_name': 'premium'}
                }
            }
        }
        mock_construct_event.return_value = mock_event

        service = StripePaymentService()
        success = service.process_webhook({'type': 'checkout.session.completed'})

        self.assertTrue(success)


class VideoIntegrationTest(TestCase):
    """Test video calling integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='videouser',
            email='video@example.com',
            password='testpass123'
        )

    @patch('twilio.rest.Client')
    def test_twilio_room_creation(self, mock_twilio_client):
        """Test Twilio room creation"""
        mock_client_instance = MagicMock()
        mock_room = MagicMock()
        mock_room.sid = 'RM1234567890'
        mock_room.unique_name = 'test_room'
        mock_room.status = 'in-progress'
        mock_room.type = 'group'
        mock_client_instance.video.rooms.create.return_value = mock_room
        mock_twilio_client.return_value = mock_client_instance

        service = TwilioVideoService()
        room = service.create_room('test_room', 'group')

        self.assertIsNotNone(room)
        self.assertEqual(room['sid'], 'RM1234567890')
        self.assertEqual(room['name'], 'test_room')

    @patch('jwt.encode')
    @patch('requests.post')
    def test_zoom_meeting_creation(self, mock_post, mock_jwt_encode):
        """Test Zoom meeting creation"""
        mock_jwt_encode.return_value = 'fake_jwt_token'

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 123456789,
            'join_url': 'https://zoom.us/j/123456789',
            'start_url': 'https://zoom.us/s/123456789',
            'password': 'zoompass'
        }
        mock_post.return_value = mock_response

        service = ZoomVideoService()
        meeting = service.create_meeting('Test Meeting', timezone.now() + timedelta(hours=1), 60)

        self.assertIsNotNone(meeting)
        self.assertEqual(meeting['id'], 123456789)
        self.assertEqual(meeting['join_url'], 'https://zoom.us/j/123456789')

    def test_video_call_service_unified_interface(self):
        """Test unified video call service interface"""
        with patch('accounts.video_integrations.TwilioVideoService') as mock_twilio:
            mock_twilio_instance = MagicMock()
            mock_twilio_instance.create_call.return_value = {'room_sid': 'RM123'}
            mock_twilio.return_value = mock_twilio_instance

            service = VideoCallService('twilio')
            call_data = {'room_name': 'test_call'}
            result = service.create_call(call_data)

            self.assertIsNotNone(result)
            mock_twilio_instance.create_call.assert_called_once_with(call_data)


class WebSocketIntegrationTest(TransactionTestCase):
    """Test WebSocket integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='wsuser',
            email='ws@example.com',
            password='testpass123'
        )
        self.session = Session.objects.create(title='WebSocket Test')

    async def test_chat_websocket_connection(self):
        """Test WebSocket connection for chat"""
        communicator = WebsocketCommunicator(
            application,
            f'/ws/chat/{self.session.id}/'
        )
        communicator.scope['user'] = self.user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Test sending a message
        message_data = {
            'type': 'chat_message',
            'message': 'Hello WebSocket!',
            'session_id': self.session.id
        }

        await communicator.send_json_to(message_data)

        # Receive response
        response = await communicator.receive_json_from()
        self.assertIn('type', response)

        await communicator.disconnect()

    async def test_video_call_websocket(self):
        """Test WebSocket for video call signaling"""
        video_call = VideoCall.objects.create(
            title='WebSocket Test Call',
            host=self.user,
            provider='twilio',
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=1)
        )

        communicator = WebsocketCommunicator(
            application,
            f'/ws/video-call/{video_call.id}/'
        )
        communicator.scope['user'] = self.user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Test sending signaling data
        signaling_data = {
            'type': 'webrtc_offer',
            'offer': {'type': 'offer', 'sdp': 'fake_sdp'},
            'target_user_id': self.user.id
        }

        await communicator.send_json_to(signaling_data)

        # Should receive acknowledgment or relay
        response = await communicator.receive_json_from()
        self.assertIn('type', response)

        await communicator.disconnect()


class EmailIntegrationTest(TestCase):
    """Test email notification integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='emailuser',
            email='email@example.com',
            password='testpass123'
        )

    @patch('django.core.mail.send_mail')
    def test_appointment_notification_email(self, mock_send_mail):
        """Test appointment notification email"""
        from accounts.notifications import NotificationService

        service = NotificationService()
        success = service.send_appointment_notification(
            self.user,
            'Test Appointment',
            timezone.now() + timedelta(days=1)
        )

        self.assertTrue(success)
        mock_send_mail.assert_called_once()

        # Check call arguments
        call_args = mock_send_mail.call_args
        self.assertIn('Appointment Reminder', call_args[0][0])  # subject
        self.assertEqual(call_args[0][3], [self.user.email])  # recipient

    @patch('django.core.mail.send_mail')
    def test_mood_tracking_reminder(self, mock_send_mail):
        """Test mood tracking reminder email"""
        from accounts.notifications import NotificationService

        service = NotificationService()
        success = service.send_mood_reminder(self.user)

        self.assertTrue(success)
        mock_send_mail.assert_called_once()

        call_args = mock_send_mail.call_args
        self.assertIn('Mood Check-in', call_args[0][0])


class SocialMediaIntegrationTest(TestCase):
    """Test social media integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='socialuser',
            email='social@example.com',
            password='testpass123'
        )
        self.mood_entry = MoodEntry.objects.create(
            user=self.user,
            mood='happy',
            note='Feeling great!'
        )

    @patch('requests.post')
    def test_facebook_posting(self, mock_post):
        """Test Facebook API posting"""
        from accounts.social_integrations import FacebookService

        mock_response = MagicMock()
        mock_response.json.return_value = {'id': '1234567890'}
        mock_post.return_value = mock_response

        service = FacebookService()
        success = service.post_content('facebook', 'Test post')

        self.assertTrue(success)
        mock_post.assert_called()

    @patch('requests.post')
    def test_twitter_posting(self, mock_post):
        """Test Twitter API posting"""
        from accounts.social_integrations import TwitterService

        mock_response = MagicMock()
        mock_response.json.return_value = {'data': {'id': '1234567890'}}
        mock_post.return_value = mock_response

        service = TwitterService()
        success = service.post_content('twitter', 'Test tweet')

        self.assertTrue(success)
        mock_post.assert_called()


class CalendarIntegrationTest(TestCase):
    """Test Google Calendar integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='caluser',
            email='cal@example.com',
            password='testpass123'
        )

    @patch('googleapiclient.discovery.build')
    def test_calendar_event_creation(self, mock_build):
        """Test Google Calendar event creation"""
        from accounts.integrations import GoogleCalendarService

        # Mock the Google API client
        mock_service = MagicMock()
        mock_event = {
            'id': 'event_123',
            'htmlLink': 'https://calendar.google.com/event?id=event_123'
        }
        mock_service.events().insert().execute.return_value = mock_event
        mock_build.return_value = mock_service

        calendar_integration = MagicMock()
        calendar_integration.access_token = 'fake_token'
        calendar_integration.google_calendar_id = 'calendar@group.calendar.google.com'

        service = GoogleCalendarService(calendar_integration)

        # Create a test appointment
        from accounts.models import Appointment
        appointment = Appointment.objects.create(
            counselor=self.user,
            client=self.user,
            title='Test Appointment',
            scheduled_date=timezone.now() + timedelta(days=1),
            duration_minutes=60
        )

        event_id = service.create_event(appointment)
        self.assertEqual(event_id, 'event_123')


class AIMLIntegrationTest(TestCase):
    """Test AI/ML integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='aiuser',
            email='ai@example.com',
            password='testpass123'
        )

    @patch('openai.ChatCompletion.create')
    def test_openai_chat_completion(self, mock_create):
        """Test OpenAI API integration"""
        from analytics.ml_models import MoodPredictionModel

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"mood": "happy", "confidence": 0.85}'
        mock_create.return_value = mock_response

        model = MoodPredictionModel()
        prediction = model.predict_mood(['I feel great today!', 'Had a wonderful day'])

        self.assertIsNotNone(prediction)
        self.assertEqual(prediction['mood'], 'happy')

    @patch('transformers.pipeline')
    def test_sentiment_analysis(self, mock_pipeline):
        """Test sentiment analysis integration"""
        from analytics.ml_models import SentimentAnalysisModel

        mock_analyzer = MagicMock()
        mock_analyzer.return_value = [{'label': 'POSITIVE', 'score': 0.95}]
        mock_pipeline.return_value = mock_analyzer

        model = SentimentAnalysisModel()
        sentiment = model.analyze_sentiment('I am feeling very happy today!')

        self.assertIsNotNone(sentiment)
        self.assertEqual(sentiment[0]['label'], 'POSITIVE')


class SecurityIntegrationTest(TestCase):
    """Test security integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='secuser',
            email='sec@example.com',
            password='testpass123'
        )

    @patch('requests.post')
    def test_recaptcha_verification(self, mock_post):
        """Test reCAPTCHA verification"""
        from safetalk.security import SecurityService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'challenge_ts': '2023-01-01T00:00:00Z',
            'hostname': 'example.com'
        }
        mock_post.return_value = mock_response

        service = SecurityService()
        is_valid = service.verify_recaptcha('fake_token')

        self.assertTrue(is_valid)
        mock_post.assert_called()

    def test_password_strength_validation(self):
        """Test password strength validation"""
        from safetalk.security import SecurityService

        service = SecurityService()

        # Test weak password
        is_strong, errors = service.validate_password_strength('123')
        self.assertFalse(is_strong)
        self.assertIn('too short', ' '.join(errors).lower())

        # Test strong password
        is_strong, errors = service.validate_password_strength('MyStr0ngP@ssw0rd!')
        self.assertTrue(is_strong)
        self.assertEqual(len(errors), 0)


class PerformanceIntegrationTest(TestCase):
    """Test performance and caching integrations"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='testpass123'
        )

    def test_analytics_caching(self):
        """Test analytics data caching"""
        from analytics.services import AnalyticsService
        from django.core.cache import cache

        # Clear cache
        cache.clear()

        service = AnalyticsService()
        data1 = service.get_dashboard_overview()

        # Should be cached
        cached_data = cache.get('dashboard_overview')
        self.assertIsNotNone(cached_data)

        # Second call should use cache
        data2 = service.get_dashboard_overview()
        self.assertEqual(data1, data2)

    @patch('django.core.cache.cache.set')
    def test_cache_invalidation(self, mock_cache_set):
        """Test cache invalidation on data changes"""
        from analytics.services import AnalyticsService

        service = AnalyticsService()

        # Create a mood entry (should invalidate relevant caches)
        MoodEntry.objects.create(user=self.user, mood='happy')

        # Get analytics (should trigger cache updates)
        service.get_mood_analytics()

        # Verify cache.set was called
        mock_cache_set.assert_called()


class ExternalAPIIntegrationTest(TestCase):
    """Test external API integrations"""

    @patch('requests.get')
    def test_weather_api_integration(self, mock_get):
        """Test weather API for mood correlation"""
        from safetalk.integrations import WeatherService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'weather': [{'main': 'Clear', 'description': 'clear sky'}],
            'main': {'temp': 22.5, 'humidity': 65}
        }
        mock_get.return_value = mock_response

        service = WeatherService()
        weather = service.get_weather('New York')

        self.assertIsNotNone(weather)
        self.assertEqual(weather['weather'][0]['main'], 'Clear')

    @patch('requests.get')
    def test_news_api_integration(self, mock_get):
        """Test news API for mental health resources"""
        from safetalk.integrations import NewsService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'articles': [
                {
                    'title': 'Mental Health Awareness Day',
                    'description': 'Learn about mental health resources',
                    'url': 'https://example.com/article1'
                }
            ]
        }
        mock_get.return_value = mock_response

        service = NewsService()
        articles = service.get_mental_health_news()

        self.assertIsNotNone(articles)
        self.assertEqual(len(articles['articles']), 1)
        self.assertIn('Mental Health', articles['articles'][0]['title'])