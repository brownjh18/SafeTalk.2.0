from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from django.contrib.auth import get_user_model
from .models import (
    UserAnalytics, MoodAnalytics, BehaviorMetrics,
    PredictiveInsights, RiskAssessment, AnalyticsReport
)
# from .ml_models import MoodPredictionModel, SentimentAnalysisModel, RiskAssessmentModel, BehaviorAnalyticsModel  # Commented out due to numpy dependency issues
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AnalyticsService:
    """Main service for handling analytics operations"""

    @staticmethod
    def update_user_analytics(user):
        """Update comprehensive analytics for a user"""
        try:
            analytics, created = UserAnalytics.objects.get_or_create(user=user)

            # Calculate basic metrics
            now = timezone.now()
            thirty_days_ago = now - timedelta(days=30)

            # Mood-related metrics
            mood_entries = user.mood_entries.filter(date__gte=thirty_days_ago.date())
            if mood_entries:
                mood_scores = []
                for entry in mood_entries:
                    mood_mapping = {
                        'happy': 5, 'excited': 4, 'calm': 3,
                        'sad': 1, 'anxious': 2, 'angry': 1
                    }
                    mood_scores.append(mood_mapping.get(entry.mood, 3))

                analytics.mood_volatility = sum((x - sum(mood_scores)/len(mood_scores))**2 for x in mood_scores) / len(mood_scores) if mood_scores else 0

            # Chat-related metrics
            chat_sessions = user.ai_conversations.all()
            analytics.total_sessions = chat_sessions.count()
            analytics.total_messages_sent = sum(conv.message_count for conv in chat_sessions)

            # Engagement score calculation
            engagement_factors = [
                min(mood_entries.count() / 30, 1) * 30,  # Mood logging (max 30 points)
                min(analytics.total_sessions / 20, 1) * 25,  # Chat sessions (max 25 points)
                min(user.appointments.filter(status='completed').count() / 10, 1) * 20,  # Appointments (max 20 points)
                min(user.achievements.count() / 5, 1) * 15,  # Achievements (max 15 points)
                min(user.goals.filter(completed=True).count() / 3, 1) * 10,  # Goals (max 10 points)
            ]
            analytics.engagement_score = sum(engagement_factors)

            # Risk score (simplified)
            risk_factors = []
            if analytics.mood_volatility > 1.5:
                risk_factors.append(20)
            if analytics.engagement_score < 30:
                risk_factors.append(15)
            if mood_entries.filter(mood__in=['sad', 'angry']).count() / max(mood_entries.count(), 1) > 0.5:
                risk_factors.append(25)
            analytics.risk_score = min(sum(risk_factors), 100)

            # Other metrics
            analytics.last_activity = now
            analytics.chat_frequency = analytics.total_messages_sent / 30 if analytics.total_messages_sent else 0
            analytics.appointment_attendance_rate = user.appointments.filter(status='completed').count() / max(user.appointments.count(), 1)
            analytics.goal_completion_rate = user.goals.filter(completed=True).count() / max(user.goals.count(), 1)

            analytics.save()
            return analytics

        except Exception as e:
            logger.error(f"Error updating user analytics: {str(e)}")
            return None

    @staticmethod
    def analyze_mood_patterns(user):
        """Analyze mood patterns and create insights"""
        try:
            mood_entries = user.mood_entries.all().order_by('date')
            if not mood_entries:
                return None

            # Use ML model for prediction
            # predictor = MoodPredictionModel()
            # predictor.train(user)

            insights = []
            for entry in mood_entries:
                # predicted_mood = predictor.predict_mood(user, entry.date)
                predicted_mood = None  # Temporarily disabled ML prediction

                mood_mapping = {
                    'happy': 5, 'excited': 4, 'calm': 3,
                    'sad': 1, 'anxious': 2, 'angry': 1
                }
                actual_score = mood_mapping.get(entry.mood, 3)
                predicted_score = mood_mapping.get(predicted_mood, 3) if predicted_mood else 3

                # Determine trend
                if abs(actual_score - predicted_score) < 0.5:
                    trend = 'stable'
                elif actual_score > predicted_score:
                    trend = 'improving'
                else:
                    trend = 'declining'

                # Create or update mood analytics
                analytics, created = MoodAnalytics.objects.get_or_create(
                    user=user,
                    date=entry.date,
                    defaults={
                        'mood_score': actual_score,
                        'mood_trend': trend,
                        'predicted_mood': predicted_score,
                        'mood_confidence': 0.8 if predicted_mood else 0.0,
                        'insights': f"Mood was {'better' if trend == 'improving' else 'worse' if trend == 'declining' else 'as expected'} than predicted"
                    }
                )

                if not created:
                    analytics.mood_score = actual_score
                    analytics.mood_trend = trend
                    analytics.predicted_mood = predicted_score
                    analytics.mood_confidence = 0.8 if predicted_mood else 0.0
                    analytics.save()

            return insights

        except Exception as e:
            logger.error(f"Error analyzing mood patterns: {str(e)}")
            return None

    @staticmethod
    def analyze_chat_sentiment(user, session):
        """Analyze sentiment in chat messages"""
        try:
            from chat.models import AIMessage
            messages = AIMessage.objects.filter(conversation__user=user, conversation=session)

            if not messages:
                return None

            # sentiment_analyzer = SentimentAnalysisModel()
            # analysis = sentiment_analyzer.analyze_conversation(messages)
            analysis = {}  # Temporarily disabled sentiment analysis

            # Create chat analytics
            chat_analytics, created = ChatAnalytics.objects.get_or_create(
                user=user,
                session=session,
                defaults={
                    'message_count': len(messages),
                    'sentiment_score': analysis.get('average_sentiment', 0),
                    'sentiment_trend': analysis.get('dominant_sentiment', 'neutral'),
                    'keywords': analysis.get('keywords', []),
                    'topics': [],  # Would be extracted separately
                    'emotional_intensity': analysis.get('emotional_volatility', 0),
                    'crisis_indicators': [],  # Would be detected separately
                    'response_patterns': analysis
                }
            )

            if not created:
                chat_analytics.sentiment_score = analysis.get('average_sentiment', 0)
                chat_analytics.sentiment_trend = analysis.get('dominant_sentiment', 'neutral')
                chat_analytics.emotional_intensity = analysis.get('emotional_volatility', 0)
                chat_analytics.response_patterns = analysis
                chat_analytics.save()

            return chat_analytics

        except Exception as e:
            logger.error(f"Error analyzing chat sentiment: {str(e)}")
            return None

    @staticmethod
    def assess_user_risk(user):
        """Perform comprehensive risk assessment"""
        try:
            # risk_assessor = RiskAssessmentModel()
            # assessment = risk_assessor.assess_risk(user)
            assessment = {
                'risk_level': 'low',
                'risk_score': 20,
                'factors': ['Basic assessment - ML disabled'],
                'confidence': 0.5,
                'recommendations': ['Continue monitoring mood patterns']
            }  # Temporarily disabled risk assessment

            # Create risk assessment record
            risk_record = RiskAssessment.objects.create(
                user=user,
                overall_risk_level=assessment['risk_level'],
                risk_score=assessment['risk_score'],
                risk_factors=assessment['factors'],
                protective_factors=[],  # Would be determined separately
                crisis_indicators=[],  # Would be detected from chat
                notes=f"Automated assessment with {assessment['confidence']*100:.1f}% confidence",
                follow_up_required=assessment['risk_level'] in ['high', 'severe']
            )

            # Create predictive insights if risk is high
            if assessment['risk_level'] in ['high', 'severe']:
                PredictiveInsights.objects.create(
                    user=user,
                    insight_type='risk_assessment',
                    title=f"High Risk Assessment: {assessment['risk_level'].title()}",
                    description=f"Risk assessment indicates {assessment['risk_level']} risk level with score {assessment['risk_score']}",
                    confidence_score=assessment['confidence'],
                    severity_level=assessment['risk_level'],
                    recommended_actions=assessment['recommendations'],
                    data_sources=['user_analytics', 'mood_patterns', 'chat_sentiment']
                )

            return risk_record

        except Exception as e:
            logger.error(f"Error assessing user risk: {str(e)}")
            return None

    @staticmethod
    def generate_user_report(user, report_type='weekly'):
        """Generate comprehensive analytics report for user"""
        try:
            now = timezone.now()

            if report_type == 'weekly':
                period_start = now - timedelta(days=7)
                title = f"Weekly Report - {user.username}"
            elif report_type == 'monthly':
                period_start = now - timedelta(days=30)
                title = f"Monthly Report - {user.username}"
            else:
                period_start = now - timedelta(days=7)
                title = f"Custom Report - {user.username}"

            # Gather data
            mood_entries = user.mood_entries.filter(date__gte=period_start.date())
            chat_sessions = user.ai_conversations.filter(created_at__gte=period_start)
            appointments = user.appointments.filter(scheduled_date__gte=period_start)
            achievements = user.achievements.filter(unlocked_at__gte=period_start)

            # Calculate metrics
            summary_data = {
                'mood_entries_count': mood_entries.count(),
                'chat_sessions_count': chat_sessions.count(),
                'appointments_count': appointments.count(),
                'achievements_count': achievements.count(),
                'avg_mood_score': mood_entries.aggregate(avg_score=Avg('mood_score'))['avg_score'] or 0,
                'total_messages': sum(session.message_count for session in chat_sessions),
            }

            # Generate insights
            insights = []
            if summary_data['mood_entries_count'] > 0:
                insights.append(f"Logged mood {summary_data['mood_entries_count']} times this period")
            if summary_data['chat_sessions_count'] > 0:
                insights.append(f"Engaged in {summary_data['chat_sessions_count']} chat sessions")
            if summary_data['appointments_count'] > 0:
                insights.append(f"Had {summary_data['appointments_count']} appointments scheduled")

            # Generate recommendations
            recommendations = []
            if summary_data['mood_entries_count'] < 3:
                recommendations.append("Consider logging your mood more regularly for better insights")
            if summary_data['chat_sessions_count'] == 0:
                recommendations.append("Try engaging with the AI companion for additional support")

            # Create report
            report = AnalyticsReport.objects.create(
                title=title,
                report_type=report_type,
                generated_for=user,
                period_start=period_start,
                period_end=now,
                summary_data=summary_data,
                insights=insights,
                recommendations=recommendations,
                charts_data={},  # Would contain chart data for visualizations
            )

            return report

        except Exception as e:
            logger.error(f"Error generating user report: {str(e)}")
            return None

    @staticmethod
    def get_personalized_insights(user):
        """Generate personalized insights and recommendations"""
        try:
            # Analyze behavior patterns
            # behavior_analyzer = BehaviorAnalyticsModel()
            # behavior_analysis = behavior_analyzer.analyze_user_behavior(user)
            behavior_analysis = {
                'mood_patterns': {'consistency': 0.8},
                'engagement_patterns': {'login_frequency': 5},
                'chat_patterns': {'avg_sentiment': 0.1}
            }  # Temporarily disabled behavior analysis

            insights = []

            # Mood-based insights
            mood_patterns = behavior_analysis.get('mood_patterns', {})
            if mood_patterns.get('consistency', 1) < 0.5:
                insights.append({
                    'type': 'mood_stability',
                    'title': 'Mood Stability',
                    'description': 'Your mood shows significant variation. Consider stress management techniques.',
                    'severity': 'medium',
                    'actions': ['Practice mindfulness', 'Maintain consistent sleep schedule', 'Exercise regularly']
                })

            # Engagement insights
            engagement = behavior_analysis.get('engagement_patterns', {})
            if engagement.get('login_frequency', 0) < 3:
                insights.append({
                    'type': 'engagement',
                    'title': 'Increase Engagement',
                    'description': 'Regular platform usage can improve mental health tracking.',
                    'severity': 'low',
                    'actions': ['Set daily mood check-in reminders', 'Schedule regular chat sessions']
                })

            # Chat-based insights
            chat_patterns = behavior_analysis.get('chat_patterns', {})
            if chat_patterns.get('avg_sentiment', 0) < -0.2:
                insights.append({
                    'type': 'emotional_support',
                    'title': 'Emotional Support',
                    'description': 'Your recent conversations show signs of distress.',
                    'severity': 'high',
                    'actions': ['Consider professional counseling', 'Reach out to support network', 'Use crisis resources if needed']
                })

            # Create predictive insights records
            for insight in insights:
                PredictiveInsights.objects.get_or_create(
                    user=user,
                    insight_type=insight['type'],
                    title=insight['title'],
                    defaults={
                        'description': insight['description'],
                        'confidence_score': 0.7,
                        'severity_level': insight['severity'],
                        'recommended_actions': insight['actions'],
                        'data_sources': ['behavior_analysis', 'mood_patterns', 'chat_sentiment']
                    }
                )

            return insights

        except Exception as e:
            logger.error(f"Error generating personalized insights: {str(e)}")
            return []


