from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('counselor', 'Counselor'),
        ('client', 'Client'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')

    # Notification preferences
    notifications_enabled = models.BooleanField(default=True)
    notification_message = models.BooleanField(default=True)
    notification_appointment = models.BooleanField(default=True)
    notification_feedback = models.BooleanField(default=True)
    notification_achievement = models.BooleanField(default=True)
    notification_system = models.BooleanField(default=True)
    notification_sound = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ('1', '😢 Very Sad'),
        ('2', '😕 Sad'),
        ('3', '😐 Neutral'),
        ('4', '😊 Happy'),
        ('5', '😄 Very Happy'),
    ]

    ENERGY_CHOICES = [
        ('1', '😴 Very Low'),
        ('2', '😪 Low'),
        ('3', '😐 Moderate'),
        ('4', '⚡ High'),
        ('5', '🔥 Very High'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_entries')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    mood_score = models.IntegerField(default=5)  # 1-10 scale for analytics
    intensity = models.IntegerField(default=5)  # 1-10 intensity scale
    energy_level = models.CharField(max_length=20, choices=ENERGY_CHOICES, blank=True, null=True)
    activities = models.JSONField(default=list, blank=True)  # List of activities
    triggers = models.JSONField(default=list, blank=True)  # List of mood triggers
    gratitude = models.TextField(blank=True, null=True)  # Gratitude notes
    note = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['date']),
            models.Index(fields=['user', 'date']),  # For efficient lookups
            models.Index(fields=['-date']),  # For recent entries
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_mood_display()} on {self.date}"

class Block(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_made')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocks_received')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')
        indexes = [
            models.Index(fields=['blocker']),
            models.Index(fields=['blocked']),
        ]

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

