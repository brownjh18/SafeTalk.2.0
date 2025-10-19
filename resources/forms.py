from django import forms
from .models import Resource, ResourceCategory

class ResourceForm(forms.ModelForm):
    attachment = forms.FileField(
        required=False,
        label="File Attachment",
        help_text="Upload a file (PDF, image, video, audio, etc.) - Max 10MB",
        widget=forms.FileInput(attrs={
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.mp4,.mp3,.wav,.avi,.mov',
            'class': 'file-input'
        })
    )

    class Meta:
        model = Resource
        fields = ['title', 'content', 'resource_type', 'category', 'tags', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'tags': forms.TextInput(attrs={'placeholder': 'Comma-separated tags'}),
        }

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Check file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if attachment.size > max_size:
                raise forms.ValidationError('File size must be under 10MB.')

            # Check file type
            allowed_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain',
                'image/jpeg',
                'image/png',
                'image/gif',
                'video/mp4',
                'audio/mpeg',
                'audio/wav',
                'video/avi',
                'video/quicktime'
            ]

            if hasattr(attachment, 'content_type') and attachment.content_type not in allowed_types:
                # Also check file extension as fallback
                allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.wav', '.avi', '.mov']
                file_ext = '.' + attachment.name.split('.')[-1].lower() if '.' in attachment.name else ''
                if file_ext not in allowed_extensions:
                    raise forms.ValidationError('Unsupported file type. Please upload PDF, document, image, video, or audio files.')

        return attachment