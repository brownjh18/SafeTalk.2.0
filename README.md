# SafeTalk - Mental Health Support Platform

SafeTalk is a comprehensive mental health support platform that provides real-time chat, counseling services, mood tracking, and community support features. Built with Django and modern web technologies, it offers a secure and user-friendly environment for mental health support.

## Features

### Core Functionality
- **Real-time Chat**: WebSocket-based instant messaging between users
- **Counseling Appointments**: Schedule and manage counseling sessions
- **Mood Tracking**: Daily mood logging with analytics and insights
- **AI Companion**: Rule-based AI support for mental health guidance
- **Community Groups**: Support groups with different categories
- **Goal Setting**: Personal goal tracking and progress monitoring
- **Achievements System**: Gamification elements to encourage engagement

### Security & Privacy
- **End-to-end Encryption**: Message encryption using RSA+AES
- **Two-Factor Authentication**: Enhanced security with 2FA
- **User Blocking**: Control over interactions
- **Anonymous Chat**: Privacy-focused chat rooms
- **Session Management**: Secure session handling

### Subscription System
- **Multiple Plans**: Basic, Classic, and Premium tiers
- **Stripe Integration**: Secure payment processing
- **Subscription Management**: Easy plan changes and cancellations

### Administrative Features
- **User Management**: Admin panel for user oversight
- **Analytics Dashboard**: Comprehensive platform analytics
- **Content Management**: Resource and group management
- **Payment Tracking**: Invoice and payment management

## Technology Stack

- **Backend**: Django 4.2, Python 3.13
- **Real-time**: Django Channels, WebSockets
- **Database**: PostgreSQL (production), SQLite (development)
- **Cache**: Redis
- **Payments**: Stripe
- **Authentication**: Django auth + django-two-factor-auth
- **Encryption**: Cryptography library
- **Deployment**: Docker, Nginx, Gunicorn

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/safetalk.git
   cd safetalk
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Deploy with Docker**
   ```bash
   # For development
   ./deploy.sh

   # For production
   ./deploy.sh production
   ```

4. **Access the Application**
   - Web App: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin/
   - Health Check: http://localhost:8000/health/

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=safetalk
DB_USER=safetalk_user
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## API Documentation

Complete API documentation is available in `api_docs.md`, including:
- Authentication endpoints
- Chat and messaging APIs
- User management
- Subscription management
- WebSocket protocols

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest tests/test_accounts.py::UserModelTest::test_user_creation -v

# Run with coverage
python -m pytest --cov=safetalk --cov-report=html
```

## Deployment

### Development
```bash
docker-compose up --build
```

### Production
```bash
./deploy.sh production
```

### Manual Deployment

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

4. Start server:
   ```bash
   # Development
   python manage.py runserver

   # Production
   gunicorn safetalk.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```

## Monitoring

### Health Checks
- `/health/` - Basic health check
- `/status/` - System status with database/cache health
- `/metrics/` - Performance metrics (staff only)

### Logging
- Error logs: `logs/django_error.log`
- Console logging with configurable levels
- Performance monitoring middleware

## Security

SafeTalk implements multiple security layers:
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting
- Security headers (CSP, HSTS, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: support@safetalk.com
- Documentation: https://docs.safetalk.com
- Issues: GitHub Issues

## Roadmap

### Upcoming Features
- Mobile app (React Native)
- Video calling integration
- Advanced analytics
- Third-party integrations
- Multi-language support
- Advanced AI features

### Version History
- **v1.0.0**: Initial release with core features
- Comprehensive mental health platform
- Real-time messaging and counseling
- Subscription management
- Security and privacy features

---

**SafeTalk** - Supporting mental health through technology and community.# SafeTalk.
# SafeTalk.2.0