class Achievement(models.Model):
    ACHIEVEMENT_CHOICES = [
        ('first_mood_log', 'First Mood Log'),
        ('consistent_logger', 'Consistent Logger'),
        ('chat_starter', 'Chat Starter'),
        ('helper', 'Helper'),
        ('goal_setter', 'Goal Setter'),
        ('progress_tracker', 'Progress Tracker'),
        ('appointment_booker', 'Appointment Booker'),
        ('feedback_giver', 'Feedback Giver'),
        ('community_builder', 'Community Builder'),
        ('mental_health_champion', 'Mental Health Champion'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_CHOICES)
    description = models.TextField()
    unlocked_at = models.DateTimeField(auto_now_add=True)
    icon = models.CharField(max_length=10, default='🏆')  # Emoji icon

    class Meta:
        unique_together = ('user', 'achievement_type')
        ordering = ['-unlocked_at']
        indexes = [
            models.Index(fields=['user', '-unlocked_at']),
            models.Index(fields=['achievement_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_achievement_type_display()}"

class Streak(models.Model):
    STREAK_CHOICES = [
        ('mood_logging', 'Mood Logging'),
        ('chatting', 'Chatting'),
        ('goal_progress', 'Goal Progress'),
        ('appointment_attendance', 'Appointment Attendance'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streaks')
    streak_type = models.CharField(max_length=25, choices=STREAK_CHOICES)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'streak_type')
        indexes = [
            models.Index(fields=['user', 'streak_type']),
            models.Index(fields=['last_activity_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_streak_type_display()}: {self.current_streak} days"

    def update_streak(self, activity_date):
        """Update streak based on activity date"""
        from datetime import timedelta

        if self.last_activity_date:
            days_diff = (activity_date - self.last_activity_date).days

            if days_diff == 1:
                # Consecutive day
                self.current_streak += 1
            elif days_diff > 1:
                # Streak broken
                self.current_streak = 1
            # If days_diff == 0, same day activity, don't change streak
        else:
            # First activity
            self.current_streak = 1

        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_activity_date = activity_date
        self.save()


class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('classic', 'Classic'),
        ('premium', 'Premium'),
    ]

    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)  # List of features included
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name} (${self.price_monthly}/month)"

    class Meta:
        ordering = ['price_monthly']


class UserSubscription(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
        ('mobile', 'Mobile Money'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(default=timezone.now)
    auto_renew = models.BooleanField(default=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['end_date']),
            models.Index(fields=['plan', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

    def is_active(self):
        return self.status == 'active' and timezone.now() < self.end_date

    def days_until_expiry(self):
        if self.end_date:
            return max(0, (self.end_date - timezone.now()).days)
        return 0

    class Meta:
        ordering = ['-start_date']


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.subscription.user.username}"

    def is_overdue(self):
        return self.status in ['sent', 'overdue'] and timezone.now() > self.due_date

    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['subscription', '-issue_date']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['invoice_number']),
        ]


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
        ('mobile', 'Mobile Money'),
        ('cash', 'Cash'),
        ('check', 'Check'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Payment {self.amount} - {self.subscription.user.username} ({self.status})"

    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['subscription', '-payment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['transaction_id']),
        ]


class CalendarIntegration(models.Model):
    """Model for Google Calendar integration"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='calendar_integration')
    google_calendar_id = models.CharField(max_length=255, blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    is_connected = models.BooleanField(default=False)
    last_sync = models.DateTimeField(blank=True, null=True)
    sync_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Calendar Integration for {self.user.username}"

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_connected']),
            models.Index(fields=['last_sync']),
        ]


class Appointment(models.Model):
    """Model for appointments and counseling sessions"""
    APPOINTMENT_TYPE_CHOICES = [
        ('counseling', 'Counseling Session'),
        ('follow_up', 'Follow-up Session'),
        ('crisis', 'Crisis Intervention'),
        ('group', 'Group Session'),
        ('workshop', 'Workshop'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts_counselor_appointments', limit_choices_to={'role': 'counselor'})
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='counseling')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    location = models.CharField(max_length=255, blank=True)  # Physical location or virtual meeting link
    notes = models.TextField(blank=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)  # For Google Calendar sync
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username} with {self.counselor.username}"

    def is_upcoming(self):
        return self.scheduled_date > timezone.now() and self.status in ['scheduled', 'confirmed']

    def get_end_time(self):
        return self.scheduled_date + timezone.timedelta(minutes=self.duration_minutes)

    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['user', '-scheduled_date']),
            models.Index(fields=['counselor', '-scheduled_date']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['appointment_type']),
        ]


class SocialMediaIntegration(models.Model):
    """Model for social media sharing integrations"""
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_integration')
    facebook_access_token = models.TextField(blank=True, null=True)
    facebook_token_expiry = models.DateTimeField(blank=True, null=True)
    twitter_access_token = models.TextField(blank=True, null=True)
    twitter_token_secret = models.TextField(blank=True, null=True)
    instagram_access_token = models.TextField(blank=True, null=True)
    linkedin_access_token = models.TextField(blank=True, null=True)
    tiktok_access_token = models.TextField(blank=True, null=True)
    sharing_enabled = models.BooleanField(default=True)
    auto_share_achievements = models.BooleanField(default=False)
    auto_share_milestones = models.BooleanField(default=False)
    last_facebook_post = models.DateTimeField(blank=True, null=True)
    last_twitter_post = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Social Integration for {self.user.username}"

    def is_platform_connected(self, platform):
        """Check if a specific platform is connected"""
        token_field = f"{platform}_access_token"
        return getattr(self, token_field, None) is not None

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['sharing_enabled']),
        ]


class SocialMediaPost(models.Model):
    """Model for scheduled social media posts"""
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_posts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    post_id = models.CharField(max_length=255, blank=True, null=True)  # Platform-specific post ID
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.platform} post by {self.user.username} - {self.status}"

    def is_ready_to_post(self):
        return (self.status == 'scheduled' and
                self.scheduled_time and
                self.scheduled_time <= timezone.now())

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['platform']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_time']),
        ]


class MoodDataShare(models.Model):
    """Model for sharing mood tracking data to social platforms"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_shares')
    mood_entry = models.ForeignKey(MoodEntry, on_delete=models.CASCADE, related_name='shares')
    platform = models.CharField(max_length=20, choices=SocialMediaPost.PLATFORM_CHOICES)
    shared_content = models.TextField()
    post_id = models.CharField(max_length=255, blank=True, null=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Mood share to {self.platform} by {self.user.username}"

    class Meta:
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['user', '-shared_at']),
            models.Index(fields=['mood_entry']),
            models.Index(fields=['platform']),
            models.Index(fields=['is_successful']),
        ]


class FileAttachment(models.Model):
    """Model for file attachments in messages and resources"""
    FILE_TYPES = [
        ('image', 'Image'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]

    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='other')
    file_size = models.PositiveIntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.TextField(blank=True, null=True)  # Encrypted key for file decryption

    def __str__(self):
        return f"{self.filename} ({self.get_file_type_display()})"

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return ".1f"
            size /= 1024.0
        return ".1f"

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_by', '-uploaded_at']),
            models.Index(fields=['file_type']),
            models.Index(fields=['uploaded_at']),
        ]


class SharedFile(models.Model):
    """Model for shared files between users"""
    file = models.ForeignKey(FileAttachment, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_files')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_files')
    shared_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file.filename} shared by {self.shared_by.username} with {self.shared_with.username}"

    def is_expired(self):
        """Check if the share has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def can_download(self):
        """Check if file can still be downloaded"""
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        if self.max_downloads and self.download_count >= self.max_downloads:
            return False
        return True

    class Meta:
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['shared_by', '-shared_at']),
            models.Index(fields=['shared_with', '-shared_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_active']),
        ]


class PushNotification(models.Model):
    """Model for push notifications"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('appointment', 'Appointment Reminder'),
        ('achievement', 'Achievement Unlocked'),
        ('system', 'System Notification'),
        ('mood_reminder', 'Mood Check-in Reminder'),
        ('feedback', 'Feedback Request'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    data = models.JSONField(blank=True, null=True)  # Additional data for the notification
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} for {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', '-sent_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['is_sent']),
        ]


class OfflineData(models.Model):
    """Model for storing offline data synchronization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offline_data')
    data_type = models.CharField(max_length=50)  # e.g., 'mood_entries', 'messages', 'appointments'
    data_id = models.CharField(max_length=100)  # ID of the data item
    data_content = models.JSONField()  # The actual data content
    version = models.PositiveIntegerField(default=1)
    is_synced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(blank=True, null=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.data_type}:{self.data_id} for {self.user.username}"

    def mark_synced(self):
        """Mark data as synchronized"""
        self.is_synced = True
        self.synced_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'data_type', '-created_at']),
            models.Index(fields=['user', 'is_synced']),
            models.Index(fields=['data_type', 'data_id']),
            models.Index(fields=['device_id']),
        ]
        unique_together = ('user', 'data_type', 'data_id', 'device_id')


class APIKey(models.Model):
    """Model for third-party API integrations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)  # Human-readable name
    key_id = models.CharField(max_length=100, unique=True)  # Public key identifier
    secret_key = models.TextField()  # Encrypted secret key
    service_name = models.CharField(max_length=50)  # e.g., 'google_calendar', 'slack', 'webhook'
    permissions = models.JSONField(default=list)  # List of allowed permissions
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.service_name}) for {self.user.username}"

    def is_expired(self):
        """Check if the API key has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def can_use_permission(self, permission):
        """Check if the key has a specific permission"""
        return permission in self.permissions

    def record_usage(self):
        """Record that the key was used"""
        self.last_used_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['key_id']),
            models.Index(fields=['service_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]


class Webhook(models.Model):
    """Model for webhook integrations"""
    WEBHOOK_EVENTS = [
        ('mood_logged', 'Mood Entry Logged'),
        ('appointment_created', 'Appointment Created'),
        ('message_sent', 'Message Sent'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('user_registered', 'User Registered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhooks')
    name = models.CharField(max_length=100)
    url = models.URLField()
    secret = models.TextField()  # For webhook signature verification
    events = models.JSONField(default=list)  # List of events to trigger webhook
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered_at = models.DateTimeField(blank=True, null=True)
    failure_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} webhook for {self.user.username}"

    def should_trigger_for_event(self, event_type):
        """Check if webhook should trigger for a specific event"""
        return event_type in self.events

    def record_trigger(self, success=True):
        """Record webhook trigger"""
        self.last_triggered_at = timezone.now()
        if not success:
            self.failure_count += 1
        self.save()

    def is_failing(self):
        """Check if webhook is failing too often"""
        return self.failure_count >= 5

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_triggered_at']),
        ]


class VideoCall(models.Model):
    """Model for video calls and meetings"""
    CALL_TYPES = [
        ('counseling', 'Counseling Session'),
        ('group', 'Group Session'),
        ('workshop', 'Workshop'),
        ('peer_support', 'Peer Support'),
    ]

    PROVIDERS = [
        ('twilio', 'Twilio Video'),
        ('zoom', 'Zoom'),
    ]

    STATUSES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    call_type = models.CharField(max_length=20, choices=CALL_TYPES, default='counseling')
    provider = models.CharField(max_length=20, choices=PROVIDERS, default='twilio')
    status = models.CharField(max_length=20, choices=STATUSES, default='scheduled')

    # Provider-specific data
    room_sid = models.CharField(max_length=100, blank=True, null=True)  # Twilio
    meeting_id = models.CharField(max_length=100, blank=True, null=True)  # Zoom
    join_url = models.URLField(blank=True, null=True)  # Zoom
    start_url = models.URLField(blank=True, null=True)  # Zoom
    password = models.CharField(max_length=50, blank=True, null=True)  # Zoom

    # Participants
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_calls')
    participants = models.ManyToManyField(User, related_name='video_calls', blank=True)

    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    # Settings
    max_participants = models.IntegerField(default=10)
    recording_enabled = models.BooleanField(default=False)
    chat_enabled = models.BooleanField(default=True)
    waiting_room = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_call_type_display()} ({self.get_status_display()})"

    def is_active(self):
        """Check if call is currently active"""
        return self.status == 'active'

    def can_join(self, user):
        """Check if user can join this call"""
        if self.status not in ['scheduled', 'active']:
            return False
        if user == self.host:
            return True
        return self.participants.filter(id=user.id).exists()

    def start_call(self):
        """Mark call as started"""
        if self.status == 'scheduled':
            self.status = 'active'
            self.actual_start = timezone.now()
            self.save()

    def end_call(self):
        """Mark call as completed"""
        if self.status == 'active':
            self.status = 'completed'
            self.actual_end = timezone.now()
            self.save()

    def get_duration(self):
        """Get call duration in minutes"""
        if self.actual_start and self.actual_end:
            return int((self.actual_end - self.actual_start).total_seconds() / 60)
        elif self.actual_start and self.status == 'active':
            return int((timezone.now() - self.actual_start).total_seconds() / 60)
        return 0

    class Meta:
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['host', '-scheduled_start']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_start']),
            models.Index(fields=['call_type']),
            models.Index(fields=['provider']),
        ]


class Notification(models.Model):
    """Model for user notifications"""
    NOTIFICATION_TYPES = [
        ('system', 'System'),
        ('message', 'Message'),
        ('appointment', 'Appointment'),
        ('achievement', 'Achievement'),
        ('feedback', 'Feedback'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['sent']),
        ]
