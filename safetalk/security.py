import re
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityService:
    """Comprehensive security service for SafeTalk"""

    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key"""
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            # Generate a new key (in production, this should be stored securely)
            key = Fernet.generate_key()
        return key

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        encrypted = self.fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid encrypted data")

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength requirements"""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in weak_passwords:
            errors.append("Password is too common")

        return len(errors) == 0, errors

    def verify_recaptcha(self, token: str) -> bool:
        """Verify reCAPTCHA token"""
        secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', None)
        if not secret_key:
            logger.warning("reCAPTCHA secret key not configured")
            return True  # Allow in development

        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': secret_key,
                    'response': token
                },
                timeout=10
            )

            result = response.json()
            return result.get('success', False)

        except Exception as e:
            logger.error(f"reCAPTCHA verification failed: {e}")
            return False

    def check_rate_limit(self, identifier: str, action: str, limit: int = 10, window: int = 60) -> bool:
        """Check if action is within rate limits"""
        cache_key = f"rate_limit:{action}:{identifier}"
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            return False

        cache.set(cache_key, current_count + 1, window)
        return True

    def log_security_event(self, event_type: str, user: Optional[User], details: Dict, severity: str = 'info'):
        """Log security-related events"""
        log_data = {
            'event_type': event_type,
            'user_id': user.id if user else None,
            'user_email': user.email if user else None,
            'timestamp': timezone.now(),
            'details': details,
            'ip_address': details.get('ip_address'),
            'user_agent': details.get('user_agent')
        }

        if severity == 'error':
            logger.error(f"Security event: {event_type}", extra=log_data)
        elif severity == 'warning':
            logger.warning(f"Security event: {event_type}", extra=log_data)
        else:
            logger.info(f"Security event: {event_type}", extra=log_data)

    def detect_suspicious_activity(self, user: User, activity_data: Dict) -> Dict:
        """Detect suspicious user activity"""
        suspicious_patterns = {
            'multiple_failed_logins': self._check_failed_logins(user),
            'unusual_login_location': self._check_login_location(user, activity_data),
            'rapid_password_changes': self._check_password_changes(user),
            'unusual_access_patterns': self._check_access_patterns(user, activity_data)
        }

        risk_score = sum(pattern['risk'] for pattern in suspicious_patterns.values() if pattern['detected'])

        return {
            'risk_score': risk_score,
            'patterns': suspicious_patterns,
            'requires_action': risk_score > 50
        }

    def _check_failed_logins(self, user: User) -> Dict:
        """Check for multiple failed login attempts"""
        cache_key = f"failed_logins:{user.id}"
        failed_count = cache.get(cache_key, 0)

        return {
            'detected': failed_count >= 5,
            'risk': min(failed_count * 10, 50),
            'details': f"{failed_count} failed login attempts"
        }

    def _check_login_location(self, user: User, activity_data: Dict) -> Dict:
        """Check for unusual login locations"""
        current_ip = activity_data.get('ip_address')
        if not current_ip:
            return {'detected': False, 'risk': 0, 'details': 'No IP data'}

        # Store last known IPs
        cache_key = f"user_ips:{user.id}"
        known_ips = cache.get(cache_key, set())

        is_new_location = current_ip not in known_ips
        risk = 30 if is_new_location else 0

        if is_new_location and len(known_ips) > 0:
            # Add to known IPs if reasonable
            known_ips.add(current_ip)
            cache.set(cache_key, known_ips, 86400 * 30)  # 30 days

        return {
            'detected': is_new_location and len(known_ips) > 0,
            'risk': risk,
            'details': f"New login location: {current_ip}"
        }

    def _check_password_changes(self, user: User) -> Dict:
        """Check for rapid password changes"""
        cache_key = f"password_changes:{user.id}"
        changes = cache.get(cache_key, [])

        # Remove old changes (older than 24 hours)
        cutoff = timezone.now() - timedelta(hours=24)
        recent_changes = [c for c in changes if c > cutoff]

        risk = min(len(recent_changes) * 15, 40)

        return {
            'detected': len(recent_changes) >= 3,
            'risk': risk,
            'details': f"{len(recent_changes)} password changes in 24h"
        }

    def _check_access_patterns(self, user: User, activity_data: Dict) -> Dict:
        """Check for unusual access patterns"""
        unusual_hours = activity_data.get('hour', 12) in [1, 2, 3, 4, 5]  # 1-5 AM
        unusual_frequency = activity_data.get('requests_per_minute', 0) > 60

        risk = 0
        details = []

        if unusual_hours:
            risk += 20
            details.append("Access during unusual hours")

        if unusual_frequency:
            risk += 25
            details.append("High request frequency")

        return {
            'detected': risk > 0,
            'risk': risk,
            'details': ', '.join(details)
        }

    def sanitize_input(self, input_data: str) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not input_data:
            return input_data

        # Remove potentially dangerous HTML/script tags
        import bleach
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attrs = {}

        return bleach.clean(input_data, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()

    def validate_file_upload(self, file, allowed_types: List[str] = None, max_size: int = 10 * 1024 * 1024) -> Tuple[bool, str]:
        """Validate file upload security"""
        if not file:
            return False, "No file provided"

        # Check file size
        if file.size > max_size:
            return False, f"File too large (max {max_size} bytes)"

        # Check file type
        if allowed_types:
            file_type = file.content_type
            if file_type not in allowed_types:
                return False, f"File type {file_type} not allowed"

        # Check for malicious content (basic check)
        file_content = file.read()
        file.seek(0)  # Reset file pointer

        # Check for script tags in text files
        if file.content_type.startswith('text/'):
            content_str = file_content.decode('utf-8', errors='ignore')
            if '<script' in content_str.lower():
                return False, "Potentially malicious content detected"

        return True, "File is valid"


class ComplianceService:
    """Service for handling compliance requirements (GDPR, HIPAA, etc.)"""

    def __init__(self):
        self.retention_periods = {
            'user_data': 365 * 7,  # 7 years
            'chat_messages': 365 * 3,  # 3 years
            'analytics': 365 * 2,  # 2 years
            'logs': 365,  # 1 year
        }

    def log_data_access(self, user: User, data_type: str, action: str, details: Dict = None):
        """Log data access for compliance"""
        log_entry = {
            'user_id': user.id,
            'data_type': data_type,
            'action': action,
            'timestamp': timezone.now(),
            'details': details or {}
        }

        logger.info(f"Data access: {action} on {data_type}", extra=log_entry)

    def anonymize_user_data(self, user: User) -> Dict:
        """Anonymize user data for analytics/research"""
        return {
            'user_hash': self.hash_user_identifier(user),
            'age_group': self.get_age_group(user),
            'location_region': self.get_location_region(user),
            'account_age_days': (timezone.now().date() - user.date_joined.date()).days,
            'activity_level': self.get_activity_level(user)
        }

    def hash_user_identifier(self, user: User) -> str:
        """Create a consistent hash for user identification"""
        identifier = f"{user.id}:{user.date_joined.isoformat()}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def get_age_group(self, user: User) -> str:
        """Get anonymized age group"""
        # This would require age field in user model
        return "unknown"  # Placeholder

    def get_location_region(self, user: User) -> str:
        """Get anonymized location region"""
        # This would use IP geolocation or user-provided location
        return "unknown"  # Placeholder

    def get_activity_level(self, user: User) -> str:
        """Get user activity level category"""
        from accounts.models import MoodEntry

        entry_count = MoodEntry.objects.filter(user=user).count()
        if entry_count > 100:
            return "high"
        elif entry_count > 50:
            return "medium"
        elif entry_count > 10:
            return "low"
        else:
            return "very_low"

    def check_data_retention(self) -> List[Dict]:
        """Check for data that should be deleted based on retention policies"""
        expired_data = []

        # Check for old chat messages
        from chat.models import Message
        cutoff_date = timezone.now() - timedelta(days=self.retention_periods['chat_messages'])
        old_messages = Message.objects.filter(timestamp__lt=cutoff_date)

        if old_messages.exists():
            expired_data.append({
                'type': 'chat_messages',
                'count': old_messages.count(),
                'oldest_date': old_messages.order_by('timestamp').first().timestamp
            })

        # Check for old analytics data
        from analytics.models import UserAnalytics
        cutoff_date = timezone.now() - timedelta(days=self.retention_periods['analytics'])
        old_analytics = UserAnalytics.objects.filter(created_at__lt=cutoff_date)

        if old_analytics.exists():
            expired_data.append({
                'type': 'analytics',
                'count': old_analytics.count(),
                'oldest_date': old_analytics.order_by('created_at').first().created_at
            })

        return expired_data

    def export_user_data(self, user: User) -> Dict:
        """Export all user data for GDPR compliance"""
        from accounts.models import MoodEntry, Achievement, Appointment
        from chat.models import Message, Session

        return {
            'user_profile': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined,
                'role': user.role
            },
            'mood_entries': list(MoodEntry.objects.filter(user=user).values()),
            'achievements': list(Achievement.objects.filter(user=user).values()),
            'appointments': list(Appointment.objects.filter(
                Q(counselor=user) | Q(client=user)
            ).values()),
            'chat_messages': list(Message.objects.filter(sender=user).values()),
            'export_date': timezone.now()
        }

    def delete_user_data(self, user: User) -> Dict:
        """Completely delete user data for GDPR compliance"""
        deletion_summary = {
            'user_id': user.id,
            'deletion_date': timezone.now(),
            'deleted_records': {}
        }

        # Delete related data
        from accounts.models import MoodEntry, Achievement, Appointment, VideoCall
        from chat.models import Message, Session, Notification
        from analytics.models import UserAnalytics, MoodAnalytics, ChatAnalytics

        deletion_summary['deleted_records']['mood_entries'] = MoodEntry.objects.filter(user=user).delete()[0]
        deletion_summary['deleted_records']['achievements'] = Achievement.objects.filter(user=user).delete()[0]
        deletion_summary['deleted_records']['appointments'] = Appointment.objects.filter(
            Q(counselor=user) | Q(client=user)
        ).delete()[0]
        deletion_summary['deleted_records']['video_calls'] = VideoCall.objects.filter(host=user).delete()[0]
        deletion_summary['deleted_records']['messages'] = Message.objects.filter(sender=user).delete()[0]
        deletion_summary['deleted_records']['notifications'] = Notification.objects.filter(user=user).delete()[0]
        deletion_summary['deleted_records']['user_analytics'] = UserAnalytics.objects.filter(user=user).delete()[0]
        deletion_summary['deleted_records']['mood_analytics'] = MoodAnalytics.objects.filter(user=user).delete()[0]
        deletion_summary['deleted_records']['chat_analytics'] = ChatAnalytics.objects.filter(user=user).delete()[0]

        # Finally delete the user
        user.delete()

        return deletion_summary


