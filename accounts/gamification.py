from .models import Achievement, Streak, MoodEntry
from chat.models import Message, Appointment, Goal, Feedback, ProgressEntry, Notification
from django.utils import timezone
from django.db.models import Count

def award_achievement(user, achievement_type, description, icon='🏆'):
    """Award an achievement to a user if they don't already have it"""
    if not Achievement.objects.filter(user=user, achievement_type=achievement_type).exists():
        achievement = Achievement.objects.create(
            user=user,
            achievement_type=achievement_type,
            description=description,
            icon=icon
        )

        # Create notification for the achievement
        achievement_names = {
            'first_mood_log': 'First Mood Log',
            'consistent_logger': 'Consistent Logger',
            'mental_health_champion': 'Mental Health Champion',
            'chat_starter': 'Chat Starter',
            'helper': 'Helper',
            'community_builder': 'Community Builder',
            'goal_setter': 'Goal Setter',
            'progress_tracker': 'Progress Tracker',
            'appointment_booker': 'Appointment Booker',
            'feedback_giver': 'Feedback Giver',
        }

        achievement_name = achievement_names.get(achievement_type, 'New Achievement')
        Notification.objects.create(
            user=user,
            title=f'Achievement Unlocked: {achievement_name}',
            message=f'Congratulations! {description}',
            notification_type='achievement',
            related_id=achievement.id
        )

        return True
    return False

def update_streak(user, streak_type, activity_date=None):
    """Update or create a streak for a user"""
    if activity_date is None:
        activity_date = timezone.now().date()

    streak, created = Streak.objects.get_or_create(
        user=user,
        streak_type=streak_type,
        defaults={'current_streak': 0, 'longest_streak': 0}
    )

    streak.update_streak(activity_date)
    return streak

def check_mood_logging_achievements(user):
    """Check and award achievements related to mood logging"""
    mood_count = MoodEntry.objects.filter(user=user).count()

    # First mood log
    if mood_count >= 1:
        award_achievement(
            user,
            'first_mood_log',
            'Logged your first mood entry - great start on your mental health journey!',
            '📝'
        )

    # Consistent logger - 7 consecutive days
    streak = update_streak(user, 'mood_logging')
    if streak.current_streak >= 7:
        award_achievement(
            user,
            'consistent_logger',
            'Logged mood for 7 consecutive days - building healthy habits!',
            '📅'
        )

    # Long-term logger - 30 total entries
    if mood_count >= 30:
        award_achievement(
            user,
            'mental_health_champion',
            'Logged mood 30 times - committed to mental wellness!',
            '🌟'
        )

def check_chat_achievements(user):
    """Check and award achievements related to chatting"""
    message_count = Message.objects.filter(sender=user).count()

    # Chat starter
    if message_count >= 1:
        award_achievement(
            user,
            'chat_starter',
            'Started your first conversation - connecting with others!',
            '💬'
        )

    # Helper - sent 10 messages
    if message_count >= 10:
        award_achievement(
            user,
            'helper',
            'Sent 10 messages - actively participating in community support!',
            '🤝'
        )

    # Community builder - sent 50 messages
    if message_count >= 50:
        award_achievement(
            user,
            'community_builder',
            'Sent 50 messages - building a supportive community!',
            '🌍'
        )

    # Update chat streak
    if message_count > 0:
        # Get the date of the most recent message
        last_message = Message.objects.filter(sender=user).order_by('-timestamp').first()
        if last_message:
            update_streak(user, 'chatting', last_message.timestamp.date())

def check_goal_achievements(user):
    """Check and award achievements related to goals"""
    goal_count = Goal.objects.filter(client=user).count()
    completed_goals = Goal.objects.filter(client=user, completed=True).count()

    # Goal setter
    if goal_count >= 1:
        award_achievement(
            user,
            'goal_setter',
            'Set your first goal - taking steps toward positive change!',
            '🎯'
        )

    # Progress tracker - completed 3 goals
    if completed_goals >= 3:
        award_achievement(
            user,
            'progress_tracker',
            'Completed 3 goals - making real progress!',
            '📈'
        )

def check_appointment_achievements(user):
    """Check and award achievements related to appointments"""
    appointment_count = Appointment.objects.filter(client=user).count()
    completed_appointments = Appointment.objects.filter(client=user, status='completed').count()

    # Appointment booker
    if appointment_count >= 1:
        award_achievement(
            user,
            'appointment_booker',
            'Booked your first counseling appointment - seeking professional support!',
            '📅'
        )

    # Regular attendee - 5 completed appointments
    if completed_appointments >= 5:
        award_achievement(
            user,
            'mental_health_champion',
            'Completed 5 counseling sessions - committed to your mental health!',
            '🏆'
        )

def check_feedback_achievements(user):
    """Check and award achievements related to feedback"""
    feedback_count = Feedback.objects.filter(client=user).count()

    # Feedback giver
    if feedback_count >= 1:
        award_achievement(
            user,
            'feedback_giver',
            'Provided feedback after a session - helping improve our services!',
            '⭐'
        )

def check_all_achievements(user):
    """Check all achievements for a user"""
    check_mood_logging_achievements(user)
    check_chat_achievements(user)
    check_goal_achievements(user)
    check_appointment_achievements(user)
    check_feedback_achievements(user)

def get_user_gamification_data(user):
    """Get all gamification data for a user"""
    achievements = Achievement.objects.filter(user=user).order_by('-unlocked_at')
    streaks = Streak.objects.filter(user=user)

    return {
        'achievements': achievements,
        'streaks': streaks,
        'total_achievements': achievements.count(),
        'recent_achievements': achievements[:3],  # Last 3 achievements
    }