class CounselorAnalyticsService:
    """Service for counselor-specific analytics and dashboards"""

    @staticmethod
    def get_counselor_dashboard_data(counselor):
        """Get comprehensive dashboard data for counselors"""
        try:
            # Get counselor's clients
            clients = User.objects.filter(
                Q(appointments__counselor=counselor) |
                Q(client_appointments__counselor=counselor)
            ).distinct()

            dashboard_data = {
                'total_clients': clients.count(),
                'active_clients': clients.filter(
                    appointments__status__in=['scheduled', 'confirmed'],
                    appointments__scheduled_date__gte=timezone.now()
                ).distinct().count(),
                'upcoming_appointments': counselor.appointments.filter(
                    scheduled_date__gte=timezone.now(),
                    status__in=['scheduled', 'confirmed']
                ).count(),
                'completed_sessions': counselor.appointments.filter(
                    status='completed'
                ).count(),
                'client_risk_summary': {},
                'recent_activity': []
            }

            # Client risk summary
            high_risk_clients = 0
            medium_risk_clients = 0

            for client in clients:
                analytics = UserAnalytics.objects.filter(user=client).first()
                if analytics and analytics.risk_score >= 70:
                    high_risk_clients += 1
                elif analytics and analytics.risk_score >= 40:
                    medium_risk_clients += 1

            dashboard_data['client_risk_summary'] = {
                'high_risk': high_risk_clients,
                'medium_risk': medium_risk_clients,
                'low_risk': clients.count() - high_risk_clients - medium_risk_clients
            }

            # Recent activity (last 7 days)
            recent_appointments = counselor.appointments.filter(
                scheduled_date__gte=timezone.now() - timedelta(days=7)
            ).order_by('-scheduled_date')[:5]

            dashboard_data['recent_activity'] = [
                {
                    'type': 'appointment',
                    'description': f"Appointment with {apt.user.username}",
                    'date': apt.scheduled_date,
                    'status': apt.status
                } for apt in recent_appointments
            ]

            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting counselor dashboard data: {str(e)}")
            return {}

    @staticmethod
    def generate_counselor_report(counselor, period_days=30):
        """Generate comprehensive report for counselor performance"""
        try:
            start_date = timezone.now() - timedelta(days=period_days)

            # Gather counselor metrics
            appointments = counselor.appointments.filter(scheduled_date__gte=start_date)
            completed_sessions = appointments.filter(status='completed')
            client_feedback = counselor.received_feedback.filter(created_at__gte=start_date)

            report_data = {
                'period_days': period_days,
                'total_appointments': appointments.count(),
                'completed_sessions': completed_sessions.count(),
                'completion_rate': completed_sessions.count() / max(appointments.count(), 1),
                'unique_clients': appointments.values('user').distinct().count(),
                'avg_session_duration': completed_sessions.aggregate(avg_duration=Avg('duration_minutes'))['avg_duration'] or 0,
                'client_satisfaction': client_feedback.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0,
                'feedback_count': client_feedback.count(),
            }

            # Create analytics report
            report = AnalyticsReport.objects.create(
                title=f"Counselor Report - {counselor.username} ({period_days} days)",
                report_type='custom',
                generated_for=counselor,
                period_start=start_date,
                period_end=timezone.now(),
                summary_data=report_data,
                insights=[
                    f"Completed {report_data['completed_sessions']} out of {report_data['total_appointments']} scheduled sessions",
                    f"Served {report_data['unique_clients']} unique clients",
                    f"Average client satisfaction: {report_data['client_satisfaction']:.1f}/5" if report_data['client_satisfaction'] > 0 else "No feedback received"
                ],
                recommendations=[
                    "Focus on completing scheduled appointments" if report_data['completion_rate'] < 0.8 else "Good appointment completion rate",
                    "Request feedback from clients" if report_data['feedback_count'] == 0 else "Continue gathering client feedback"
                ]
            )

            return report

        except Exception as e:
            logger.error(f"Error generating counselor report: {str(e)}")
            return None