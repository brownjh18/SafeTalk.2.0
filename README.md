# SafeTalk 2.0 - Advanced Mental Health Support Platform

![SafeTalk Logo](https://img.shields.io/badge/SafeTalk-2.0-4f46e5?style=for-the-badge&logo=django)
![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=flat&logo=django)
![Python](https://img.shields.io/badge/Python-3.13-3776ab?style=flat&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)

SafeTalk 2.0 is a comprehensive, modern mental health support platform featuring real-time messaging, AI-powered support, counseling services, and community features. Built with Django and cutting-edge web technologies, it provides a secure, accessible, and user-friendly environment for mental health support.

## 🏗️ Environment-Based Configuration

SafeTalk 2.0 uses a modular settings structure that separates development and production configurations:

### Settings Structure
```
safetalk/settings/
├── __init__.py
├── base.py          # Shared settings for all environments
├── development.py   # Development-specific settings
└── production.py    # Production-specific settings
```

### Environment Selection
The application automatically selects settings based on the `DJANGO_ENV` environment variable:
- `DJANGO_ENV=development` → Uses `development.py`
- `DJANGO_ENV=production` → Uses `production.py`
- Default: `development`

### Quick Setup
```bash
# Development
cp .env.development .env
python manage.py runserver

# Production
cp .env.production .env
DJANGO_ENV=production python manage.py runserver
```

## 🌟 Key Features

### 💬 **Advanced Messaging System**
- **Real-time Chat**: WebSocket-based instant messaging with presence indicators
- **File Attachments**: Support for documents, images, and media files
- **Message Encryption**: End-to-end encryption for privacy
- **Notification System**: Real-time notifications with customizable badges
- **Conversation Management**: Archive, mute, and organize conversations

### 🤖 **AI-Powered Support**
- **AI Companion**: Advanced rule-based AI for mental health guidance
- **Sentiment Analysis**: Real-time mood detection and analysis
- **Personalized Recommendations**: AI-driven resource suggestions
- **24/7 Availability**: Always-on AI support for immediate assistance

### 📅 **Professional Counseling**
- **Appointment Management**: Schedule and manage counseling sessions
- **Calendar Integration**: Visual calendar with appointment tracking
- **Counselor Matching**: Intelligent counselor-client pairing
- **Session Notes**: Secure note-taking and progress tracking
- **Video Calling**: Integrated video consultation features

### 📊 **Comprehensive Analytics**
- **Mood Tracking**: Advanced mood logging with trend analysis
- **Progress Monitoring**: Visual progress charts and insights
- **Goal Setting**: Personal goal tracking with achievement system
- **Mental Health Metrics**: Comprehensive wellness indicators
- **Export Capabilities**: Data export for personal records

### 🔒 **Security & Privacy**
- **End-to-End Encryption**: Military-grade message encryption
- **Two-Factor Authentication**: Enhanced security with 2FA/TOTP
- **GDPR Compliance**: Full data protection compliance
- **Anonymous Options**: Privacy-focused communication channels
- **Data Export**: Complete data portability options

### 💳 **Subscription Management**
- **Flexible Plans**: Basic, Classic, and Premium subscription tiers
- **Stripe Integration**: Secure payment processing
- **Usage Analytics**: Detailed usage and engagement metrics
- **Plan Management**: Easy upgrades, downgrades, and cancellations

## 🛠 Technology Stack

### Backend & Core
- **Framework**: Django 4.2.7 with Python 3.13
- **Real-time**: Django Channels with WebSocket support
- **Database**: PostgreSQL 15 (production) / SQLite (development)
- **Cache**: Redis 5.0 with django-redis
- **Task Queue**: Celery 5.3.4 with Redis broker

### Security & Authentication
- **Encryption**: Cryptography library with RSA+AES
- **2FA**: django-two-factor-auth with TOTP support
- **Sessions**: Secure session management with rotation
- **Headers**: Comprehensive security headers (CSP, HSTS, etc.)

### Machine Learning & AI
- **ML Models**: scikit-learn, TensorFlow, PyTorch
- **NLP**: Transformers, NLTK for sentiment analysis
- **Analytics**: Pandas, NumPy, Matplotlib for insights
- **AI Models**: Custom-trained models for mental health support

### Frontend & UI
- **Templates**: Modern Django templates with responsive design
- **Styling**: Custom CSS with gradient effects and animations
- **JavaScript**: Vanilla JS with modern ES6+ features
- **Icons**: Custom emoji-based icon system
- **Themes**: Light/dark theme support

### DevOps & Deployment
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for development
- **Web Server**: Nginx with Gunicorn WSGI
- **Monitoring**: Health checks and performance metrics
- **CI/CD**: Automated deployment pipeline

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (recommended)
- **Git** for version control
- **Python 3.13** (for local development)

### Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/brownjh18/SafeTalk.2.0.git
   cd SafeTalk.2.0
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Deploy with Docker (Recommended)**
   ```bash
   # Development deployment
   ./deploy.sh

   # Production deployment
   ./deploy.sh production
   ```

4. **Manual Installation**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt

   # Run database migrations
   python manage.py migrate

   # Collect static files
   python manage.py collectstatic --noinput

   # Create superuser (optional)
   python manage.py createsuperuser
   ```

5. **Start the Application**
   ```bash
   # Development
   python manage.py runserver

   # Production
   gunicorn safetalk.wsgi:application --bind 0.0.0.0:8000 --workers 4
   ```

6. **Access the Platform**
   - **Web Application**: http://localhost:8000
   - **Admin Panel**: http://localhost:8000/admin/
   - **API Health Check**: http://localhost:8000/health/
   - **System Status**: http://localhost:8000/status/

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following:

```bash
# Django Configuration
SECRET_KEY=your-super-secret-key-here-generate-with-django-secret-key-generator
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost,127.0.0.1

# Database Configuration
DB_NAME=safetalk_db
DB_USER=safetalk_user
DB_PASSWORD=secure-database-password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/1
CACHE_URL=redis://localhost:6379/1

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Stripe Payment Configuration
STRIPE_PUBLIC_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Additional Configuration Files
- **nginx.conf**: Nginx configuration for production deployment
- **docker-compose.yml**: Docker services configuration
- **pytest.ini**: Testing configuration
- **requirements.txt**: Python dependencies

## 📚 API Documentation

Complete API documentation is available in `api_docs.md`, including:

### Core Endpoints
- **Authentication**: `/api/auth/` - Login, registration, 2FA
- **Messaging**: `/api/messaging/` - Real-time chat and conversations
- **Appointments**: `/api/appointments/` - Session management
- **Resources**: `/api/resources/` - Mental health resources
- **Analytics**: `/api/analytics/` - Usage and progress metrics

### WebSocket Protocols
- **Chat Rooms**: Real-time messaging channels
- **Presence**: User online/offline status
- **Notifications**: Live notification delivery

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python -m pytest

# Run specific test module
python -m pytest tests/test_accounts.py -v

# Run with coverage report
python -m pytest --cov=safetalk --cov-report=html --cov-report=term

# Run specific test
python -m pytest tests/test_accounts.py::UserModelTest::test_user_creation -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and stress testing

## 🚢 Deployment

### Development Environment
```bash
# Using Docker Compose
docker-compose up --build

# Using deployment script
./deploy.sh
```

### Production Environment
```bash
# Full production deployment
./deploy.sh production

# Manual production setup
docker-compose -f docker-compose.production.yml up --build -d
```

### Deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificates installed
- [ ] Domain DNS configured
- [ ] Health checks passing
- [ ] Monitoring configured

## 📊 Monitoring & Health Checks

### Health Endpoints
- **Basic Health**: `GET /health/` - Application status
- **System Status**: `GET /status/` - Database, cache, services
- **Performance Metrics**: `GET /metrics/` - Response times, usage stats
- **Error Logs**: `GET /logs/` - Recent error logs (admin only)

### Monitoring Features
- **Real-time Metrics**: Performance monitoring dashboard
- **Error Tracking**: Automated error logging and alerting
- **Usage Analytics**: User engagement and feature usage
- **Security Monitoring**: Failed login attempts and suspicious activity

## 🔐 Security Features

### Authentication & Authorization
- **Multi-factor Authentication**: TOTP-based 2FA
- **Session Security**: Secure session management with rotation
- **Password Policies**: Strong password requirements
- **Account Lockout**: Brute force protection

### Data Protection
- **Encryption at Rest**: Database encryption
- **Encryption in Transit**: TLS 1.3 for all communications
- **Message Encryption**: End-to-end encryption for sensitive data
- **Data Anonymization**: Privacy-preserving data handling

### Compliance
- **GDPR Ready**: Full data protection compliance
- **HIPAA Considerations**: Healthcare data handling
- **Data Export**: Complete data portability
- **Right to Erasure**: Data deletion capabilities

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with proper tests
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Code Standards
- **PEP 8**: Python code style compliance
- **ESLint**: JavaScript code quality
- **Prettier**: Code formatting
- **Conventional Commits**: Commit message standards

### Testing Requirements
- **Unit Tests**: Required for all new features
- **Integration Tests**: API endpoint coverage
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load testing for critical paths

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Documentation

### Getting Help
- **📧 Email**: support@safetalk.com
- **📚 Documentation**: https://docs.safetalk.com
- **💬 Discord**: [SafeTalk Community](https://discord.gg/safetalk)
- **🐛 Issues**: [GitHub Issues](https://github.com/brownjh18/SafeTalk.2.0/issues)

### Resources
- **API Documentation**: `api_docs.md`
- **Deployment Guide**: `deploy.sh` and `docker-compose.yml`
- **Configuration Guide**: `.env.example`
- **Development Guide**: `CONTRIBUTING.md`

## 🗺️ Roadmap

### Current Version (v2.0.0)
- ✅ **Real-time messaging** with file attachments
- ✅ **Advanced notification system** with badges
- ✅ **Modern dashboard design** with premium UI
- ✅ **Comprehensive appointment management**
- ✅ **Enhanced resource library**
- ✅ **AI-powered support features**

### Upcoming Features (v2.1.0)
- 🔄 **Mobile app** (React Native)
- 📹 **Video calling integration** with WebRTC
- 🤝 **Peer support groups** with moderation
- 📱 **Progressive Web App** (PWA) features
- 🌍 **Multi-language support** (i18n)
- 📊 **Advanced analytics dashboard**
- 🔗 **Third-party integrations** (calendar, fitness apps)

### Future Vision (v3.0.0)
- 🧠 **Advanced AI therapy** with ML models
- 👥 **Community-driven content** and resources
- 📱 **Cross-platform mobile apps**
- 🔬 **Research partnerships** with mental health organizations
- 🌐 **Global expansion** with localized content

## 📈 Version History

### **v2.0.0** (Current)
- Complete UI/UX redesign with modern dashboard
- Enhanced messaging system with notifications
- Advanced appointment management system
- Comprehensive resource library
- Premium design with animations and effects
- Full mobile responsiveness

### **v1.0.0** (Previous)
- Basic mental health platform
- Core messaging functionality
- Simple appointment scheduling
- Basic resource management
- Standard Django admin interface

---

## 🙏 Acknowledgments

SafeTalk 2.0 represents a significant advancement in digital mental health support, combining cutting-edge technology with compassionate care. We extend our gratitude to:

- **Mental Health Professionals** for their clinical guidance
- **Open Source Community** for incredible tools and libraries
- **Beta Testers** for valuable feedback and suggestions
- **Contributors** for their time and expertise

---

**🛡️ SafeTalk 2.0** - *Empowering mental health through technology, community, and compassionate care.*

*Built with ❤️ for mental health support worldwide.*

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
   git clone https://github.com/brownjh18/SafeTalk.2.0.git
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
#   S a f e T a l k . 2 . 0 
 
 #   S a f e T a l k . 2 . 0 
 
 