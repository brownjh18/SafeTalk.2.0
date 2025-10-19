import logging
import time
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.core.cache import cache
from safetalk.security import SecurityService

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Middleware for security enhancements"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.security_service = SecurityService()

        # URLs that should be protected
        self.protected_urls = [
            '/admin/',
            '/accounts/',
            '/chat/',
            '/analytics/',
        ]

        # URLs that allow file uploads
        self.upload_urls = [
            '/chat/upload/',
            '/accounts/upload/',
        ]

    def __call__(self, request):
        # Start timing for performance monitoring
        start_time = time.time()

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Store in request for later use
        request.client_ip = client_ip
        request.user_agent = user_agent

        # Security checks
        if not self._perform_security_checks(request):
            return HttpResponseForbidden("Access denied")

        # Rate limiting
        if not self._check_rate_limits(request):
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)

        # Log security events for protected URLs
        if any(url in request.path for url in self.protected_urls):
            self._log_access_attempt(request)

        # File upload validation
        if request.method == 'POST' and any(url in request.path for url in self.upload_urls):
            if not self._validate_file_upload(request):
                return JsonResponse({'error': 'Invalid file upload'}, status=400)

        response = self.get_response(request)

        # Add security headers
        self._add_security_headers(response)

        # Performance monitoring
        duration = time.time() - start_time
        if duration > 1.0:  # Log slow requests
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s")

        return response

    def _get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _perform_security_checks(self, request):
        """Perform basic security checks"""
        # Check for suspicious patterns in URL
        suspicious_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
        if any(pattern in request.path.lower() for pattern in suspicious_patterns):
            logger.warning(f"Suspicious URL pattern detected: {request.path}")
            return False

        # Check for SQL injection attempts
        sql_patterns = ['union select', 'information_schema', 'script>', 'iframe']
        query_string = request.META.get('QUERY_STRING', '').lower()
        if any(pattern in query_string for pattern in sql_patterns):
            logger.warning(f"Potential SQL injection attempt: {query_string}")
            return False

        return True

    def _check_rate_limits(self, request):
        """Check rate limits for requests"""
        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
        else:
            identifier = f"ip:{request.client_ip}"

        # Different limits for different types of requests
        if request.path.startswith('/api/'):
            return self.security_service.check_rate_limit(identifier, 'api', limit=100, window=60)
        elif request.method == 'POST':
            return self.security_service.check_rate_limit(identifier, 'post', limit=20, window=60)
        else:
            return self.security_service.check_rate_limit(identifier, 'general', limit=200, window=60)

    def _log_access_attempt(self, request):
        """Log access attempts to protected resources"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.security_service.log_security_event(
                'protected_access',
                request.user,
                {
                    'path': request.path,
                    'method': request.method,
                    'ip_address': request.client_ip,
                    'user_agent': request.user_agent
                }
            )

    def _validate_file_upload(self, request):
        """Validate file uploads"""
        for file_key in request.FILES:
            uploaded_file = request.FILES[file_key]

            # Basic validation
            is_valid, error_msg = self.security_service.validate_file_upload(
                uploaded_file,
                allowed_types=['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain'],
                max_size=10 * 1024 * 1024  # 10MB
            )

            if not is_valid:
                logger.warning(f"Invalid file upload: {error_msg}")
                return False

        return True

    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy (basic)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:;"
        )
        response['Content-Security-Policy'] = csp

        # HSTS (HTTP Strict Transport Security)
        if getattr(settings, 'SECURE_SSL_REDIRECT', False):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'


class AuditMiddleware:
    """Middleware for audit logging"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request data for audit logging
        request.audit_data = {
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }

        response = self.get_response(request)

        # Log significant events
        if self._should_audit(request, response):
            self._log_audit_event(request, response)

        return response

    def _should_audit(self, request, response):
        """Determine if request should be audited"""
        # Audit failed authentications
        if response.status_code in [401, 403]:
            return True

        # Audit admin actions
        if request.path.startswith('/admin/'):
            return True

        # Audit data modifications
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return True

        # Audit sensitive data access
        sensitive_paths = ['/accounts/', '/analytics/', '/admin/']
        if any(path in request.path for path in sensitive_paths):
            return True

        return False

    def _log_audit_event(self, request, response):
        """Log audit event"""
        from safetalk.security import AuditService

        audit_service = AuditService()

        event_type = 'api_access' if request.path.startswith('/api/') else 'page_access'

        audit_service.log_audit_event(
            event_type=event_type,
            user=getattr(request, 'user', None),
            resource=request.path,
            action=f"{request.method} ({response.status_code})",
            details={
                'status_code': response.status_code,
                'query_string': request.audit_data['query_string'],
                'user_agent': request.audit_data['user_agent'],
                'ip_address': getattr(request, 'client_ip', None),
            }
        )


