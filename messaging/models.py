from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('mention', 'Mention'),
        ('reply', 'Reply'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type}: {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now
            self.save()


class UserPresence(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    current_conversation = models.ForeignKey('Conversation', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {'Online' if self.is_online else 'Offline'}"

    def update_presence(self, is_online=True, conversation=None):
        self.is_online = is_online
        self.last_seen = timezone.now
        if conversation:
            self.current_conversation = conversation
        self.save()

    @property
    def status_display(self):
        if self.is_online:
            return 'Online'
        elif self.last_seen:
            now = timezone.now()
            diff = now - self.last_seen
            if diff.days > 0:
                return f'Last seen {diff.days} day{"s" if diff.days > 1 else ""} ago'
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f'Last seen {hours} hour{"s" if hours > 1 else ""} ago'
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f'Last seen {minutes} minute{"s" if minutes > 1 else ""} ago'
            else:
                return 'Last seen just now'
        return 'Offline'


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Add this field to fix the NOT NULL constraint error

    def __str__(self):
        if self.title:
            return self.title
        participants_names = [p.get_full_name() or p.username for p in self.participants.all()]
        return ', '.join(participants_names) or 'Conversation'

    @property
    def last_message(self):
        return self.messages.order_by('-timestamp').first()

    def unread_count(self, user):
        return self.messages.exclude(sender=user).exclude(read_by=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)
    is_read = models.BooleanField(default=False)  # Add this field to fix the NOT NULL constraint error

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'

    class Meta:
        ordering = ['timestamp']


class MessageAttachment(models.Model):
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(
        upload_to='message_attachments/%Y/%m/%d/',
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip']
        )]
    )
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Size in bytes
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Attachment: {self.filename}"

    @property
    def file_extension(self):
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''

    @property
    def is_image(self):
        return self.content_type.startswith('image/')

    @property
    def is_document(self):
        return self.content_type in ['application/pdf', 'application/msword',
                                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                   'text/plain']

    @property
    def is_archive(self):
        return self.content_type in ['application/zip', 'application/x-rar-compressed']

    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            self.filename = self.file.name
        if self.file and self.file_size == 0:
            self.file_size = self.file.size
        if self.file and not self.content_type:
            self.content_type = self.file.content_type or 'application/octet-stream'
        super().save(*args, **kwargs)