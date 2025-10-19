from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from .models import CalendarIntegration, SocialMediaIntegration


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for SafeTalk"""

    def save_user(self, request, user, form, commit=True):
        """Save user and create integration records"""
        user = super().save_user(request, user, form, commit)

        # Create integration records for new users
        CalendarIntegration.objects.get_or_create(
            user=user,
            defaults={'sync_enabled': True}
        )

        SocialMediaIntegration.objects.get_or_create(
            user=user,
            defaults={'sharing_enabled': True}
        )

        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for SafeTalk"""

    def save_user(self, request, sociallogin, form=None):
        """Save user from social login and set up integrations"""
        user = super().save_user(request, sociallogin, form)

        # Create integration records
        CalendarIntegration.objects.get_or_create(
            user=user,
            defaults={'sync_enabled': True}
        )

        SocialMediaIntegration.objects.get_or_create(
            user=user,
            defaults={'sharing_enabled': True}
        )

        return user

    def populate_user(self, request, sociallogin, data):
        """Populate user data from social provider"""
        user = super().populate_user(request, sociallogin, data)

        # Set additional fields based on provider
        provider = sociallogin.account.provider

        if provider == 'google':
            # Store Google-specific data for calendar integration
            sociallogin.account.extra_data = data

        elif provider == 'facebook':
            # Store Facebook-specific data
            sociallogin.account.extra_data = data

        return user

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors"""
        # Log the error for debugging
        print(f"Social auth error for {provider_id}: {error}")

        # Call parent method
        return super().authentication_error(
            request, provider_id, error, exception, extra_context
        )