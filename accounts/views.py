from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .tasks import send_welcome_email, send_notification_email
from django.views.decorators.csrf import csrf_protect
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
import csv
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    User, MoodEntry, Achievement, Appointment, CalendarIntegration, SocialMediaIntegration,
    SocialMediaPost, MoodDataShare, SubscriptionPlan, UserSubscription, Invoice, Payment, VideoCall,
    FileAttachment, SharedFile, PushNotification, OfflineData, APIKey, Webhook
)
from .forms import CustomUserCreationForm, ProfileUpdateForm, MoodForm, SubscriptionPlanForm
from .integrations import GoogleCalendarService, CalendarReminderService
from .social_integrations import FacebookService, TwitterService, SocialMediaScheduler
# from chat.models import Notification  # Commented out as chat app doesn't exist


def registration_view(request):
    """View for user registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to SafeTalk.")

            # Send welcome email asynchronously
            send_welcome_email.delay(user.id)

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.middleware.csrf import get_token
                from safetalk.security import SecurityService

                security_service = SecurityService()
                access_token = security_service.generate_secure_token(32)
                refresh_token = security_service.generate_secure_token(32)

                # Store tokens in session for server-side validation
                request.session['access_token'] = access_token
                request.session['refresh_token'] = refresh_token

                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful!',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role,
                    }
                })

            return redirect('client_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
def login_view(request):
    """View for user login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful! Welcome back.")

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.middleware.csrf import get_token
                from safetalk.security import SecurityService

                security_service = SecurityService()
                access_token = security_service.generate_secure_token(32)
                refresh_token = security_service.generate_secure_token(32)

                # Store tokens in session for server-side validation
                request.session['access_token'] = access_token
                request.session['refresh_token'] = refresh_token

                return JsonResponse({
                    'success': True,
                    'message': 'Login successful!',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role,
                    }
                })

            # Regular form submission - redirect based on user role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'counselor':
                return redirect('counselor_dashboard')
            else:  # client
                return redirect('client_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid username or password.'
                })
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')