class ComplianceMiddleware:
    """Middleware for compliance requirements"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for GDPR consent
        if request.user.is_authenticated:
            self._check_gdpr_consent(request)

        response = self.get_response(request)

        # Add compliance headers
        self._add_compliance_headers(response)

        return response

    def _check_gdpr_consent(self, request):
        """Check GDPR consent status"""
        # This would check if user has given consent for data processing
        # For now, just log the access
        from safetalk.security import ComplianceService

        compliance_service = ComplianceService()
        compliance_service.log_data_access(
            request.user,
            'user_profile',
            'access',
            {
                'path': request.path,
                'ip_address': getattr(request, 'client_ip', None)
            }
        )

    def _add_compliance_headers(self, response):
        """Add compliance-related headers"""
        # GDPR compliance
        response['X-GDPR-Compliant'] = 'true'

        # Data processing location
        response['X-Data-Processing-Location'] = 'EU'  # Adjust based on actual location

        # Contact information for data protection
        response['X-Data-Protection-Contact'] = 'privacy@safetalk.com'


class PerformanceMiddleware:
    """Middleware for performance monitoring"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # Log performance metrics
        self._log_performance_metrics(request, response, duration)

        # Add performance header
        response['X-Response-Time'] = f"{duration:.3f}s"

        return response

    def _log_performance_metrics(self, request, response, duration):
        """Log performance metrics"""
        if duration > 2.0:  # Log slow requests
            logger.warning(
                f"Slow request detected: {request.path} "
                f"took {duration:.3f}s (status: {response.status_code})"
            )

        # Store metrics for analytics
        metrics_key = f"perf:{request.path}:{timezone.now().strftime('%Y%m%d%H')}"
        current_avg = cache.get(metrics_key, {'count': 0, 'total_time': 0.0})

        current_avg['count'] += 1
        current_avg['total_time'] += duration

        cache.set(metrics_key, current_avg, 3600)  # Store for 1 hour


class MaintenanceMiddleware:
    """Middleware for maintenance mode"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        maintenance_mode = cache.get('maintenance_mode', False)

        if maintenance_mode and not request.path.startswith('/admin/'):
            # Allow access to maintenance page or for staff
            if hasattr(request, 'user') and request.user.is_staff:
                pass  # Allow staff access
            else:
                return self._maintenance_response()

        return self.get_response(request)

    def _maintenance_response(self):
        """Return maintenance mode response"""
        return JsonResponse({
            'error': 'Service temporarily unavailable',
            'message': 'SafeTalk is currently undergoing maintenance. Please try again later.',
            'estimated_downtime': '30 minutes'
        }, status=503)


class CORSHeadersMiddleware:
    """Middleware for CORS headers (for API access)"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', ['http://localhost:3000'])

    def __call__(self, request):
        response = self.get_response(request)

        # Add CORS headers for API requests
        if request.path.startswith('/api/'):
            origin = request.META.get('HTTP_ORIGIN')
            if origin in self.allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
                response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        return response