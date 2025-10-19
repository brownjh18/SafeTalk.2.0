import os
import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from twilio.rest import Client as TwilioClient
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

logger = logging.getLogger(__name__)


class TwilioVideoService:
    """Service for Twilio Video calling integration"""

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.api_key_sid = settings.TWILIO_API_KEY_SID
        self.api_key_secret = settings.TWILIO_API_KEY_SECRET
        self.client = TwilioClient(self.account_sid, self.auth_token) if all([
            self.account_sid, self.auth_token, self.api_key_sid, self.api_key_secret
        ]) else None

    def is_available(self):
        """Check if Twilio service is properly configured"""
        return self.client is not None

    def create_room(self, room_name, room_type='group'):
        """Create a Twilio video room"""
        if not self.is_available():
            return None

        try:
            room = self.client.video.rooms.create(
                unique_name=room_name,
                type=room_type,  # 'group', 'group-small', 'peer-to-peer'
                record_participants_on_connect=False,
                status_callback=settings.TWILIO_STATUS_CALLBACK_URL or None,
                status_callback_method='POST'
            )
            logger.info(f"Created Twilio room: {room.sid}")
            return {
                'sid': room.sid,
                'name': room.unique_name,
                'status': room.status,
                'type': room.type
            }
        except Exception as e:
            logger.error(f"Error creating Twilio room: {str(e)}")
            return None

    def get_room(self, room_sid):
        """Get room information"""
        if not self.is_available():
            return None

        try:
            room = self.client.video.rooms(room_sid).fetch()
            return {
                'sid': room.sid,
                'name': room.unique_name,
                'status': room.status,
                'type': room.type,
                'participants': room.participants_count
            }
        except Exception as e:
            logger.error(f"Error fetching room {room_sid}: {str(e)}")
            return None

    def end_room(self, room_sid):
        """End a Twilio video room"""
        if not self.is_available():
            return False

        try:
            room = self.client.video.rooms(room_sid).update(status='completed')
            logger.info(f"Ended Twilio room: {room.sid}")
            return True
        except Exception as e:
            logger.error(f"Error ending room {room_sid}: {str(e)}")
            return False

    def generate_access_token(self, identity, room_name):
        """Generate access token for a participant"""
        if not self.is_available():
            return None

        try:
            # Create access token
            token = AccessToken(
                self.account_sid,
                self.api_key_sid,
                self.api_key_secret,
                identity=identity,
                ttl=3600  # 1 hour
            )

            # Add video grant
            video_grant = VideoGrant(room=room_name)
            token.add_grant(video_grant)

            jwt_token = token.to_jwt()
            logger.info(f"Generated access token for {identity} in room {room_name}")
            return jwt_token.decode() if isinstance(jwt_token, bytes) else jwt_token

        except Exception as e:
            logger.error(f"Error generating access token: {str(e)}")
            return None

    def get_participants(self, room_sid):
        """Get list of participants in a room"""
        if not self.is_available():
            return []

        try:
            participants = self.client.video.rooms(room_sid).participants.list()
            return [{
                'sid': p.sid,
                'identity': p.identity,
                'status': p.status,
                'start_time': p.date_created,
                'end_time': p.date_updated if p.status == 'disconnected' else None
            } for p in participants]
        except Exception as e:
            logger.error(f"Error getting participants for room {room_sid}: {str(e)}")
            return []

    def remove_participant(self, room_sid, participant_sid):
        """Remove a participant from a room"""
        if not self.is_available():
            return False

        try:
            self.client.video.rooms(room_sid).participants(participant_sid).update(status='disconnected')
            logger.info(f"Removed participant {participant_sid} from room {room_sid}")
            return True
        except Exception as e:
            logger.error(f"Error removing participant {participant_sid}: {str(e)}")
            return False


