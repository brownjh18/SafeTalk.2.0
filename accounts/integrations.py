import os
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from django.utils import timezone
from django.conf import settings
from .models import CalendarIntegration, Appointment

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Service class for Google Calendar integration"""

    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]

    def __init__(self, calendar_integration):
        self.calendar_integration = calendar_integration
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Calendar API service"""
        try:
            creds = None
            if (self.calendar_integration.access_token and
                self.calendar_integration.refresh_token):

                creds = Credentials(
                    token=self.calendar_integration.access_token,
                    refresh_token=self.calendar_integration.refresh_token,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=settings.GOOGLE_CALENDAR_CLIENT_ID,
                    client_secret=settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                    scopes=self.SCOPES
                )

                # Refresh token if expired
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self._update_credentials(creds)

            if creds and creds.valid:
                self.service = build('calendar', 'v3', credentials=creds)
            else:
                self.service = None
                logger.warning(f"Invalid credentials for user {self.calendar_integration.user.username}")

        except Exception as e:
            logger.error(f"Error initializing Google Calendar service: {str(e)}")
            self.service = None

    def _update_credentials(self, creds):
        """Update stored credentials after refresh"""
        self.calendar_integration.access_token = creds.token
        if creds.refresh_token:
            self.calendar_integration.refresh_token = creds.refresh_token
        if creds.expiry:
            self.calendar_integration.token_expiry = creds.expiry
        self.calendar_integration.save()

    def is_connected(self):
        """Check if calendar service is properly connected"""
        return self.service is not None

    def create_event(self, appointment):
        """Create a Google Calendar event for an appointment"""
        if not self.is_connected():
            return None

        try:
            event = {
                'summary': appointment.title,
                'description': appointment.description or f"Counseling session with {appointment.counselor.username}",
                'start': {
                    'dateTime': appointment.scheduled_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': appointment.get_end_time().isoformat(),
                    'timeZone': 'UTC',
                },
                'location': appointment.location or 'Virtual Meeting',
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},      # 30 minutes before
                    ],
                },
            }

            calendar_id = self.calendar_integration.google_calendar_id or 'primary'
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()

            # Update appointment with Google event ID
            appointment.google_event_id = created_event['id']
            appointment.save()

            logger.info(f"Created Google Calendar event for appointment {appointment.id}")
            return created_event['id']

        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return None

    def update_event(self, appointment):
        """Update an existing Google Calendar event"""
        if not self.is_connected() or not appointment.google_event_id:
            return False

        try:
            event = {
                'summary': appointment.title,
                'description': appointment.description or f"Counseling session with {appointment.counselor.username}",
                'start': {
                    'dateTime': appointment.scheduled_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': appointment.get_end_time().isoformat(),
                    'timeZone': 'UTC',
                },
                'location': appointment.location or 'Virtual Meeting',
            }

            calendar_id = self.calendar_integration.google_calendar_id or 'primary'
            self.service.events().update(
                calendarId=calendar_id,
                eventId=appointment.google_event_id,
                body=event
            ).execute()

            logger.info(f"Updated Google Calendar event for appointment {appointment.id}")
            return True

        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error updating calendar event: {str(e)}")
            return False

    def delete_event(self, appointment):
        """Delete a Google Calendar event"""
        if not self.is_connected() or not appointment.google_event_id:
            return False

        try:
            calendar_id = self.calendar_integration.google_calendar_id or 'primary'
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=appointment.google_event_id
            ).execute()

            # Clear the Google event ID
            appointment.google_event_id = None
            appointment.save()

            logger.info(f"Deleted Google Calendar event for appointment {appointment.id}")
            return True

        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            return False

    def sync_appointments(self):
        """Sync all upcoming appointments to Google Calendar"""
        if not self.is_connected():
            return 0

        synced_count = 0
        upcoming_appointments = Appointment.objects.filter(
            user=self.calendar_integration.user,
            scheduled_date__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).exclude(google_event_id__isnull=False)

        for appointment in upcoming_appointments:
            if self.create_event(appointment):
                synced_count += 1

        self.calendar_integration.last_sync = timezone.now()
        self.calendar_integration.save()

        logger.info(f"Synced {synced_count} appointments for user {self.calendar_integration.user.username}")
        return synced_count


class CalendarReminderService:
    """Service for managing appointment reminders"""

    @staticmethod
    def send_reminders():
        """Send reminders for upcoming appointments"""
        # Appointments in next 24 hours that haven't had reminders sent
        reminder_time = timezone.now() + timedelta(hours=24)
        appointments = Appointment.objects.filter(
            scheduled_date__lte=reminder_time,
            scheduled_date__gt=timezone.now(),
            status__in=['scheduled', 'confirmed'],
            reminder_sent=False
        )

        reminder_count = 0
        for appointment in appointments:
            if CalendarReminderService._send_appointment_reminder(appointment):
                appointment.reminder_sent = True
                appointment.save()
                reminder_count += 1

        logger.info(f"Sent {reminder_count} appointment reminders")
        return reminder_count

    @staticmethod
    def _send_appointment_reminder(appointment):
        """Send reminder notification for a specific appointment"""
        try:
            from chat.models import Notification

            # Create notification for the user
            Notification.objects.create(
                user=appointment.user,
                title=f"Upcoming Appointment Reminder",
                message=f"You have an appointment with {appointment.counselor.username} on {appointment.scheduled_date.strftime('%B %d, %Y at %I:%M %p')}.",
                notification_type='appointment',
                related_id=appointment.id
            )

            # Also notify the counselor
            Notification.objects.create(
                user=appointment.counselor,
                title=f"Appointment Reminder",
                message=f"You have an appointment with {appointment.user.username} on {appointment.scheduled_date.strftime('%B %d, %Y at %I:%M %p')}.",
                notification_type='appointment',
                related_id=appointment.id
            )

            return True

        except Exception as e:
            logger.error(f"Error sending reminder for appointment {appointment.id}: {str(e)}")
            return False