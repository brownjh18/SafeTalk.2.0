from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Max
from django.utils import timezone
import json

from .models import Conversation, Message, MessageAttachment, Notification, UserPresence

User = get_user_model()


@login_required
def messages_view(request):
    """Main messages view showing conversations and chat interface"""
    # Get conversations for the current user
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count(
            'messages',
            filter=Q(messages__read_by__isnull=True) & ~Q(messages__sender=request.user)
        )
    ).order_by('-last_message_time').prefetch_related('participants', 'messages')

    # Prepare conversation data for template
    conversations_data = []
    for conv in conversations:
        other_participants = conv.participants.exclude(id=request.user.id)
        if other_participants.exists():
            other_participant = other_participants.first()
            conversations_data.append({
                'id': conv.id,
                'other_participants': [other_participant],
                'last_message': conv.last_message,
                'unread_count': conv.unread_count,
            })

    context = {
        'conversations': conversations_data,
        'is_admin': request.user.is_staff,
    }

    return render(request, 'messaging/messages.html', context)


@login_required
def start_chat_with_user(request, user_id):
    """Start a chat with a specific user"""
    other_user = get_object_or_404(User, id=user_id)

    # Don't allow chatting with yourself
    if other_user == request.user:
        return redirect('messaging:messages')

    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).annotate(
        participant_count=Count('participants')
    ).filter(participant_count=2).first()

    if existing_conversation:
        return redirect('messaging:conversation_detail', conversation_id=existing_conversation.id)

    # Create new conversation
    conversation = Conversation.objects.create()
    conversation.participants.set([request.user, other_user])

    return redirect('messaging:conversation_detail', conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    """View for a specific conversation - redirects to main messages view"""
    # Redirect to main messages view with conversation parameter
    return redirect(f'/messaging/?conversation={conversation_id}')


@login_required
@require_POST
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content', '').strip()
        else:
            content = request.POST.get('content', '').strip()

        if not content:
            return JsonResponse({'error': 'Message content cannot be empty'}, status=400)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        # Create notifications for other participants
        from .models import Notification
        other_participants = conversation.participants.exclude(id=request.user.id)
        for participant in other_participants:
            Notification.objects.create(
                recipient=participant,
                sender=request.user,
                notification_type='message',
                title=f'New message from {request.user.get_full_name() or request.user.username}',
                message=content[:100] + ('...' if len(content) > 100 else ''),
                conversation=conversation
            )

        # Broadcast message via WebSocket for real-time updates
        # This would be handled by Django Channels or similar WebSocket implementation

        return JsonResponse({
            'message_id': message.id,
            'timestamp': timezone.now().isoformat(),
            'success': True,
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def search_users(request):
    """Search for users to start conversations with"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'users': []})

    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]  # Limit results

    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': user.email,
            'role': getattr(user, 'role', 'User'),
        })

    return JsonResponse({'users': users_data})


@login_required
@require_POST
def create_conversation(request):
    """Create a new conversation with selected users"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            participant_ids = data.get('participants', [])
        else:
            participant_ids = request.POST.getlist('participants', [])

        if not participant_ids:
            return JsonResponse({'error': 'At least one participant required'}, status=400)

        # Convert to integers if needed
        participant_ids = [int(pid) for pid in participant_ids]

        # Add current user to participants
        participant_ids.append(request.user.id)

        # Remove duplicates
        participant_ids = list(set(participant_ids))

        # Get participant users
        participants = User.objects.filter(id__in=participant_ids)

        if len(participants) < 2:
            return JsonResponse({'error': 'Need at least 2 participants'}, status=400)

        # Check if conversation already exists (for 1-on-1 chats)
        if len(participants) == 2:
            existing_conversation = Conversation.objects.filter(
                participants__in=participants
            ).annotate(
                participant_count=Count('participants')
            ).filter(participant_count=2).first()

            if existing_conversation:
                return JsonResponse({
                    'conversation_id': existing_conversation.id,
                    'message': 'Conversation already exists',
                    'success': True
                })

        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.set(participants)

        return JsonResponse({
            'conversation_id': conversation.id,
            'message': 'Conversation created successfully',
            'success': True
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': 'Invalid participant IDs'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def archive_conversation(request, conversation_id):
    """Archive a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        conversation.is_active = False
        conversation.save()

        return JsonResponse({
            'success': True,
            'message': 'Conversation archived successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        # Store the conversation title for response
        conversation_title = str(conversation)

        # Delete the conversation (this will cascade delete messages and attachments)
        conversation.delete()

        return JsonResponse({
            'success': True,
            'message': f'Conversation "{conversation_title}" deleted successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def mute_conversation(request, conversation_id):
    """Mute notifications for a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        # For now, we'll use a simple approach - you could extend this with a proper muting model
        # Store muted conversations in user preferences or create a ConversationMute model
        muted_conversations = request.session.get('muted_conversations', [])
        if conversation_id not in muted_conversations:
            muted_conversations.append(conversation_id)
            request.session['muted_conversations'] = muted_conversations

        return JsonResponse({
            'success': True,
            'message': 'Conversation muted successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def unmute_conversation(request, conversation_id):
    """Unmute notifications for a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        muted_conversations = request.session.get('muted_conversations', [])
        if conversation_id in muted_conversations:
            muted_conversations.remove(conversation_id)
            request.session['muted_conversations'] = muted_conversations

        return JsonResponse({
            'success': True,
            'message': 'Conversation unmuted successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def conversations_api(request):
    """API endpoint to get conversations list"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__timestamp'),
        unread_count=Count(
            'messages',
            filter=Q(messages__read_by__isnull=True) & ~Q(messages__sender=request.user)
        )
    ).order_by('-last_message_time').prefetch_related('participants', 'messages')

    conversations_data = []
    for conv in conversations:
        other_participants = conv.participants.exclude(id=request.user.id)
        if other_participants.exists():
            other_participant = other_participants.first()
            conversations_data.append({
                'id': conv.id,
                'other_participants': [{
                    'id': other_participant.id,
                    'username': other_participant.username,
                    'full_name': other_participant.get_full_name(),
                }],
                'last_message': {
                    'id': conv.last_message.id if conv.last_message else None,
                    'content': conv.last_message.content if conv.last_message else 'No messages yet',
                    'timestamp': conv.last_message.timestamp.isoformat() if conv.last_message else None,
                    'sender_username': conv.last_message.sender.username if conv.last_message else None,
                    'is_read': request.user in conv.last_message.read_by.all() if conv.last_message else True,
                } if conv.last_message else None,
                'unread_count': conv.unread_count,
            })

    return JsonResponse({'conversations': conversations_data})


@login_required
def conversation_messages_api(request, conversation_id):
    """API endpoint to get messages for a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    messages = conversation.messages.all().order_by('timestamp').select_related('sender')

    messages_data = []
    for msg in messages:
        # Get attachment data
        attachments_data = []
        for attachment in msg.attachments.all():
            attachments_data.append({
                'id': attachment.id,
                'filename': attachment.filename,
                'file_size': attachment.file_size,
                'content_type': attachment.content_type,
                'is_image': attachment.is_image,
                'is_document': attachment.is_document,
                'is_archive': attachment.is_archive,
                'download_url': attachment.file.url
            })

        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'sender_username': msg.sender.username,
            'sender_id': msg.sender.id,
            'is_sent': msg.sender == request.user,
            'attachments': attachments_data,
        })

    participants_data = []
    for participant in conversation.participants.all():
        participants_data.append({
            'id': participant.id,
            'username': participant.username,
            'full_name': participant.get_full_name(),
        })

    return JsonResponse({
        'conversation_id': conversation.id,
        'title': conversation.title or f"Chat with {', '.join([p.get_full_name() or p.username for p in conversation.participants.exclude(id=request.user.id)])}",
        'participants': participants_data,
        'messages': messages_data,
    })


@login_required
def notifications_api(request):
    """API endpoint to get notifications for the current user"""
    notifications = Notification.objects.filter(recipient=request.user).select_related('sender', 'conversation')

    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'sender': {
                'id': notification.sender.id,
                'username': notification.sender.username,
                'full_name': notification.sender.get_full_name(),
            },
            'conversation_id': notification.conversation.id if notification.conversation else None,
        })

    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })


@login_required
def unread_notifications_api(request):
    """API endpoint to get unread notifications for the current user"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).select_related('sender', 'conversation').order_by('-created_at')

    notifications_data = []
    for notification in notifications[:10]:  # Limit to 10 recent notifications
        notifications_data.append({
            'id': notification.id,
            'type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.isoformat(),
            'sender': {
                'id': notification.sender.id,
                'username': notification.sender.username,
                'full_name': notification.sender.get_full_name(),
            },
            'conversation_id': notification.conversation.id if notification.conversation else None,
        })

    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': len(notifications_data)
    })


@login_required
def unread_notifications_count_api(request):
    """API endpoint to get unread notifications count for the current user"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return JsonResponse({
        'count': count
    })


@login_required
def notifications_page(request):
    """View for displaying all notifications for the current user"""
    # Get all notifications for the current user
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'conversation').order_by('-created_at')

    # Mark notifications as read when viewing the page
    unread_notifications = notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.mark_as_read()

    context = {
        'notifications': notifications,
        'unread_count': 0,  # All are now read
    }

    return render(request, 'messaging/notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.mark_as_read()

    return JsonResponse({'success': True})


@login_required
def unread_notifications_api(request):
    """API endpoint to get unread notifications for the current user"""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).select_related('sender', 'conversation').order_by('-created_at')

    notifications_data = []
    for notification in notifications[:10]:  # Limit to 10 recent notifications
        notifications_data.append({
            'id': notification.id,
            'type': notification.notification_type,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.isoformat(),
            'sender': {
                'id': notification.sender.id,
                'username': notification.sender.username,
                'full_name': notification.sender.get_full_name(),
            },
            'conversation_id': notification.conversation.id if notification.conversation else None,
        })

    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': len(notifications_data)
    })


@login_required
def unread_notifications_count_api(request):
    """API endpoint to get unread notifications count for the current user"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return JsonResponse({
        'count': count
    })


@login_required
def search_messages(request, conversation_id):
    """Search messages within a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'messages': []})

        # Get search options
        search_content = request.GET.get('content', 'true').lower() == 'true'
        search_sender = request.GET.get('sender', 'true').lower() == 'true'

        messages = conversation.messages.all().select_related('sender')

        # Filter messages based on search criteria
        results = []
        for message in messages:
            match = False
            match_reasons = []

            if search_content and query.lower() in message.content.lower():
                match = True
                match_reasons.append('content')

            if search_sender:
                sender_name = (message.sender.get_full_name() or message.sender.username).lower()
                if query.lower() in sender_name:
                    match = True
                    match_reasons.append('sender')

            if match:
                results.append({
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat(),
                    'sender_username': message.sender.username,
                    'sender_full_name': message.sender.get_full_name(),
                    'is_sent': message.sender == request.user,
                    'match_reasons': match_reasons
                })

        return JsonResponse({
            'messages': results,
            'query': query,
            'total_results': len(results)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def upload_attachment(request):
    """Upload a file attachment for a message"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)

        uploaded_file = request.FILES['file']

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return JsonResponse({'error': 'File size too large. Maximum size is 10MB'}, status=400)

        # Create a temporary message to attach the file to
        # In a real implementation, you might want to handle this differently
        temp_message = Message.objects.create(
            conversation_id=request.POST.get('conversation_id'),
            sender=request.user,
            content='File attachment'
        )

        # Create the attachment
        attachment = MessageAttachment.objects.create(
            message=temp_message,
            file=uploaded_file,
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content_type=uploaded_file.content_type or 'application/octet-stream'
        )

        return JsonResponse({
            'success': True,
            'attachment_id': attachment.id,
            'filename': attachment.filename,
            'file_size': attachment.file_size,
            'content_type': attachment.content_type,
            'is_image': attachment.is_image,
            'download_url': attachment.file.url
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def delete_attachment(request, attachment_id):
    """Delete a file attachment"""
    try:
        attachment = get_object_or_404(
            MessageAttachment,
            id=attachment_id,
            message__sender=request.user
        )

        # Store file path for deletion
        file_path = attachment.file.path
        attachment.delete()

        # Delete the file from storage
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def update_presence(request):
    """Update user presence status"""
    try:
        conversation_id = request.POST.get('conversation_id')
        is_online = request.POST.get('is_online', 'true').lower() == 'true'

        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    participants=request.user
                )
            except Conversation.DoesNotExist:
                pass  # User is not a participant in this conversation

        # Get or create presence record
        presence, created = UserPresence.objects.get_or_create(
            user=request.user,
            defaults={'is_online': is_online, 'current_conversation': conversation}
        )

        if not created:
            presence.is_online = is_online
            presence.last_seen = timezone.now()
            if conversation:
                presence.current_conversation = conversation
            presence.save()

        return JsonResponse({
            'success': True,
            'is_online': is_online,
            'last_seen': presence.last_seen.isoformat()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_user_presence(request, user_id):
    """Get presence status for a specific user"""
    try:
        target_user = get_object_or_404(User, id=user_id)

        from .models import UserPresence
        presence, created = UserPresence.objects.get_or_create(
            user=target_user,
            defaults={'is_online': False}
        )

        return JsonResponse({
            'user_id': target_user.id,
            'username': target_user.username,
            'is_online': presence.is_online,
            'last_seen': presence.last_seen.isoformat(),
            'status_display': presence.status_display
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_conversation_presence(request, conversation_id):
    """Get presence status for all participants in a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )

        from .models import UserPresence
        presence_data = []

        for participant in conversation.participants.exclude(id=request.user.id):
            presence, created = UserPresence.objects.get_or_create(
                user=participant,
                defaults={'is_online': False}
            )

            presence_data.append({
                'user_id': participant.id,
                'username': participant.username,
                'full_name': participant.get_full_name(),
                'is_online': presence.is_online,
                'last_seen': presence.last_seen.isoformat(),
                'status_display': presence.status_display,
                'current_conversation': presence.current_conversation.id if presence.current_conversation else None
            })

        return JsonResponse({
            'conversation_id': conversation.id,
            'participants_presence': presence_data
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )

    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_conversation_read(request, conversation_id):
    """Mark all messages in a conversation as read for the current user"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # Mark all messages in this conversation as read by current user
    unread_messages = conversation.messages.exclude(sender=request.user).exclude(read_by=request.user)
    for message in unread_messages:
        message.read_by.add(request.user)

    # Mark conversation as read in any notifications
    from .models import Notification
    Notification.objects.filter(
        recipient=request.user,
        conversation=conversation,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_message_read(request, message_id):
    """Mark a specific message as read"""
    message = get_object_or_404(
        Message,
        id=message_id,
        conversation__participants=request.user
    )

    if message.sender != request.user:  # Don't mark your own messages as read
        message.read_by.add(request.user)

    return JsonResponse({'success': True})