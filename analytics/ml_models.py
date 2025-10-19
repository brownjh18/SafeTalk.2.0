import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
from sklearn.pipeline import Pipeline
import joblib
import os
from datetime import datetime, timedelta
from django.conf import settings
from accounts.models import MoodEntry
from .models import UserAnalytics, MoodAnalytics
import logging

logger = logging.getLogger(__name__)


class MoodPredictionModel:
    """Machine learning model for predicting user mood based on historical data"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = os.path.join(settings.BASE_DIR, 'analytics', 'models', 'mood_predictor.pkl')

    def prepare_data(self, user):
        """Prepare historical mood data for training"""
        # Get mood entries for the user
        mood_entries = MoodEntry.objects.filter(user=user).order_by('date')

        if len(mood_entries) < 7:  # Need at least a week of data
            return None

        data = []
        for i, entry in enumerate(mood_entries):
            # Convert mood to numerical value
            mood_mapping = {
                'happy': 5, 'excited': 4, 'calm': 3,
                'sad': 1, 'anxious': 2, 'angry': 1
            }
            mood_score = mood_mapping.get(entry.mood, 3)

            # Calculate features
            features = {
                'mood_score': mood_score,
                'day_of_week': entry.date.weekday(),
                'day_of_month': entry.date.day,
                'month': entry.date.month,
                'has_note': 1 if entry.note else 0,
                'note_length': len(entry.note) if entry.note else 0,
            }

            # Add previous mood scores (rolling window of 3 days)
            for j in range(1, 4):
                if i >= j:
                    prev_mood = mood_entries[i-j]
                    prev_score = mood_mapping.get(prev_mood.mood, 3)
                    features[f'prev_mood_{j}'] = prev_score
                else:
                    features[f'prev_mood_{j}'] = 3  # Default neutral

            # Add trend features
            if i >= 3:
                recent_moods = [mood_mapping.get(mood_entries[k].mood, 3) for k in range(i-2, i+1)]
                features['mood_trend'] = np.polyfit(range(3), recent_moods, 1)[0]  # Linear trend
                features['mood_volatility'] = np.std(recent_moods)
            else:
                features['mood_trend'] = 0
                features['mood_volatility'] = 0

            data.append(features)

        return pd.DataFrame(data)

    def train(self, user):
        """Train the mood prediction model for a specific user"""
        try:
            df = self.prepare_data(user)
            if df is None or len(df) < 10:
                logger.warning(f"Insufficient data for user {user.id}")
                return False

            # Prepare features and target
            feature_cols = [col for col in df.columns if col != 'mood_score']
            X = df[feature_cols]
            y = df['mood_score']

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Create and train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )

            self.model.fit(X_train, y_train)

            # Evaluate
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            logger.info(f"Model trained for user {user.id}, MSE: {mse}")

            self.is_trained = True

            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)

            return True

        except Exception as e:
            logger.error(f"Error training mood prediction model: {str(e)}")
            return False

    def predict_mood(self, user, prediction_date=None):
        """Predict mood for a given date"""
        if not self.is_trained:
            # Try to load existing model
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
            else:
                return None

        if prediction_date is None:
            prediction_date = datetime.now().date()

        try:
            # Get recent mood data
            recent_entries = MoodEntry.objects.filter(
                user=user,
                date__gte=prediction_date - timedelta(days=7)
            ).order_by('-date')[:7]

            if len(recent_entries) < 3:
                return None

            # Prepare features for prediction
            features = {
                'day_of_week': prediction_date.weekday(),
                'day_of_month': prediction_date.day,
                'month': prediction_date.month,
                'has_note': 0,  # Assume no note for prediction
                'note_length': 0,
            }

            # Add previous mood scores
            for j in range(1, 4):
                if len(recent_entries) > j-1:
                    prev_entry = recent_entries[j-1]
                    mood_mapping = {
                        'happy': 5, 'excited': 4, 'calm': 3,
                        'sad': 1, 'anxious': 2, 'angry': 1
                    }
                    features[f'prev_mood_{j}'] = mood_mapping.get(prev_entry.mood, 3)
                else:
                    features[f'prev_mood_{j}'] = 3

            # Calculate trend
            recent_scores = []
            for entry in recent_entries[:3]:
                mood_mapping = {
                    'happy': 5, 'excited': 4, 'calm': 3,
                    'sad': 1, 'anxious': 2, 'angry': 1
                }
                recent_scores.append(mood_mapping.get(entry.mood, 3))

            if len(recent_scores) >= 3:
                features['mood_trend'] = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
                features['mood_volatility'] = np.std(recent_scores)
            else:
                features['mood_trend'] = 0
                features['mood_volatility'] = 0

            # Make prediction
            X_pred = pd.DataFrame([features])
            prediction = self.model.predict(X_pred)[0]

            # Convert back to mood category
            mood_ranges = {
                (4.5, 6): 'happy',
                (3.5, 4.5): 'excited',
                (2.5, 3.5): 'calm',
                (1.5, 2.5): 'anxious',
                (0, 1.5): 'sad'
            }

            for (min_val, max_val), mood in mood_ranges.items():
                if min_val <= prediction < max_val:
                    return mood

            return 'calm'  # Default

        except Exception as e:
            logger.error(f"Error predicting mood: {str(e)}")
            return None


class SentimentAnalysisModel:
    """Model for analyzing sentiment in chat messages"""

    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.is_trained = False
        self.model_path = os.path.join(settings.BASE_DIR, 'analytics', 'models', 'sentiment_analyzer.pkl')

    def analyze_sentiment(self, text):
        """Analyze sentiment of a text message"""
        try:
            from textblob import TextBlob

            # Use TextBlob for sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1

            # Classify sentiment
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            # Extract keywords
            keywords = []
            for word, tag in blob.tags:
                if tag in ['JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
                    keywords.append(word.lower())

            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'confidence': abs(polarity),
                'keywords': keywords[:10],  # Top 10 keywords
                'intensity': abs(polarity) * subjectivity
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'confidence': 0.0,
                'keywords': [],
                'intensity': 0.0
            }

    def analyze_conversation(self, messages):
        """Analyze sentiment patterns in a conversation"""
        if not messages:
            return {}

        sentiments = []
        for message in messages:
            analysis = self.analyze_sentiment(message.content)
            sentiments.append(analysis)

        # Calculate aggregate metrics
        avg_polarity = np.mean([s['polarity'] for s in sentiments])
        avg_subjectivity = np.mean([s['subjectivity'] for s in sentiments])
        sentiment_distribution = {
            'positive': sum(1 for s in sentiments if s['sentiment'] == 'positive'),
            'neutral': sum(1 for s in sentiments if s['sentiment'] == 'neutral'),
            'negative': sum(1 for s in sentiments if s['sentiment'] == 'negative'),
        }

        # Calculate trend
        polarities = [s['polarity'] for s in sentiments]
        if len(polarities) > 1:
            trend = np.polyfit(range(len(polarities)), polarities, 1)[0]
        else:
            trend = 0

        # Detect emotional intensity changes
        intensities = [s['intensity'] for s in sentiments]
        volatility = np.std(intensities) if len(intensities) > 1 else 0

        return {
            'average_sentiment': avg_polarity,
            'sentiment_trend': trend,
            'emotional_volatility': volatility,
            'sentiment_distribution': sentiment_distribution,
            'dominant_sentiment': max(sentiment_distribution, key=sentiment_distribution.get),
            'conversation_length': len(messages),
            'positive_ratio': sentiment_distribution['positive'] / len(sentiments),
            'negative_ratio': sentiment_distribution['negative'] / len(sentiments),
        }


class RiskAssessmentModel:
    """Model for assessing mental health risk based on user behavior"""

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = os.path.join(settings.BASE_DIR, 'analytics', 'models', 'risk_assessor.pkl')

    def prepare_features(self, user):
        """Prepare features for risk assessment"""
        try:
            # Get user analytics
            analytics = UserAnalytics.objects.filter(user=user).first()
            if not analytics:
                return None

            # Get recent mood data
            recent_moods = MoodEntry.objects.filter(
                user=user,
                date__gte=datetime.now().date() - timedelta(days=30)
            )

            # Get chat analytics
            chat_analytics = ChatAnalytics.objects.filter(
                user=user,
                created_at__gte=datetime.now() - timedelta(days=30)
            )

            # Calculate features
            features = {
                'engagement_score': analytics.engagement_score,
                'risk_score': analytics.risk_score,
                'mood_volatility': analytics.mood_volatility,
                'chat_frequency': analytics.chat_frequency,
                'appointment_attendance': analytics.appointment_attendance_rate,
                'goal_completion': analytics.goal_completion_rate,
                'days_since_last_activity': (datetime.now().date() - analytics.last_activity.date()).days if analytics.last_activity else 30,
            }

            # Mood-based features
            if recent_moods:
                mood_scores = []
                for mood in recent_moods:
                    mood_mapping = {
                        'happy': 5, 'excited': 4, 'calm': 3,
                        'sad': 1, 'anxious': 2, 'angry': 1
                    }
                    mood_scores.append(mood_mapping.get(mood.mood, 3))

                features['avg_mood_last_30_days'] = np.mean(mood_scores)
                features['mood_std_last_30_days'] = np.std(mood_scores)
                features['negative_mood_ratio'] = sum(1 for score in mood_scores if score <= 2) / len(mood_scores)
            else:
                features['avg_mood_last_30_days'] = 3
                features['mood_std_last_30_days'] = 0
                features['negative_mood_ratio'] = 0

            # Chat-based features
            if chat_analytics:
                avg_sentiment = np.mean([ca.sentiment_score for ca in chat_analytics])
                features['avg_chat_sentiment'] = avg_sentiment
                features['negative_chat_ratio'] = sum(1 for ca in chat_analytics if ca.sentiment_score < -0.1) / len(chat_analytics)
                features['crisis_keywords_count'] = sum(len(ca.crisis_indicators) for ca in chat_analytics)
            else:
                features['avg_chat_sentiment'] = 0
                features['negative_chat_ratio'] = 0
                features['crisis_keywords_count'] = 0

            return features

        except Exception as e:
            logger.error(f"Error preparing risk assessment features: {str(e)}")
            return None

    def assess_risk(self, user):
        """Assess mental health risk for a user"""
        try:
            features = self.prepare_features(user)
            if not features:
                return {
                    'risk_level': 'unknown',
                    'risk_score': 50,
                    'confidence': 0.0,
                    'factors': [],
                    'recommendations': ['Insufficient data for assessment']
                }

            # Simple rule-based risk assessment (can be enhanced with ML)
            risk_score = 0
            factors = []
            recommendations = []

            # Engagement factors
            if features['engagement_score'] < 30:
                risk_score += 20
                factors.append('Low engagement')
                recommendations.append('Increase user engagement through personalized content')

            if features['days_since_last_activity'] > 14:
                risk_score += 15
                factors.append('Inactive for extended period')
                recommendations.append('Reach out to check user well-being')

            # Mood factors
            if features['avg_mood_last_30_days'] < 2.5:
                risk_score += 25
                factors.append('Consistently low mood')
                recommendations.append('Consider professional counseling support')

            if features['mood_volatility'] > 1.5:
                risk_score += 15
                factors.append('High mood volatility')
                recommendations.append('Monitor mood patterns closely')

            if features['negative_mood_ratio'] > 0.6:
                risk_score += 20
                factors.append('High proportion of negative moods')
                recommendations.append('Immediate intervention may be needed')

            # Chat factors
            if features['avg_chat_sentiment'] < -0.3:
                risk_score += 15
                factors.append('Negative chat sentiment')
                recommendations.append('Review chat content for concerning themes')

            if features['crisis_keywords_count'] > 5:
                risk_score += 25
                factors.append('Multiple crisis indicators')
                recommendations.append('Urgent professional intervention required')

            # Determine risk level
            if risk_score >= 70:
                risk_level = 'severe'
            elif risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 30:
                risk_level = 'moderate'
            elif risk_score >= 15:
                risk_level = 'low'
            else:
                risk_level = 'minimal'

            return {
                'risk_level': risk_level,
                'risk_score': min(risk_score, 100),
                'confidence': 0.8,  # Rule-based confidence
                'factors': factors,
                'recommendations': recommendations
            }

        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return {
                'risk_level': 'unknown',
                'risk_score': 50,
                'confidence': 0.0,
                'factors': ['Assessment error'],
                'recommendations': ['Manual review required']
            }


class BehaviorAnalyticsModel:
    """Model for analyzing user behavior patterns"""

    def __init__(self):
        self.is_trained = False

    def analyze_user_behavior(self, user, days=30):
        """Analyze comprehensive user behavior patterns"""
        try:
            start_date = datetime.now().date() - timedelta(days=days)

            # Get various data points
            mood_entries = MoodEntry.objects.filter(user=user, date__gte=start_date)
            chat_sessions = ChatAnalytics.objects.filter(user=user, created_at__gte=start_date)
            appointments = user.appointments.filter(scheduled_date__gte=start_date)

            analysis = {
                'period_days': days,
                'mood_patterns': self._analyze_mood_patterns(mood_entries),
                'engagement_patterns': self._analyze_engagement_patterns(user, start_date),
                'chat_patterns': self._analyze_chat_patterns(chat_sessions),
                'appointment_patterns': self._analyze_appointment_patterns(appointments),
                'overall_insights': []
            }

            # Generate insights
            analysis['overall_insights'] = self._generate_behavior_insights(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            return {}

    def _analyze_mood_patterns(self, mood_entries):
        """Analyze mood entry patterns"""
        if not mood_entries:
            return {'entries_count': 0, 'consistency': 0, 'avg_mood': 3}

        mood_scores = []
        for entry in mood_entries:
            mood_mapping = {
                'happy': 5, 'excited': 4, 'calm': 3,
                'sad': 1, 'anxious': 2, 'angry': 1
            }
            mood_scores.append(mood_mapping.get(entry.mood, 3))

        # Calculate consistency (inverse of volatility)
        consistency = 1 / (1 + np.std(mood_scores)) if len(mood_scores) > 1 else 1

        return {
            'entries_count': len(mood_entries),
            'consistency': consistency,
            'avg_mood': np.mean(mood_scores),
            'mood_volatility': np.std(mood_scores) if len(mood_scores) > 1 else 0,
            'most_common_mood': max(set(entry.mood for entry in mood_entries),
                                   key=lambda x: sum(1 for e in mood_entries if e.mood == x))
        }

    def _analyze_engagement_patterns(self, user, start_date):
        """Analyze user engagement patterns"""
        # This would analyze login patterns, feature usage, etc.
        # For now, return basic structure
        return {
            'login_frequency': 0,  # Would calculate from session data
            'feature_usage': {},
            'peak_activity_hours': [],
            'engagement_trend': 'stable'
        }

    def _analyze_chat_patterns(self, chat_sessions):
        """Analyze chat behavior patterns"""
        if not chat_sessions:
            return {'sessions_count': 0, 'avg_sentiment': 0, 'communication_style': 'minimal'}

        return {
            'sessions_count': len(chat_sessions),
            'avg_sentiment': np.mean([s.sentiment_score for s in chat_sessions]),
            'communication_style': 'active' if len(chat_sessions) > 10 else 'moderate',
            'sentiment_trend': 'stable'  # Would calculate trend
        }

    def _analyze_appointment_patterns(self, appointments):
        """Analyze appointment attendance patterns"""
        if not appointments:
            return {'total_appointments': 0, 'attendance_rate': 0}

        completed = sum(1 for apt in appointments if apt.status == 'completed')
        attendance_rate = completed / len(appointments) if appointments else 0

        return {
            'total_appointments': len(appointments),
            'attendance_rate': attendance_rate,
            'upcoming_count': sum(1 for apt in appointments if apt.status == 'scheduled'),
            'completion_rate': attendance_rate
        }

    def _generate_behavior_insights(self, analysis):
        """Generate actionable insights from behavior analysis"""
        insights = []

        mood_data = analysis.get('mood_patterns', {})
        if mood_data.get('entries_count', 0) > 0:
            if mood_data.get('consistency', 0) < 0.5:
                insights.append("Mood tracking shows high volatility - consider stress management techniques")
            if mood_data.get('avg_mood', 3) < 2.5:
                insights.append("Consistently low mood scores suggest need for additional support")

        chat_data = analysis.get('chat_patterns', {})
        if chat_data.get('sessions_count', 0) > 0:
            if chat_data.get('avg_sentiment', 0) < -0.2:
                insights.append("Chat sentiment analysis indicates persistent negative emotions")

        appointment_data = analysis.get('appointment_patterns', {})
        if appointment_data.get('attendance_rate', 1) < 0.7:
            insights.append("Low appointment attendance rate - follow up may be needed")

        return insights if insights else ["User behavior appears within normal ranges"]