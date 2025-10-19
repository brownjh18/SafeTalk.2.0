from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()

class UserAnalytics(models.Model):
    """Model for storing user behavior analytics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    mood_entries_count = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    total_messages_sent = models.IntegerField(default=0)
    total_messages_received = models.IntegerField(default=0)
    average_session_duration = models.DurationField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    engagement_score = models.FloatField(default=0.0)  # 0-100 scale
    risk_score = models.FloatField(default=0.0)  # 0-100 scale
    mood_volatility = models.FloatField(default=0.0)  # Standard deviation of mood scores
    chat_frequency = models.FloatField(default=0.0)  # Messages per day
    appointment_attendance_rate = models.FloatField(default=0.0)  # 0-1 scale
    goal_completion_rate = models.FloatField(default=0.0)  # 0-1 scale
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['risk_score']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"Analytics for {self.user.username}"

class MoodAnalytics(models.Model):
    """Model for mood pattern analysis"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_analytics')
    dominant_mood = models.CharField(max_length=20, default='neutral')
    analysis_date = models.DateField(default=timezone.now)
    mood_score = models.FloatField()  # Normalized mood score (0-10)
    mood_trend = models.CharField(max_length=20, choices=[
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
        ('volatile', 'Volatile'),
    ], default='stable')
    predicted_mood = models.FloatField(null=True, blank=True)
    mood_confidence = models.FloatField(default=0.0)  # 0-1 scale
    factors = models.JSONField(default=dict)  # Contributing factors
    insights = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'analysis_date')
        ordering = ['-analysis_date']
        indexes = [
            models.Index(fields=['user', '-analysis_date']),
            models.Index(fields=['mood_trend']),
            models.Index(fields=['predicted_mood']),
        ]

    def __str__(self):
        return f"Mood analytics for {self.user.username} on {self.analysis_date}"

# class ChatAnalytics(models.Model):
#     """Model for chat message analytics"""
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_analytics')
#     conversation = models.ForeignKey('messaging.Conversation', on_delete=models.CASCADE, related_name='analytics', null=True, blank=True)
#     total_messages_sent = models.IntegerField(default=0)
#     analysis_date = models.DateField(default=timezone.now)
#     message_count = models.IntegerField(default=0)
#     sentiment_score = models.FloatField(default=0.0)  # -1 to 1 scale
#     sentiment_trend = models.CharField(max_length=20, choices=[
#         ('positive', 'Positive'),
#         ('neutral', 'Neutral'),
#         ('negative', 'Negative'),
#     ], default='neutral')
#     keywords = models.JSONField(default=list)
#     topics = models.JSONField(default=list)
#     emotional_intensity = models.FloatField(default=0.0)  # 0-1 scale
#     crisis_indicators = models.JSONField(default=list)
#     response_patterns = models.JSONField(default=dict)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'conversation', 'analysis_date')
#         indexes = [
#             models.Index(fields=['user', 'conversation']),
#             models.Index(fields=['sentiment_score']),
#             models.Index(fields=['sentiment_trend']),
#         ]

#     def __str__(self):
#         return f"Chat analytics for {self.user.username} in conversation {self.conversation.id if self.conversation else 'N/A'}"

class BehaviorMetrics(models.Model):
    """Model for detailed behavior metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_metrics')
    metric_type = models.CharField(max_length=50, choices=[
        ('login_frequency', 'Login Frequency'),
        ('session_duration', 'Session Duration'),
        ('feature_usage', 'Feature Usage'),
        ('social_interaction', 'Social Interaction'),
        ('goal_setting', 'Goal Setting'),
        ('appointment_booking', 'Appointment Booking'),
        ('mood_logging', 'Mood Logging'),
        ('chat_engagement', 'Chat Engagement'),
    ])
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20, default='count')  # count, percentage, hours, etc.
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    context = models.JSONField(default=dict)  # Additional context data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'metric_type', '-period_end']),
            models.Index(fields=['metric_type', 'period_start', 'period_end']),
        ]

    def __str__(self):
        return f"{self.metric_type} for {self.user.username}: {self.metric_value}"

class PredictiveInsights(models.Model):
    """Model for predictive analytics insights"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictive_insights')
    insight_type = models.CharField(max_length=50, choices=[
        ('mood_prediction', 'Mood Prediction'),
        ('risk_assessment', 'Risk Assessment'),
        ('engagement_forecast', 'Engagement Forecast'),
        ('trend_analysis', 'Trend Analysis'),
        ('intervention_recommendation', 'Intervention Recommendation'),
    ])
    title = models.CharField(max_length=200)
    description = models.TextField()
    confidence_score = models.FloatField(default=0.0)  # 0-1 scale
    severity_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='low')
    predicted_outcome = models.TextField(blank=True)
    recommended_actions = models.JSONField(default=list)
    data_sources = models.JSONField(default=list)  # Sources used for prediction
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['insight_type']),
            models.Index(fields=['severity_level']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.insight_type} for {self.user.username}: {self.title}"

class RiskAssessment(models.Model):
    """Model for mental health risk assessment"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risk_assessments')
    overall_risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('severe', 'Severe'),
    ], default='low')
    risk_score = models.FloatField(default=0.0)  # 0-100 scale
    risk_factors = models.JSONField(default=list)
    protective_factors = models.JSONField(default=list)
    crisis_indicators = models.JSONField(default=list)
    assessment_date = models.DateTimeField(default=timezone.now)
    next_assessment_due = models.DateTimeField(null=True, blank=True)
    assessor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_assessments')
    notes = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessment_date']
        indexes = [
            models.Index(fields=['user', '-assessment_date']),
            models.Index(fields=['overall_risk_level']),
            models.Index(fields=['follow_up_required']),
        ]

    def __str__(self):
        return f"Risk assessment for {self.user.username}: {self.overall_risk_level}"

class AnalyticsReport(models.Model):
    """Model for generated analytics reports"""
    REPORT_TYPES = [
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('quarterly', 'Quarterly Report'),
        ('custom', 'Custom Report'),
    ]

    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='weekly')
    generated_for = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_reports')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    summary_data = models.JSONField(default=dict)
    insights = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    charts_data = models.JSONField(default=dict)  # Data for visualizations
    file_path = models.FileField(upload_to='analytics_reports/%Y/%m/%d/', null=True, blank=True)
    is_shared = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, related_name='shared_reports', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['generated_for', '-created_at']),
            models.Index(fields=['report_type']),
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return f"{self.report_type} report for {self.generated_for.username}: {self.title}"

class MLModelMetrics(models.Model):
    """Model for tracking ML model performance"""
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    metric_type = models.CharField(max_length=50, choices=[
        ('accuracy', 'Accuracy'),
        ('precision', 'Precision'),
        ('recall', 'Recall'),
        ('f1_score', 'F1 Score'),
        ('auc', 'AUC'),
        ('mse', 'Mean Squared Error'),
        ('mae', 'Mean Absolute Error'),
    ])
    metric_value = models.FloatField()
    dataset_size = models.IntegerField()
    training_date = models.DateTimeField()
    validation_date = models.DateTimeField(null=True, blank=True)
    model_parameters = models.JSONField(default=dict)
    performance_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name', 'model_version']),
            models.Index(fields=['metric_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.model_name} v{self.model_version} - {self.metric_type}: {self.metric_value}"