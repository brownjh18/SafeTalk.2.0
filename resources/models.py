from django.db import models

class ResourceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Resource Categories"

    def __str__(self):
        return self.name

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('article', 'Article'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('guide', 'Guide'),
        ('exercise', 'Exercise'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='article')
    category = models.ForeignKey(ResourceCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")

    # Media file attachments
    attachment = models.FileField(upload_to='resources/%Y/%m/%d/', null=True, blank=True,
                                help_text="Upload a file (PDF, image, video, audio, etc.)")
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")

    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