class AuditService:
    """Service for audit logging and compliance tracking"""

    def __init__(self):
        self.audit_log = logging.getLogger('audit')

    def log_audit_event(self, event_type: str, user: Optional[User],
                        resource: str, action: str, details: Dict = None):
        """Log audit events for compliance"""
        audit_entry = {
            'event_type': event_type,
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'user_email': user.email if user and hasattr(user, 'email') else None,
            'resource': resource,
            'action': action,
            'timestamp': timezone.now(),
            'details': details or {},
            'ip_address': details.get('ip_address') if details else None,
            'user_agent': details.get('user_agent') if details else None
        }

        self.audit_log.info(f"AUDIT: {event_type} - {action} on {resource}", extra=audit_entry)

    def get_audit_trail(self, user: Optional[User] = None, resource: str = None,
                       start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Retrieve audit trail for compliance reporting"""
        # In a real implementation, this would query an audit log database
        # For now, return a placeholder
        return [{
            'event_type': 'sample_event',
            'user_id': user.id if user else None,
            'resource': resource or 'system',
            'action': 'access',
            'timestamp': timezone.now(),
            'details': {'sample': True}
        }]

    def generate_compliance_report(self, report_type: str, start_date: datetime,
                                 end_date: datetime) -> Dict:
        """Generate compliance reports"""
        if report_type == 'access_log':
            return {
                'report_type': 'access_log',
                'period': f"{start_date.date()} to {end_date.date()}",
                'total_events': 0,
                'summary': 'Access log report generated'
            }
        elif report_type == 'data_retention':
            compliance_service = ComplianceService()
            expired_data = compliance_service.check_data_retention()

            return {
                'report_type': 'data_retention',
                'period': f"{start_date.date()} to {end_date.date()}",
                'expired_data': expired_data,
                'recommendations': [
                    'Review and delete expired chat messages',
                    'Archive old analytics data',
                    'Update retention policies as needed'
                ]
            }

        return {'error': 'Unknown report type'}