class ZoomVideoService:
    """Service for Zoom Video SDK integration"""

    def __init__(self):
        self.api_key = settings.ZOOM_API_KEY
        self.api_secret = settings.ZOOM_API_SECRET
        self.account_id = settings.ZOOM_ACCOUNT_ID

    def is_available(self):
        """Check if Zoom service is properly configured"""
        return all([self.api_key, self.api_secret, self.account_id])

    def generate_jwt_token(self):
        """Generate JWT token for Zoom API authentication"""
        import jwt
        import datetime

        try:
            payload = {
                'iss': self.api_key,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                'iat': datetime.datetime.utcnow(),
            }
            token = jwt.encode(payload, self.api_secret, algorithm='HS256')
            return token if isinstance(token, str) else token.decode()
        except Exception as e:
            logger.error(f"Error generating Zoom JWT: {str(e)}")
            return None

    def create_meeting(self, topic, start_time=None, duration=60):
        """Create a Zoom meeting"""
        if not self.is_available():
            return None

        try:
            token = self.generate_jwt_token()
            if not token:
                return None

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            data = {
                'topic': topic,
                'type': 2,  # Scheduled meeting
                'start_time': start_time.isoformat() if start_time else None,
                'duration': duration,
                'timezone': 'UTC',
                'agenda': 'SafeTalk Counseling Session',
                'settings': {
                    'host_video': True,
                    'participant_video': True,
                    'join_before_host': False,
                    'mute_upon_entry': True,
                    'watermark': False,
                    'use_pmi': False,
                    'approval_type': 0,  # Automatically approve
                    'audio': 'both',  # Both telephone and computer audio
                    'auto_recording': 'none'
                }
            }

            response = requests.post(
                f'https://api.zoom.us/v2/users/me/meetings',
                headers=headers,
                json=data
            )
            response.raise_for_status()

            meeting_data = response.json()
            logger.info(f"Created Zoom meeting: {meeting_data['id']}")
            return {
                'id': meeting_data['id'],
                'join_url': meeting_data['join_url'],
                'start_url': meeting_data['start_url'],
                'password': meeting_data.get('password'),
                'topic': meeting_data['topic'],
                'start_time': meeting_data.get('start_time')
            }

        except Exception as e:
            logger.error(f"Error creating Zoom meeting: {str(e)}")
            return None

    def get_meeting(self, meeting_id):
        """Get meeting information"""
        if not self.is_available():
            return None

        try:
            token = self.generate_jwt_token()
            headers = {'Authorization': f'Bearer {token}'}

            response = requests.get(
                f'https://api.zoom.us/v2/meetings/{meeting_id}',
                headers=headers
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error getting Zoom meeting {meeting_id}: {str(e)}")
            return None

    def delete_meeting(self, meeting_id):
        """Delete a Zoom meeting"""
        if not self.is_available():
            return False

        try:
            token = self.generate_jwt_token()
            headers = {'Authorization': f'Bearer {token}'}

            response = requests.delete(
                f'https://api.zoom.us/v2/meetings/{meeting_id}',
                headers=headers
            )
            response.raise_for_status()

            logger.info(f"Deleted Zoom meeting: {meeting_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting Zoom meeting {meeting_id}: {str(e)}")
            return False


class VideoCallService:
    """Unified video calling service interface"""

    PROVIDERS = {
        'twilio': TwilioVideoService,
        'zoom': ZoomVideoService,
    }

    def __init__(self, provider='twilio'):
        self.provider = provider
        self.service = self.PROVIDERS.get(provider)()

    def is_available(self):
        """Check if video service is available"""
        return self.service and self.service.is_available()

    def create_call(self, call_data):
        """Create a video call"""
        if self.provider == 'twilio':
            return self._create_twilio_call(call_data)
        elif self.provider == 'zoom':
            return self._create_zoom_call(call_data)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _create_twilio_call(self, call_data):
        """Create Twilio video call"""
        room_name = call_data.get('room_name', f"call_{timezone.now().strftime('%Y%m%d_%H%M%S')}")
        room_type = call_data.get('room_type', 'group')

        room = self.service.create_room(room_name, room_type)
        if room:
            return {
                'provider': 'twilio',
                'room_sid': room['sid'],
                'room_name': room['name'],
                'status': room['status'],
                'type': room['type']
            }
        return None

    def _create_zoom_call(self, call_data):
        """Create Zoom video call"""
        topic = call_data.get('topic', 'SafeTalk Video Call')
        start_time = call_data.get('start_time')
        duration = call_data.get('duration', 60)

        meeting = self.service.create_meeting(topic, start_time, duration)
        if meeting:
            return {
                'provider': 'zoom',
                'meeting_id': meeting['id'],
                'join_url': meeting['join_url'],
                'start_url': meeting['start_url'],
                'password': meeting.get('password'),
                'topic': meeting['topic']
            }
        return None

    def generate_token(self, identity, room_name):
        """Generate access token for participant"""
        if self.provider == 'twilio':
            return self.service.generate_access_token(identity, room_name)
        else:
            # Zoom doesn't require client-side tokens like Twilio
            return None

    def end_call(self, call_data):
        """End a video call"""
        if self.provider == 'twilio':
            room_sid = call_data.get('room_sid')
            return self.service.end_room(room_sid) if room_sid else False
        elif self.provider == 'zoom':
            meeting_id = call_data.get('meeting_id')
            return self.service.delete_meeting(meeting_id) if meeting_id else False
        return False

    def get_call_info(self, call_data):
        """Get call information"""
        if self.provider == 'twilio':
            room_sid = call_data.get('room_sid')
            return self.service.get_room(room_sid) if room_sid else None
        elif self.provider == 'zoom':
            meeting_id = call_data.get('meeting_id')
            return self.service.get_meeting(meeting_id) if meeting_id else None
        return None