@login_required
def profile_view(request, user_id=None):
    """View for user profile"""
    if user_id:
        # Viewing another user's profile (admin/counselor only)
        if request.user.role not in ['admin', 'counselor']:
            messages.error(request, "You don't have permission to view other profiles.")
            return redirect('profile')

        try:
            profile_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('manage_users')
    else:
        # Viewing own profile
        profile_user = request.user

    context = {
        'profile_user': profile_user,
        'is_own_profile': profile_user == request.user,
        'mood_entries': MoodEntry.objects.filter(user=profile_user),
        'upcoming_appointments': Appointment.objects.filter(
            user=profile_user,
            scheduled_date__gte=timezone.now()
        ),
        'achievements': Achievement.objects.filter(user=profile_user),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request, user_id=None):
    """View for editing user profile"""
    # Handle both positional and keyword arguments
    if user_id is None and len(request.resolver_match.kwargs) > 0:
        # Get user_id from URL kwargs if not passed as parameter
        user_id = request.resolver_match.kwargs.get('user_id')
    """View for editing user profile"""
    if user_id:
        # Editing another user's profile (admin/counselor only)
        if request.user.role not in ['admin', 'counselor']:
            messages.error(request, "You don't have permission to edit other profiles.")
            return redirect('profile')

        try:
            profile_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('manage_users')
    else:
        # Editing own profile
        profile_user = request.user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile_user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            # Redirect to manage_users if admin/counselor editing another user
            if user_id and request.user.role in ['admin', 'counselor']:
                return redirect('manage_users')
            elif user_id:
                return redirect('user_profile', user_id=user_id)
            else:
                return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile_user)

    context = {
        'form': form,
        'profile_user': profile_user,
        'is_own_profile': profile_user == request.user,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def account_settings_view(request):
    """View for account settings (notifications, privacy, etc.)"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_notifications':
            # Update notification preferences
            preferences = [
                'notification_message', 'notification_appointment', 'notification_feedback',
                'notification_achievement', 'notification_system', 'notification_sound'
            ]

            for pref in preferences:
                value = request.POST.get(pref) == 'on'
                setattr(request.user, pref, value)

            request.user.save()
            messages.success(request, "Notification preferences updated successfully!")

        elif action == 'update_privacy':
            # Update privacy settings
            request.user.is_profile_public = request.POST.get('is_profile_public') == 'on'
            request.user.show_mood_history = request.POST.get('show_mood_history') == 'on'
            request.user.allow_data_sharing = request.POST.get('allow_data_sharing') == 'on'
            request.user.save()
            messages.success(request, "Privacy settings updated successfully!")

        elif action == 'change_password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            elif len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, "Password changed successfully!")

        return redirect('account_settings')

    context = {
        'user': request.user,
    }
    return render(request, 'accounts/account_settings.html', context)


@login_required
def achievements_view(request):
    """View for displaying user achievements"""
    achievements = Achievement.objects.filter(user=request.user).order_by('-unlocked_at')
    context = {
        'achievements': achievements,
    }
    return render(request, 'accounts/achievements.html', context)


@login_required
def log_mood(request):
    """View for logging mood entries"""
    if request.method == 'POST':
        form = MoodForm(request.POST)
        if form.is_valid():
            mood_entry = form.save(commit=False)
            mood_entry.user = request.user
            mood_entry.save()
            messages.success(request, "Mood logged successfully!")
            return redirect('mood_history')
    else:
        form = MoodForm()
    return render(request, 'accounts/log_mood.html', {'form': form})


@login_required
def mood_history(request):
    """View for displaying mood history"""
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')
    context = {
        'mood_entries': mood_entries,
    }
    return render(request, 'accounts/mood_history.html', context)


def logout_view(request):
    """View for user logout"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def add_user_view(request):
    """View for adding new users (admin/counselor only)"""
    if request.user.role not in ['admin', 'counselor']:
        messages.error(request, "You don't have permission to add users.")
        return redirect('profile')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully!")
            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/add_user.html', {'form': form})


@login_required
def user_list_view(request):
    """View for listing all users"""
    if request.user.role not in ['admin', 'counselor']:
        messages.error(request, "You don't have permission to view users.")
        return redirect('profile')

    users = User.objects.all().order_by('username')
    context = {
        'users': users,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
def user_insights(request):
    """View for displaying user insights and analytics"""
    if request.user.role not in ['admin', 'counselor']:
        messages.error(request, "You don't have permission to view insights.")
        return redirect('profile')

    # Mood statistics
    mood_stats = MoodEntry.objects.aggregate(
        total_entries=Count('id'),
        avg_mood=Avg('mood')
    )

    # Monthly mood trends
    monthly_trends = MoodEntry.objects.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        count=Count('id'),
        avg_mood=Avg('mood')
    ).order_by('month')

    # User activity
    user_activity = User.objects.annotate(
        mood_count=Count('mood_entries')
    ).values('username', 'mood_count').order_by('-mood_count')[:10]

    context = {
        'mood_stats': mood_stats,
        'monthly_trends': monthly_trends,
        'user_activity': user_activity,
    }
    return render(request, 'accounts/user_insights.html', context)


@login_required
def export_mood_data(request):
    """View for exporting mood data to CSV"""
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mood_data.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Mood', 'Note'])

    for entry in mood_entries:
        writer.writerow([
            entry.date,
            entry.get_mood_display(),
            entry.note or ''
        ])

    return response


@require_POST
@login_required
def notification_preferences_api(request):
    """API view for updating notification preferences"""
    preferences = [
        'notification_message', 'notification_appointment', 'notification_feedback',
        'notification_achievement', 'notification_system', 'notification_sound'
    ]

    for pref in preferences:
        value = request.POST.get(pref) == 'on'
        setattr(request.user, pref, value)

    request.user.save()
    return JsonResponse({'success': True})


@login_required
def subscription_plans(request):
    """View for displaying available subscription plans"""
    if request.user.role != 'client':
        messages.error(request, "Access denied. This page is only available to clients.")
        return redirect('profile')

    plans = SubscriptionPlan.objects.filter(is_active=True)
    # Also include deactivated plans for reactivation
    deactivated_plans = SubscriptionPlan.objects.filter(is_active=False)
    context = {
        'plans': plans,
        'deactivated_plans': deactivated_plans,
    }
    return render(request, 'accounts/subscription_plans.html', context)


@login_required
def subscribe(request, plan_name):
    """View for subscribing to a plan"""
    try:
        plan = SubscriptionPlan.objects.get(name=plan_name, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        messages.error(request, "Plan not found.")
        return redirect('subscription_plans')

    # Check if user already has an active subscription
    existing_subscription = UserSubscription.objects.filter(
        user=request.user,
        status__in=['active', 'pending']
    ).first()

    if existing_subscription:
        messages.error(request, "You already have an active subscription.")
        return redirect('subscription_status')

    # Create Stripe checkout session
    from .payment_integrations import StripePaymentService
    checkout_session = StripePaymentService.create_subscription_checkout_session(request.user, plan)

    if checkout_session:
        return redirect(checkout_session.url)
    else:
        messages.error(request, "Failed to create payment session. Please try again.")
        return redirect('subscription_plans')


@login_required
def subscription_status(request):
    """View for displaying subscription status"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        subscription = None

    context = {
        'subscription': subscription,
    }
    return render(request, 'accounts/subscription_status.html', context)


@login_required
def cancel_subscription(request):
    """View for canceling subscription"""
    try:
        subscription = UserSubscription.objects.get(user=request.user, status='active')

        # Cancel with payment processor
        from .payment_integrations import StripePaymentService
        success = StripePaymentService.cancel_subscription(subscription)

        if success:
            messages.success(request, "Subscription cancelled successfully.")
        else:
            messages.error(request, "Failed to cancel subscription. Please contact support.")

    except UserSubscription.DoesNotExist:
        messages.error(request, "No active subscription found.")

    return redirect('subscription_status')


@login_required
def renew_subscription(request):
    """View for renewing subscription"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        if subscription.status == 'expired':
            # Create new checkout session for renewal
            from .payment_integrations import StripePaymentService
            checkout_session = StripePaymentService.create_subscription_checkout_session(request.user, subscription.plan)

            if checkout_session:
                return redirect(checkout_session.url)
            else:
                messages.error(request, "Failed to create renewal session. Please try again.")
        else:
            messages.error(request, "Subscription is not expired.")
    except UserSubscription.DoesNotExist:
        messages.error(request, "No subscription found.")

    return redirect('subscription_status')


@login_required
def subscription_success(request):
    """Handle successful subscription payment"""
    session_id = request.GET.get('session_id')
    if session_id:
        messages.success(request, "Subscription activated successfully! Welcome to SafeTalk Premium.")
    else:
        messages.success(request, "Subscription updated successfully!")

    return redirect('subscription_status')


@login_required
def subscription_cancel(request):
    """Handle cancelled subscription payment"""
    messages.info(request, "Subscription cancelled. You can subscribe anytime.")
    return redirect('subscription_plans')


@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    from .payment_integrations import PaymentService
    success = PaymentService.process_webhook(request)

    if success:
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error'}, status=400)


# Video calling views
@login_required
def video_calls_list(request):
    """View for listing video calls"""
    # Show calls where user is host or participant
    calls = VideoCall.objects.filter(
        models.Q(host=request.user) | models.Q(participants=request.user)
    ).distinct().order_by('-scheduled_start')

    upcoming = calls.filter(
        scheduled_start__gte=timezone.now(),
        status__in=['scheduled', 'active']
    )

    past = calls.filter(
        models.Q(scheduled_start__lt=timezone.now()) | models.Q(status__in=['completed', 'cancelled'])
    )[:10]

    context = {
        'upcoming_calls': upcoming,
        'past_calls': past,
    }
    return render(request, 'accounts/video_calls.html', context)


@login_required
def create_video_call(request):
    """View for creating new video calls"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        call_type = request.POST.get('call_type', 'counseling')
        provider = request.POST.get('provider', 'twilio')
        scheduled_start_str = request.POST.get('scheduled_start')
        duration = int(request.POST.get('duration', 60))
        max_participants = int(request.POST.get('max_participants', 10))

        try:
            scheduled_start = datetime.fromisoformat(scheduled_start_str.replace('T', ' '))
            scheduled_end = scheduled_start + timedelta(minutes=duration)

            # Create video call record
            video_call = VideoCall.objects.create(
                title=title,
                description=description,
                call_type=call_type,
                provider=provider,
                host=request.user,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                max_participants=max_participants,
                recording_enabled=request.POST.get('recording_enabled') == 'on',
                chat_enabled=request.POST.get('chat_enabled') != 'off',
                waiting_room=request.POST.get('waiting_room') != 'off',
            )

            # Add participants if specified
            participant_ids = request.POST.getlist('participants')
            if participant_ids:
                participants = User.objects.filter(id__in=participant_ids)
                video_call.participants.add(*participants)

            # Create video service call
            from .video_integrations import VideoCallService
            service = VideoCallService(provider)

            call_data = {
                'room_name': f"call_{video_call.id}",
                'topic': title,
                'start_time': scheduled_start,
                'duration': duration,
            }

            call_info = service.create_call(call_data)

            if call_info:
                # Update video call with provider data
                if provider == 'twilio':
                    video_call.room_sid = call_info.get('room_sid')
                elif provider == 'zoom':
                    video_call.meeting_id = call_info.get('meeting_id')
                    video_call.join_url = call_info.get('join_url')
                    video_call.start_url = call_info.get('start_url')
                    video_call.password = call_info.get('password')
                video_call.save()

                messages.success(request, "Video call created successfully!")
                return redirect('video_call_detail', call_id=video_call.id)
            else:
                video_call.status = 'failed'
                video_call.save()
                messages.error(request, "Failed to create video call with provider.")

        except ValueError as e:
            messages.error(request, f"Invalid date format: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error creating video call: {str(e)}")

    # Get available participants (counselors and clients)
    counselors = User.objects.filter(role='counselor', is_active=True).exclude(id=request.user.id)
    clients = User.objects.filter(role='client', is_active=True).exclude(id=request.user.id)

    context = {
        'counselors': counselors,
        'clients': clients,
    }
    return render(request, 'accounts/create_video_call.html', context)


@login_required
def video_call_detail(request, call_id):
    """View for video call details and joining"""
    try:
        video_call = VideoCall.objects.get(id=call_id)

        # Check if user can access this call
        if not video_call.can_join(request.user):
            messages.error(request, "You don't have permission to join this call.")
            return redirect('video_calls_list')

        # Generate access token if needed
        access_token = None
        if video_call.provider == 'twilio' and video_call.room_sid:
            from .video_integrations import VideoCallService
            service = VideoCallService('twilio')
            access_token = service.generate_token(str(request.user.id), video_call.room_sid)

        context = {
            'video_call': video_call,
            'access_token': access_token,
            'can_join': video_call.status in ['scheduled', 'active'] and video_call.can_join(request.user),
            'is_host': video_call.host == request.user,
        }
        return render(request, 'accounts/video_call_detail.html', context)

    except VideoCall.DoesNotExist:
        messages.error(request, "Video call not found.")
        return redirect('video_calls_list')


@login_required
@require_POST
def start_video_call(request, call_id):
    """API view to start a video call"""
    try:
        video_call = VideoCall.objects.get(id=call_id, host=request.user)

        if video_call.status == 'scheduled':
            video_call.start_call()
            return JsonResponse({'success': True, 'message': 'Call started successfully'})

        return JsonResponse({'success': False, 'error': 'Call cannot be started'})

    except VideoCall.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Call not found'})


@login_required
@require_POST
def end_video_call(request, call_id):
    """API view to end a video call"""
    try:
        video_call = VideoCall.objects.get(id=call_id, host=request.user)

        if video_call.status == 'active':
            video_call.end_call()

            # End call with provider
            from .video_integrations import VideoCallService
            service = VideoCallService(video_call.provider)
            service.end_call({
                'room_sid': video_call.room_sid,
                'meeting_id': video_call.meeting_id,
            })

            return JsonResponse({'success': True, 'message': 'Call ended successfully'})

        return JsonResponse({'success': False, 'error': 'Call is not active'})

    except VideoCall.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Call not found'})


@login_required
@require_POST
def join_video_call(request, call_id):
    """API view to join a video call"""
    try:
        video_call = VideoCall.objects.get(id=call_id)

        if not video_call.can_join(request.user):
            return JsonResponse({'success': False, 'error': 'Cannot join this call'})

        # Generate access token for Twilio
        access_token = None
        if video_call.provider == 'twilio' and video_call.room_sid:
            from .video_integrations import VideoCallService
            service = VideoCallService('twilio')
            access_token = service.generate_token(str(request.user.id), video_call.room_sid)

        return JsonResponse({
            'success': True,
            'access_token': access_token,
            'room_name': video_call.room_sid or f"call_{video_call.id}",
            'join_url': video_call.join_url,
        })

    except VideoCall.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Call not found'})


# Admin views for subscription management
@login_required
def admin_plan_management(request):
    """Admin view for managing subscription plans"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    plans = SubscriptionPlan.objects.all().order_by('price_monthly')
    # Don't filter by is_active=True so deactivated plans remain visible for reactivation
    context = {
        'plans': plans,
    }
    return render(request, 'accounts/admin_plan_management.html', context)


@login_required
def admin_create_plan(request):
    """Admin view for creating new subscription plans"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    if request.method == 'POST':
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan created successfully!")
            return redirect('admin_plan_management')
    else:
        form = SubscriptionPlanForm()

    context = {
        'form': form,
        'service_choices': [
            ('google_calendar', 'Google Calendar'),
            ('slack', 'Slack'),
            ('webhook', 'Webhook'),
            ('zapier', 'Zapier'),
            ('ifttt', 'IFTTT'),
        ]
    }
    return render(request, 'accounts/admin_create_plan.html', context)


@login_required
def admin_edit_plan(request, plan_id):
    """Admin view for editing subscription plans"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    if request.method == 'POST':
        plan.display_name = request.POST.get('display_name')
        plan.description = request.POST.get('description')
        plan.price_monthly = request.POST.get('price_monthly')
        plan.features = request.POST.getlist('features')
        plan.is_active = request.POST.get('is_active') == 'on'
        plan.save()
        messages.success(request, "Plan updated successfully!")
        return redirect('admin_plan_management')

    context = {
        'plan': plan,
    }
    return render(request, 'accounts/admin_edit_plan.html', context)


@login_required
def admin_toggle_plan_status(request, plan_id):
    """Admin view for toggling plan status"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return JsonResponse({'error': 'Access denied'})

    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    plan.is_active = not plan.is_active
    plan.save()

    return JsonResponse({'success': True, 'is_active': plan.is_active})


@login_required
def admin_subscription_management(request):
    """Admin view for managing all subscriptions"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    subscriptions = UserSubscription.objects.all().select_related('user', 'plan').order_by('-start_date')

    # Calculate statistics
    total_subscriptions = subscriptions.count()
    active_subscriptions = subscriptions.filter(status='active').count()

    # Calculate revenue (simplified - would need more complex logic for real implementation)
    active_subs = subscriptions.filter(status='active')
    total_revenue = sum(sub.plan.price_monthly for sub in active_subs)

    # Calculate churn rate (simplified)
    expired_count = subscriptions.filter(status='expired').count()
    churn_rate = (expired_count / total_subscriptions * 100) if total_subscriptions > 0 else 0

    # Get plans
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')

    context = {
        'subscriptions': subscriptions,
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'total_revenue': total_revenue,
        'churn_rate': churn_rate,
        'plans': plans,
    }
    return render(request, 'accounts/admin_subscription_management.html', context)


@login_required
def admin_subscription_detail(request, subscription_id):
    """Admin view for subscription details"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    subscription = get_object_or_404(UserSubscription, id=subscription_id)
    invoices = subscription.invoices.all().order_by('-issue_date')
    payments = subscription.payments.all().order_by('-payment_date')

    context = {
        'subscription': subscription,
        'invoices': invoices,
        'payments': payments,
    }
    return render(request, 'accounts/admin_subscription_detail.html', context)


@login_required
def admin_invoice_management(request):
    """Admin view for managing invoices"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    invoices = Invoice.objects.all().select_related('subscription__user').order_by('-issue_date')
    context = {
        'invoices': invoices,
    }
    return render(request, 'accounts/admin_invoice_management.html', context)


@login_required
def admin_create_invoice(request, subscription_id):
    """Admin view for creating invoices"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    subscription = get_object_or_404(UserSubscription, id=subscription_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        due_date_str = request.POST.get('due_date')

        try:
            due_date = datetime.fromisoformat(due_date_str)
            invoice_number = f"INV-{subscription.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

            Invoice.objects.create(
                invoice_number=invoice_number,
                subscription=subscription,
                amount=amount,
                due_date=due_date
            )
            messages.success(request, "Invoice created successfully!")
            return redirect('admin_subscription_detail', subscription_id=subscription_id)
        except ValueError:
            messages.error(request, "Invalid date format.")

    context = {
        'subscription': subscription,
    }
    return render(request, 'accounts/admin_create_invoice.html', context)


@login_required
def admin_send_invoice(request, invoice_id):
    """Admin view for sending invoices"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice.status = 'sent'
    invoice.save()
    messages.success(request, "Invoice sent successfully!")
    return redirect('admin_invoice_management')


@login_required
def admin_payment_management(request):
    """Admin view for managing payments"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    payments = Payment.objects.all().select_related('subscription__user').order_by('-payment_date')
    context = {
        'payments': payments,
    }
    return render(request, 'accounts/admin_payment_management.html', context)


@login_required
def admin_record_payment(request, subscription_id):
    """Admin view for recording payments"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    subscription = get_object_or_404(UserSubscription, id=subscription_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id')

        Payment.objects.create(
            subscription=subscription,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='completed'
        )

        # Update subscription status if payment completes it
        if subscription.status == 'pending':
            subscription.status = 'active'
            subscription.last_payment_date = timezone.now()
            subscription.save()

        messages.success(request, "Payment recorded successfully!")
        return redirect('admin_subscription_detail', subscription_id=subscription_id)

    context = {
        'subscription': subscription,
    }
    return render(request, 'accounts/admin_record_payment.html', context)


class SubscriptionRequiredMiddleware(MiddlewareMixin):
    """
    Middleware to check if user has an active subscription for premium features.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware for certain views
        exempt_urls = [
            reverse('login'),
            reverse('register'),
            reverse('logout'),
            '/admin/',
            '/accounts/subscription',
            '/accounts/subscribe',
        ]

        if request.path.startswith(tuple(exempt_urls)):
            return None

        # Check if user is authenticated
        if not request.user.is_authenticated:
            return None

        # Check if user has active subscription for premium features
        try:
            subscription = request.user.subscription
            if not subscription.is_active():
                # Redirect to subscription page for premium features
                if request.path.startswith('/chat/') or request.path.startswith('/analytics/'):
                    return redirect('subscription_plans')
        except:
            # No subscription found, redirect to subscription page for premium features
            if request.path.startswith('/chat/') or request.path.startswith('/analytics/'):
                return redirect('subscription_plans')

        return None


@login_required
def calendar_view(request):
    """Calendar view for managing appointments and schedule"""
    from django.utils import timezone
    from datetime import timedelta

    # Get user's appointments
    appointments = Appointment.objects.filter(
        user=request.user
    ).order_by('scheduled_date')

    # Separate upcoming and past appointments
    now = timezone.now()
    upcoming_appointments = appointments.filter(scheduled_date__gte=now)[:10]
    past_appointments = appointments.filter(scheduled_date__lt=now)[:5]

    context = {
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'user_role': request.user.role,
    }
    return render(request, 'dashboard/calendar.html', context)


@login_required
def calendar_settings(request):
    """View for managing Google Calendar integration settings"""
    calendar_integration, created = CalendarIntegration.objects.get_or_create(
        user=request.user,
        defaults={'sync_enabled': True}
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'connect':
            # Redirect to Google OAuth
            # This would typically redirect to allauth's Google OAuth flow
            messages.info(request, "Redirecting to Google for calendar access...")
            return redirect('account_settings')  # Fallback to account settings since socialaccount_connections doesn't exist

        elif action == 'disconnect':
            calendar_integration.is_connected = False
            calendar_integration.access_token = None
            calendar_integration.refresh_token = None
            calendar_integration.google_calendar_id = None
            calendar_integration.save()
            messages.success(request, "Google Calendar disconnected successfully.")

        elif action == 'sync':
            if calendar_integration.is_connected:
                service = GoogleCalendarService(calendar_integration)
                synced_count = service.sync_appointments()
                messages.success(request, f"Synced {synced_count} appointments to Google Calendar.")
            else:
                messages.error(request, "Google Calendar is not connected.")

        elif action == 'toggle_sync':
            calendar_integration.sync_enabled = not calendar_integration.sync_enabled
            calendar_integration.save()
            status = "enabled" if calendar_integration.sync_enabled else "disabled"
            messages.success(request, f"Calendar sync {status}.")

    context = {
        'calendar_integration': calendar_integration,
    }
    return render(request, 'accounts/calendar_settings.html', context)


@login_required
def social_settings(request):
    """View for managing social media integration settings"""
    social_integration, created = SocialMediaIntegration.objects.get_or_create(
        user=request.user,
        defaults={'sharing_enabled': True}
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'connect_facebook':
            messages.info(request, "Redirecting to Facebook for authentication...")
            return redirect('account_settings')  # Fallback to account settings since socialaccount_connections doesn't exist

        elif action == 'connect_twitter':
            messages.info(request, "Redirecting to Twitter for authentication...")
            return redirect('account_settings')  # Fallback to account settings since socialaccount_connections doesn't exist

        elif action == 'disconnect_facebook':
            social_integration.facebook_access_token = None
            social_integration.facebook_token_expiry = None
            social_integration.save()
            messages.success(request, "Facebook disconnected successfully.")

        elif action == 'disconnect_twitter':
            social_integration.twitter_access_token = None
            social_integration.twitter_token_secret = None
            social_integration.save()
            messages.success(request, "Twitter disconnected successfully.")

        elif action == 'toggle_sharing':
            social_integration.sharing_enabled = not social_integration.sharing_enabled
            social_integration.save()
            status = "enabled" if social_integration.sharing_enabled else "disabled"
            messages.success(request, f"Social sharing {status}.")

        elif action == 'toggle_auto_achievements':
            social_integration.auto_share_achievements = not social_integration.auto_share_achievements
            social_integration.save()
            status = "enabled" if social_integration.auto_share_achievements else "disabled"
            messages.success(request, f"Auto-share achievements {status}.")

        elif action == 'toggle_auto_milestones':
            social_integration.auto_share_milestones = not social_integration.auto_share_milestones
            social_integration.save()
            status = "enabled" if social_integration.auto_share_milestones else "disabled"
            messages.success(request, f"Auto-share milestones {status}.")

    context = {
        'social_integration': social_integration,
    }
    return render(request, 'accounts/social_settings.html', context)


@login_required
def appointments_list(request):
    """View for listing user appointments"""
    # Filter appointments based on user role
    if request.user.role == 'counselor':
        # Counselors see appointments where they are the counselor
        appointments = Appointment.objects.filter(
            counselor=request.user
        ).order_by('-scheduled_date')
    elif request.user.role == 'admin':
        # Admins see all appointments
        appointments = Appointment.objects.all().order_by('-scheduled_date')
    else:
        # Clients see their own appointments
        appointments = Appointment.objects.filter(
            user=request.user
        ).order_by('-scheduled_date')

    # Apply filters
    status = request.GET.get('status')
    counselor_id = request.GET.get('counselor')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        appointments = appointments.filter(status=status)

    if counselor_id:
        appointments = appointments.filter(counselor_id=counselor_id)

    if date_from:
        appointments = appointments.filter(scheduled_date__date__gte=date_from)

    if date_to:
        appointments = appointments.filter(scheduled_date__date__lte=date_to)

    if search:
        appointments = appointments.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search) |
            models.Q(counselor__first_name__icontains=search) |
            models.Q(counselor__last_name__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search)
        )

    upcoming = appointments.filter(
        scheduled_date__gte=timezone.now(),
        status__in=['scheduled', 'confirmed']
    )

    past = appointments.filter(
        scheduled_date__lt=timezone.now()
    ) | appointments.filter(status__in=['completed', 'cancelled'])

    # Get counselors for filter dropdown
    counselors = User.objects.filter(role='counselor', is_active=True)

    context = {
        'upcoming_appointments': upcoming,
        'past_appointments': past[:10],  # Show last 10 past appointments
        'counselors': counselors,
    }
    return render(request, 'accounts/appointments.html', context)


@login_required
def appointment_detail(request, appointment_id):
    """View for appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Check permissions
    if request.user.role == 'client' and appointment.user != request.user:
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('appointments_list')
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('appointments_list')

    context = {
        'appointment': appointment,
        'is_counselor': request.user.role == 'counselor',
    }
    return render(request, 'accounts/appointment_detail.html', context)


@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Check permissions
    if request.user.role == 'client' and appointment.user != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    # Check if appointment can be cancelled
    if appointment.status in ['completed', 'cancelled']:
        return JsonResponse({'success': False, 'error': 'Appointment cannot be cancelled'})

    if appointment.scheduled_date <= timezone.now() + timedelta(hours=24):
        return JsonResponse({'success': False, 'error': 'Appointments can only be cancelled at least 24 hours in advance'})

    appointment.status = 'cancelled'
    appointment.save()

    # Create notification
    Notification.objects.create(
        user=appointment.user,
        title='Appointment Cancelled',
        message=f'Your appointment "{appointment.title}" with {appointment.counselor.get_full_name() or appointment.counselor.username} has been cancelled.',
        notification_type='appointment',
        related_id=appointment.id
    )

    return JsonResponse({'success': True})


@login_required
def export_appointments(request):
    """Export appointments data"""
    # Filter appointments based on user role (same logic as appointments_list)
    if request.user.role == 'counselor':
        # Counselors see appointments where they are the counselor
        appointments = Appointment.objects.filter(
            counselor=request.user
        ).order_by('-scheduled_date')
    elif request.user.role == 'admin':
        # Admins see all appointments
        appointments = Appointment.objects.all().order_by('-scheduled_date')
    else:
        # Clients see their own appointments
        appointments = Appointment.objects.filter(
            user=request.user
        ).order_by('-scheduled_date')

    # Apply all filters from the form
    status = request.GET.get('status')
    counselor_id = request.GET.get('counselor')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status:
        appointments = appointments.filter(status=status)

    if counselor_id:
        appointments = appointments.filter(counselor_id=counselor_id)

    if date_from:
        appointments = appointments.filter(scheduled_date__date__gte=date_from)

    if date_to:
        appointments = appointments.filter(scheduled_date__date__lte=date_to)

    if search:
        appointments = appointments.filter(
            models.Q(title__icontains=search) |
            models.Q(description__icontains=search) |
            models.Q(counselor__first_name__icontains=search) |
            models.Q(counselor__last_name__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="appointments.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Client', 'Counselor', 'Title', 'Status', 'Duration', 'Description'])

    for appointment in appointments:
        writer.writerow([
            appointment.scheduled_date.date(),
            appointment.scheduled_date.time(),
            appointment.user.get_full_name() or appointment.user.username,
            appointment.counselor.get_full_name() or appointment.counselor.username,
            appointment.title,
            appointment.status,
            f"{appointment.duration_minutes} minutes",
            appointment.description or ''
        ])

    return response


@login_required
def create_appointment(request):
    """View for creating new appointments"""
    if request.method == 'POST':
        counselor_id = request.POST.get('counselor')
        client_id = request.POST.get('client')  # For counselors scheduling appointments
        title = request.POST.get('title')
        description = request.POST.get('description')
        scheduled_date_str = request.POST.get('scheduled_date')
        duration = int(request.POST.get('duration', 60))

        try:
            # Determine if counselor or client is creating the appointment
            if request.user.role == 'counselor':
                # Counselor scheduling for a client
                if not client_id:
                    messages.error(request, "Please select a client.")
                    return redirect('create_appointment')
                client = User.objects.get(id=client_id, role='client')
                counselor = request.user
                appointment_user = client
            else:
                # Client scheduling with a counselor
                counselor = User.objects.get(id=counselor_id, role='counselor')
                client = request.user
                appointment_user = request.user

            scheduled_date = datetime.fromisoformat(scheduled_date_str.replace('T', ' '))

            appointment = Appointment.objects.create(
                user=appointment_user,
                counselor=counselor,
                title=title,
                description=description,
                scheduled_date=scheduled_date,
                duration_minutes=duration,
                status='scheduled'
            )

            # Create notification for the client
            Notification.objects.create(
                user=appointment_user,
                title='New Appointment Scheduled',
                message=f'Your appointment "{title}" with {counselor.get_full_name() or counselor.username} has been scheduled for {scheduled_date.strftime("%B %d, %Y at %I:%M %p")}.',
                notification_type='appointment',
                related_id=appointment.id
            )

            # Try to sync with Google Calendar if connected
            try:
                calendar_integration = CalendarIntegration.objects.get(
                    user=appointment_user,
                    is_connected=True,
                    sync_enabled=True
                )
                service = GoogleCalendarService(calendar_integration)
                service.create_event(appointment)
            except CalendarIntegration.DoesNotExist:
                pass  # Calendar not connected, skip sync

            messages.success(request, "Appointment created successfully!")
            return redirect('appointments_list')

        except User.DoesNotExist:
            messages.error(request, "Selected user is not available.")
        except ValueError:
            messages.error(request, "Invalid date format.")
        except Exception as e:
            messages.error(request, f"Error creating appointment: {str(e)}")

    # Context based on user role
    if request.user.role == 'counselor':
        # Counselor can select clients
        clients = User.objects.filter(role='client', is_active=True)
        context = {
            'clients': clients,
            'is_counselor': True,
        }
    else:
        # Client selects counselor
        counselors = User.objects.filter(role='counselor', is_active=True)
        context = {
            'counselors': counselors,
            'is_counselor': False,
        }

    return render(request, 'accounts/create_appointment.html', context)


@login_required
def edit_appointment(request, appointment_id):
    """View for editing existing appointments"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Check permissions
    if request.user.role == 'client' and appointment.user != request.user:
        messages.error(request, "You don't have permission to edit this appointment.")
        return redirect('appointments_list')
    elif request.user.role == 'counselor' and appointment.counselor != request.user:
        messages.error(request, "You don't have permission to edit this appointment.")
        return redirect('appointments_list')

    if request.method == 'POST':
        counselor_id = request.POST.get('counselor')
        title = request.POST.get('title')
        description = request.POST.get('description')
        scheduled_date_str = request.POST.get('scheduled_date')
        duration = int(request.POST.get('duration', 60))

        try:
            if counselor_id:
                counselor = User.objects.get(id=counselor_id, role='counselor')
                appointment.counselor = counselor

            appointment.title = title
            appointment.description = description
            appointment.scheduled_date = datetime.fromisoformat(scheduled_date_str.replace('T', ' '))
            appointment.duration_minutes = duration

            appointment.save()

            # Try to update Google Calendar if connected
            try:
                calendar_integration = CalendarIntegration.objects.get(
                    user=appointment.user,
                    is_connected=True,
                    sync_enabled=True
                )
                service = GoogleCalendarService(calendar_integration)
                service.update_event(appointment)
            except CalendarIntegration.DoesNotExist:
                pass  # Calendar not connected, skip sync

            messages.success(request, "Appointment updated successfully!")
            return redirect('appointments_list')

        except User.DoesNotExist:
            messages.error(request, "Selected counselor is not available.")
        except ValueError:
            messages.error(request, "Invalid date format.")
        except Exception as e:
            messages.error(request, f"Error updating appointment: {str(e)}")

    counselors = User.objects.filter(role='counselor', is_active=True)
    context = {
        'appointment': appointment,
        'counselors': counselors,
        'is_edit': True,
    }
    return render(request, 'accounts/create_appointment.html', context)


@login_required
def social_posts(request):
    """View for managing scheduled social media posts"""
    posts = SocialMediaPost.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_post':
            platform = request.POST.get('platform')
            content = request.POST.get('content')
            scheduled_time_str = request.POST.get('scheduled_time')

            try:
                if scheduled_time_str:
                    scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('T', ' '))
                else:
                    scheduled_time = None

                SocialMediaPost.objects.create(
                    user=request.user,
                    platform=platform,
                    content=content,
                    scheduled_time=scheduled_time,
                    status='scheduled' if scheduled_time else 'draft'
                )
                messages.success(request, "Post created successfully!")
                return redirect('social_posts')

            except Exception as e:
                messages.error(request, f"Error creating post: {str(e)}")

        elif action == 'delete_post':
            post_id = request.POST.get('post_id')
            try:
                post = SocialMediaPost.objects.get(id=post_id, user=request.user)
                post.delete()
                messages.success(request, "Post deleted successfully.")
            except SocialMediaPost.DoesNotExist:
                messages.error(request, "Post not found.")

    context = {
        'posts': posts,
    }
    return render(request, 'accounts/social_posts.html', context)


@login_required
@require_POST
def share_mood_data(request):
    """AJAX view for sharing mood data on social media"""
    mood_entry_id = request.POST.get('mood_entry_id')
    platforms = request.POST.getlist('platforms')

    try:
        mood_entry = MoodEntry.objects.get(id=mood_entry_id, user=request.user)
        social_integration = SocialMediaIntegration.objects.get(user=request.user)

        if not social_integration.sharing_enabled:
            return JsonResponse({'success': False, 'error': 'Social sharing is disabled'})

        shared_platforms = []
        for platform in platforms:
            if social_integration.is_platform_connected(platform):
                if platform == 'facebook':
                    service = FacebookService(social_integration)
                elif platform == 'twitter':
                    service = TwitterService(social_integration)
                else:
                    continue

                mood_emoji = mood_entry.get_mood_display().split(' ')[0]
                content = f"{mood_emoji} Feeling {mood_entry.get_mood_display()} today"

                if mood_entry.note:
                    content += f"\n\n{mood_entry.note}"

                content += "\n\n#MentalHealth #MoodTracking #SafeTalk"

                if service.post_content(platform, content):
                    MoodDataShare.objects.create(
                        user=request.user,
                        mood_entry=mood_entry,
                        platform=platform,
                        shared_content=content,
                        is_successful=True
                    )
                    shared_platforms.append(platform)

        if shared_platforms:
            return JsonResponse({
                'success': True,
                'message': f'Shared on {", ".join(shared_platforms)}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to share on selected platforms'
            })

    except MoodEntry.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mood entry not found'})
    except SocialMediaIntegration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Social integration not configured'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mood_shares_history(request):
    """View for mood data sharing history"""
    shares = MoodDataShare.objects.filter(user=request.user).order_by('-shared_at')

    context = {
        'shares': shares,
    }
    return render(request, 'accounts/mood_shares.html', context)


# AJAX views for calendar integration
@login_required
@require_POST
def sync_calendar(request):
    """AJAX view to sync appointments with Google Calendar"""
    try:
        calendar_integration = CalendarIntegration.objects.get(
            user=request.user,
            is_connected=True
        )

        service = GoogleCalendarService(calendar_integration)
        synced_count = service.sync_appointments()

        return JsonResponse({
            'success': True,
            'synced_count': synced_count
        })

    except CalendarIntegration.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Google Calendar not connected'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def update_appointment_calendar(request, appointment_id):
    """AJAX view to update appointment in Google Calendar"""
    try:
        appointment = Appointment.objects.get(id=appointment_id, user=request.user)
        calendar_integration = CalendarIntegration.objects.get(
            user=request.user,
            is_connected=True
        )

        service = GoogleCalendarService(calendar_integration)

        if appointment.google_event_id:
            success = service.update_event(appointment)
        else:
            event_id = service.create_event(appointment)
            success = event_id is not None

        return JsonResponse({'success': success})

    except Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Appointment not found'})
    except CalendarIntegration.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calendar not connected'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# File sharing and upload views
@login_required
def file_list(request):
    """View for listing user's files"""
    files = FileAttachment.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    shared_with_me = SharedFile.objects.filter(shared_with=request.user, is_active=True).select_related('file')

    context = {
        'files': files,
        'shared_files': shared_with_me,
    }
    return render(request, 'accounts/file_list.html', context)


@login_required
def upload_file(request):
    """View for uploading files"""
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Validate file
        from safetalk.security import SecurityService
        security_service = SecurityService()
        is_valid, error_msg = security_service.validate_file_upload(
            uploaded_file,
            allowed_types=['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            max_size=10 * 1024 * 1024  # 10MB
        )

        if not is_valid:
            messages.error(request, f"File upload failed: {error_msg}")
            return redirect('file_list')

        # Determine file type
        mime_type = uploaded_file.content_type
        if mime_type.startswith('image/'):
            file_type = 'image'
        elif mime_type == 'application/pdf':
            file_type = 'document'
        elif mime_type.startswith('audio/'):
            file_type = 'audio'
        elif mime_type.startswith('video/'):
            file_type = 'video'
        else:
            file_type = 'document'

        # Create file attachment
        file_attachment = FileAttachment.objects.create(
            file=uploaded_file,
            filename=uploaded_file.name,
            file_type=file_type,
            file_size=uploaded_file.size,
            mime_type=mime_type,
            uploaded_by=request.user,
            is_encrypted=False  # Could be made configurable
        )

        messages.success(request, f"File '{uploaded_file.name}' uploaded successfully!")
        return redirect('file_list')

    return render(request, 'accounts/upload_file.html')


@login_required
def share_file(request, file_id):
    """View for sharing files with other users"""
    file_attachment = get_object_or_404(FileAttachment, id=file_id, uploaded_by=request.user)

    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        expires_days = request.POST.get('expires_days')
        max_downloads = request.POST.get('max_downloads')

        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=int(expires_days))

        max_downloads_int = int(max_downloads) if max_downloads else None

        shared_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                SharedFile.objects.create(
                    file=file_attachment,
                    shared_by=request.user,
                    shared_with=user,
                    expires_at=expires_at,
                    max_downloads=max_downloads_int
                )
                shared_count += 1
            except User.DoesNotExist:
                continue

        if shared_count > 0:
            messages.success(request, f"File shared with {shared_count} user(s)!")
        else:
            messages.error(request, "No users selected or invalid users.")

        return redirect('file_list')

    # Get users to share with (exclude self and get counselors/clients)
    users = User.objects.exclude(id=request.user.id).filter(
        role__in=['counselor', 'client'],
        is_active=True
    ).order_by('username')

    context = {
        'file': file_attachment,
        'users': users,
    }
    return render(request, 'accounts/share_file.html', context)


@login_required
def download_shared_file(request, share_id):
    """View for downloading shared files"""
    shared_file = get_object_or_404(
        SharedFile,
        id=share_id,
        shared_with=request.user,
        is_active=True
    )

    if not shared_file.can_download():
        messages.error(request, "This file is no longer available for download.")
        return redirect('file_list')

    # Increment download count
    shared_file.download_count += 1
    shared_file.save()

    # Return file
    file_path = shared_file.file.file.path
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=shared_file.file.mime_type)
        response['Content-Disposition'] = f'attachment; filename="{shared_file.file.filename}"'
        return response


@login_required
def delete_file(request, file_id):
    """View for deleting user's files"""
    file_attachment = get_object_or_404(FileAttachment, id=file_id, uploaded_by=request.user)

    if request.method == 'POST':
        # Delete the file from storage
        file_attachment.file.delete(save=False)
        # Delete the database record
        file_attachment.delete()

        messages.success(request, f"File '{file_attachment.filename}' deleted successfully!")
        return redirect('file_list')

    context = {
        'file': file_attachment,
    }
    return render(request, 'accounts/delete_file.html', context)


# Push notification views
@login_required
def notification_list(request):
    """View for listing user notifications"""
    notifications = PushNotification.objects.filter(user=request.user).order_by('-sent_at')

    # Mark notifications as read when viewed
    unread_notifications = notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.mark_as_read()

    context = {
        'notifications': notifications,
        'unread_count': unread_notifications.count(),
    }
    return render(request, 'accounts/notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """API view to mark notification as read"""
    try:
        notification = PushNotification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except PushNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})


@login_required
@require_POST
def send_test_notification(request):
    """API view to send a test notification"""
    if request.user.role not in ['admin', 'counselor']:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    PushNotification.objects.create(
        user=request.user,
        title='Test Notification',
        message='This is a test notification to verify the system is working.',
        notification_type='system'
    )

    return JsonResponse({'success': True, 'message': 'Test notification sent!'})


# Offline functionality views
@login_required
@require_POST
def sync_offline_data(request):
    """API view to sync offline data"""
    try:
        data = request.POST.get('data')
        if not data:
            return JsonResponse({'success': False, 'error': 'No data provided'})

        import json
        offline_data = json.loads(data)

        synced_count = 0
        for item in offline_data:
            OfflineData.objects.update_or_create(
                user=request.user,
                data_type=item['data_type'],
                data_id=item['data_id'],
                device_id=item.get('device_id', 'web'),
                defaults={
                    'data_content': item['data_content'],
                    'version': item.get('version', 1),
                    'is_synced': True,
                    'synced_at': timezone.now(),
                }
            )
            synced_count += 1

        return JsonResponse({
            'success': True,
            'synced_count': synced_count,
            'message': f'Synced {synced_count} items successfully'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_offline_data(request):
    """API view to get offline data for sync"""
    device_id = request.GET.get('device_id', 'web')

    # Get unsynced data
    unsynced_data = OfflineData.objects.filter(
        user=request.user,
        device_id=device_id,
        is_synced=False
    ).values('data_type', 'data_id', 'data_content', 'version')

    return JsonResponse({
        'success': True,
        'data': list(unsynced_data)
    })


@login_required
@require_POST
def mark_data_synced(request):
    """API view to mark offline data as synced"""
    data_ids = request.POST.getlist('data_ids[]')

    updated_count = OfflineData.objects.filter(
        user=request.user,
        data_id__in=data_ids
    ).update(is_synced=True, synced_at=timezone.now())

    return JsonResponse({
        'success': True,
        'updated_count': updated_count
    })


# API integration views
@login_required
def api_keys_list(request):
    """View for managing API keys"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    api_keys = APIKey.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'api_keys': api_keys,
    }
    return render(request, 'accounts/api_keys.html', context)


@login_required
def create_api_key(request):
    """View for creating new API keys"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    if request.method == 'POST':
        name = request.POST.get('name')
        service_name = request.POST.get('service_name')
        permissions = request.POST.getlist('permissions')
        expires_days = request.POST.get('expires_days')

        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=int(expires_days))

        # Generate secure key
        from safetalk.security import SecurityService
        security_service = SecurityService()
        key_id = security_service.generate_secure_token(16)
        secret_key = security_service.generate_secure_token(32)

        APIKey.objects.create(
            user=request.user,
            name=name,
            key_id=key_id,
            secret_key=security_service.encrypt_data(secret_key),
            service_name=service_name,
            permissions=permissions,
            expires_at=expires_at
        )

        messages.success(request, f"API key '{name}' created successfully!")
        return redirect('api_keys_list')

    context = {
        'service_choices': [
            ('google_calendar', 'Google Calendar'),
            ('slack', 'Slack'),
            ('webhook', 'Webhook'),
            ('zapier', 'Zapier'),
            ('ifttt', 'IFTTT'),
        ]
    }
    return render(request, 'accounts/create_api_key.html', context)


@login_required
def delete_api_key(request, key_id):
    """View for deleting API keys"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return JsonResponse({'success': False, 'error': 'Access denied'})

    try:
        api_key = APIKey.objects.get(id=key_id, user=request.user)
        api_key.delete()
        return JsonResponse({'success': True})
    except APIKey.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'API key not found'})


@login_required
def webhooks_list(request):
    """View for managing webhooks"""
    webhooks = Webhook.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'webhooks': webhooks,
    }
    return render(request, 'accounts/webhooks.html', context)


@login_required
def create_webhook(request):
    """View for creating new webhooks"""
    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')
        secret = request.POST.get('secret')
        events = request.POST.getlist('events')

        Webhook.objects.create(
            user=request.user,
            name=name,
            url=url,
            secret=secret,
            events=events
        )

        messages.success(request, f"Webhook '{name}' created successfully!")
        return redirect('webhooks_list')

    context = {
        'event_choices': [
            ('mood_logged', 'Mood Entry Logged'),
            ('appointment_created', 'Appointment Created'),
            ('message_sent', 'Message Sent'),
            ('achievement_unlocked', 'Achievement Unlocked'),
            ('user_registered', 'User Registered'),
            ('file_shared', 'File Shared'),
            ('notification_sent', 'Notification Sent'),
        ]
    }
    return render(request, 'accounts/create_webhook.html', context)


@login_required
def delete_webhook(request, webhook_id):
    """View for deleting webhooks"""
    try:
        webhook = Webhook.objects.get(id=webhook_id, user=request.user)
        webhook.delete()
        return JsonResponse({'success': True})
    except Webhook.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Webhook not found'})


# API endpoints for third-party integrations
def api_authenticate(request):
    """API authentication endpoint"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if not auth_header.startswith('Bearer '):
        return JsonResponse({'error': 'Invalid authorization header'}, status=401)

    token = auth_header[7:]  # Remove 'Bearer ' prefix

    try:
        # Find API key
        api_key = APIKey.objects.get(key_id=token[:16], is_active=True)

        if api_key.is_expired():
            return JsonResponse({'error': 'API key expired'}, status=401)

        # Decrypt and verify secret
        from safetalk.security import SecurityService
        security_service = SecurityService()
        stored_secret = security_service.decrypt_data(api_key.secret_key)

        if token[17:] != stored_secret:  # token format: key_id.secret
            return JsonResponse({'error': 'Invalid API key'}, status=401)

        # Record usage
        api_key.record_usage()

        # Attach user to request for further processing
        request.api_user = api_key.user
        request.api_key = api_key

        return None  # Continue to next middleware/view

    except APIKey.DoesNotExist:
        return JsonResponse({'error': 'Invalid API key'}, status=401)
    except Exception as e:
        return JsonResponse({'error': 'Authentication failed'}, status=401)


@login_required
def api_mood_entries(request):
    """API endpoint for mood entries"""
    if not hasattr(request, 'api_key'):
        return JsonResponse({'error': 'API authentication required'}, status=401)

    if not request.api_key.can_use_permission('read_mood'):
        return JsonResponse({'error': 'Insufficient permissions'}, status=403)

    mood_entries = MoodEntry.objects.filter(user=request.api_key.user).order_by('-date')

    data = []
    for entry in mood_entries:
        data.append({
            'id': entry.id,
            'mood': entry.mood,
            'mood_display': entry.get_mood_display(),
            'note': entry.note,
            'date': entry.date.isoformat(),
        })

    return JsonResponse({'success': True, 'data': data})


@login_required
def api_create_mood_entry(request):
    """API endpoint for creating mood entries"""
    if not hasattr(request, 'api_key'):
        return JsonResponse({'error': 'API authentication required'}, status=401)

    if not request.api_key.can_use_permission('write_mood'):
        return JsonResponse({'error': 'Insufficient permissions'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        import json
        data = json.loads(request.body)

        mood_entry = MoodEntry.objects.create(
            user=request.api_key.user,
            mood=data['mood'],
            note=data.get('note', ''),
            date=data.get('date', timezone.now().date())
        )

        return JsonResponse({
            'success': True,
            'data': {
                'id': mood_entry.id,
                'mood': mood_entry.mood,
                'date': mood_entry.date.isoformat(),
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_appointments(request):
    """API endpoint for appointments"""
    if not hasattr(request, 'api_key'):
        return JsonResponse({'error': 'API authentication required'}, status=401)

    if not request.api_key.can_use_permission('read_appointments'):
        return JsonResponse({'error': 'Insufficient permissions'}, status=403)

    appointments = Appointment.objects.filter(user=request.api_key.user).order_by('-scheduled_date')

    data = []
    for appointment in appointments:
        data.append({
            'id': appointment.id,
            'title': appointment.title,
            'description': appointment.description,
            'counselor': appointment.counselor.username,
            'scheduled_date': appointment.scheduled_date.isoformat(),
            'status': appointment.status,
        })

    return JsonResponse({'success': True, 'data': data})


@login_required
def api_send_notification(request):
    """API endpoint for sending notifications"""
    if not hasattr(request, 'api_key'):
        return JsonResponse({'error': 'API authentication required'}, status=401)

    if not request.api_key.can_use_permission('send_notifications'):
        return JsonResponse({'error': 'Insufficient permissions'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        import json
        data = json.loads(request.body)

        # Create notification
        notification = PushNotification.objects.create(
            user=request.api_key.user,
            title=data['title'],
            message=data['message'],
            notification_type=data.get('type', 'system'),
            data=data.get('data', {})
        )

        return JsonResponse({
            'success': True,
            'notification_id': notification.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def content_management(request):
    """View for content management (admin only)"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    context = {
        'page_title': 'Content Management',
        'page_subtitle': 'Manage platform resources and content',
    }
    return render(request, 'content.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('profile')

    # Get admin-specific data
    total_users = User.objects.count()
    total_clients = User.objects.filter(role='client').count()
    total_counselors = User.objects.filter(role='counselor').count()
    appointments_today = Appointment.objects.filter(
        scheduled_date__date=timezone.now().date()
    ).count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    active_sessions = 0  # Placeholder - implement session counting logic

    context = {
        'total_users': total_users,
        'total_clients': total_clients,
        'total_counselors': total_counselors,
        'appointments_today': appointments_today,
        'recent_users': recent_users,
        'active_sessions': active_sessions,
    }
    return render(request, 'dashboard.html', context)


@login_required
def counselor_dashboard(request):
    """Counselor dashboard view"""
    if request.user.role != 'counselor':
        messages.error(request, "Access denied.")
        return redirect('profile')

    # Get counselor-specific data
    active_clients = User.objects.filter(role='client').count()
    todays_appointments = Appointment.objects.filter(
        counselor=request.user,
        scheduled_date__gte=timezone.now(),
        scheduled_date__date=timezone.now().date()
    ).count()

    pending_sessions = Appointment.objects.filter(
        counselor=request.user,
        status='scheduled'
    ).count()

    unread_messages = 0  # Placeholder - implement message counting logic

    upcoming_appointments = Appointment.objects.filter(
        counselor=request.user,
        scheduled_date__gte=timezone.now()
    ).order_by('scheduled_date')[:5]

    recent_clients = []  # Placeholder - implement recent clients logic

    context = {
        'active_clients': active_clients,
        'todays_appointments': todays_appointments,
        'pending_sessions': pending_sessions,
        'unread_messages': unread_messages,
        'upcoming_appointments': upcoming_appointments,
        'recent_clients': recent_clients,
    }
    return render(request, 'dashboard.html', context)


@login_required
def client_dashboard(request):
    """Client dashboard view"""
    if request.user.role != 'client':
        messages.error(request, "Access denied.")
        return redirect('profile')

    # Get client-specific data
    recent_mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')[:5]
    upcoming_appointments = Appointment.objects.filter(
        user=request.user,
        scheduled_date__gte=timezone.now()
    ).order_by('scheduled_date')[:3]

    achievements = Achievement.objects.filter(user=request.user).order_by('-unlocked_at')[:3]

    # Additional context for new dashboard
    recent_messages = []  # Add message logic here if needed
    sessions_completed = 8  # Placeholder
    progress_percentage = 67
    goals_achieved = 5
    goals_percentage = 50
    current_streak = 7
    streak_percentage = 70

    context = {
        'recent_mood_entries': recent_mood_entries,
        'upcoming_appointments': upcoming_appointments,
        'achievements': achievements,
        'recent_messages': recent_messages,
        'sessions_completed': sessions_completed,
        'progress_percentage': progress_percentage,
        'goals_achieved': goals_achieved,
        'goals_percentage': goals_percentage,
        'current_streak': current_streak,
        'streak_percentage': streak_percentage,
    }
    return render(request, 'dashboard.html', context)


# Webhook processing
def process_webhook_trigger(user, event_type, data):
    """Process webhook triggers for events"""
    webhooks = Webhook.objects.filter(
        user=user,
        is_active=True
    ).exclude(
        failure_count__gte=5  # Skip failing webhooks
    )

    for webhook in webhooks:
        if webhook.should_trigger_for_event(event_type):
            # Trigger webhook asynchronously
            from .tasks import send_webhook
            send_webhook.delay(webhook.id, event_type, data)
