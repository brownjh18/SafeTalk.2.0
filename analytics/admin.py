from django.contrib import admin
from .models import (
    UserAnalytics, MoodAnalytics, BehaviorMetrics,
    PredictiveInsights, RiskAssessment, AnalyticsReport, MLModelMetrics
)


@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'engagement_score', 'risk_score', 'last_activity', 'updated_at']
    list_filter = ['engagement_score', 'risk_score', 'last_activity']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MoodAnalytics)
class MoodAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'analysis_date', 'mood_score', 'mood_trend', 'predicted_mood']
    list_filter = ['mood_trend', 'analysis_date']
    search_fields = ['user__username']
    readonly_fields = ['created_at']


# @admin.register(ChatAnalytics)
# class ChatAnalyticsAdmin(admin.ModelAdmin):
#     list_display = ['user', 'session', 'sentiment_score', 'sentiment_trend', 'message_count']
#     list_filter = ['sentiment_trend', 'created_at']
#     search_fields = ['user__username', 'session__title']
#     readonly_fields = ['created_at']


@admin.register(BehaviorMetrics)
class BehaviorMetricsAdmin(admin.ModelAdmin):
    list_display = ['user', 'metric_type', 'metric_value', 'period_start', 'period_end']
    list_filter = ['metric_type', 'period_start', 'period_end']
    search_fields = ['user__username']
    readonly_fields = ['created_at']


@admin.register(PredictiveInsights)
class PredictiveInsightsAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'title', 'confidence_score', 'severity_level', 'is_active']
    list_filter = ['insight_type', 'severity_level', 'is_active', 'created_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at']


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'overall_risk_level', 'risk_score', 'assessment_date', 'follow_up_required']
    list_filter = ['overall_risk_level', 'follow_up_required', 'assessment_date']
    search_fields = ['user__username']
    readonly_fields = ['created_at']


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'generated_for', 'period_start', 'period_end', 'created_at']
    list_filter = ['report_type', 'created_at']
    search_fields = ['title', 'generated_for__username']
    readonly_fields = ['created_at']


@admin.register(MLModelMetrics)
class MLModelMetricsAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'model_version', 'metric_type', 'metric_value', 'is_active']
    list_filter = ['model_name', 'metric_type', 'is_active']
    search_fields = ['model_name', 'model_version']
    readonly_fields = ['created_at']