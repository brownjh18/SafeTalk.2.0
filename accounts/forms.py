from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, MoodEntry, SubscriptionPlan

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True, initial='client')
    agree_terms = forms.BooleanField(required=True, label="I agree to the Terms of Service and Privacy Policy")
    newsletter = forms.BooleanField(required=False, label="Subscribe to newsletter")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'agree_terms', 'newsletter')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom error messages
        self.fields['username'].error_messages = {
            'unique': "A user with this username already exists.",
            'required': "Username is required.",
        }
        self.fields['email'].error_messages = {
            'unique': "A user with this email already exists.",
            'required': "Email is required.",
            'invalid': "Enter a valid email address.",
        }
        self.fields['first_name'].error_messages = {
            'required': "First name is required.",
        }
        self.fields['last_name'].error_messages = {
            'required': "Last name is required.",
        }
        self.fields['role'].error_messages = {
            'required': "Please select your role.",
        }
        self.fields['agree_terms'].error_messages = {
            'required': "You must agree to the terms and conditions.",
        }

class ClientRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

class ProfileUpdateForm(forms.ModelForm):
    # Additional fields for admin editing
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    timezone = forms.CharField(max_length=50, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'role', 'phone_number',
            'date_of_birth', 'timezone', 'bio', 'notifications_enabled',
            'notification_message', 'notification_appointment', 'notification_feedback',
            'notification_achievement', 'notification_system', 'notification_sound'
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'timezone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_message': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_appointment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_feedback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_achievement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_sound': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make role field optional for regular users
        if hasattr(self.instance, 'role') and self.instance.role not in ['admin', 'counselor']:
            self.fields['role'].required = False
            self.fields['role'].widget.attrs['disabled'] = True

class SubscriptionPlanForm(forms.ModelForm):
    features = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter features as comma-separated values'}),
        help_text="Enter features separated by commas (e.g., Feature 1, Feature 2, Feature 3)",
        required=False
    )

    class Meta:
        model = SubscriptionPlan
        fields = ('name', 'display_name', 'description', 'price_monthly', 'features', 'is_active')
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Premium Plan'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the plan...'}),
            'price_monthly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert features list to comma-separated string for display
        if self.instance and self.instance.pk and isinstance(self.instance.features, list):
            self.fields['features'].initial = ', '.join(self.instance.features)

    def clean_features(self):
        """Convert comma-separated string to list"""
        features_str = self.cleaned_data.get('features', '')
        if features_str.strip():
            # Split by comma and strip whitespace
            features_list = [f.strip() for f in features_str.split(',') if f.strip()]
            return features_list
        return []


class MoodForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ('mood', 'note')
        widgets = {
            'mood': forms.RadioSelect(attrs={'class': 'mood-radio'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional note about your mood...'}),
        }