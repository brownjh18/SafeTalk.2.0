# SafeTalk API Documentation

## Overview
SafeTalk is a comprehensive mental health support platform that provides real-time chat, counseling services, mood tracking, and community support features.

## Authentication
All API endpoints require authentication except for health check endpoints.

### Authentication Methods
- Session-based authentication (Django sessions)
- Two-factor authentication (2FA) support
- API tokens for external integrations

## Core API Endpoints

### Health & Monitoring

#### Health Check
```
GET /health/
```
Returns basic health status of the application.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-10-13T06:00:00.000Z",
    "version": "1.0.0"
}
```

#### System Status
```
GET /status/
```
Returns detailed system status including database and cache health.

**Response:**
```json
{
    "status": "healthy",
    "database": "healthy",
    "cache": "healthy",
    "timestamp": "2025-10-13T06:00:00.000Z"
}
```

#### Performance Metrics
```
GET /metrics/
```
Returns performance metrics for monitoring (staff only).

**Response:**
```json
{
    "metrics": {
        "/chat/dashboard/": {
            "average_duration_ms": 245.67,
            "request_count": 150,
            "last_request": "2025-10-13T06:00:00.000Z"
        }
    },
    "timestamp": "2025-10-13T06:00:00.000Z"
}
```

### User Management

#### User Registration
```
POST /register/
```
Register a new user account.

**Request Body:**
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "password1": "securepassword123",
    "password2": "securepassword123",
    "role": "client"
}
```

#### User Login
```
POST /login/
```
Authenticate user and create session.

**Request Body:**
```json
{
    "username": "johndoe",
    "password": "securepassword123"
}
```

#### User Profile
```
GET /profile/
```
Get current user's profile information.

**Response:**
```json
{
    "username": "johndoe",
    "email": "john@example.com",
    "role": "client",
    "total_appointments": 5,
    "completed_appointments": 3,
    "goals_set": 8,
    "goals_completed": 5
}
```

### Chat System

#### Get Messages
```
GET /chat/messages/
```
Get paginated list of user's messages.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)

**Response:**
```json
{
    "messages": [
        {
            "id": 1,
            "sender": "johndoe",
            "content": "Hello, how are you?",
            "timestamp": "2025-10-13T06:00:00.000Z",
            "status": "read"
        }
    ],
    "total_pages": 5,
    "current_page": 1
}
```

#### Send Message
```
POST /chat/session/{session_id}/
```
Send a message in a chat session.

**Request Body:**
```json
{
    "content": "Hello, I need some support today.",
    "message_type": "text"
}
```

#### Start Chat
```
GET /chat/start-chat/{user_id}/
```
Start a new chat session with another user.

**Response:**
```json
{
    "session_id": 123,
    "redirect_url": "/chat/session/123/"
}
```

### Mood Tracking

#### Log Mood
```
POST /log-mood/
```
Log daily mood entry.

**Request Body:**
```json
{
    "mood": "happy",
    "note": "Feeling good after exercise"
}
```

#### Mood History
```
GET /mood-history/
```
Get user's mood history with analytics.

**Response:**
```json
{
    "mood_entries": [
        {
            "date": "2025-10-13",
            "mood": "happy",
            "note": "Great day!"
        }
    ],
    "mood_counts": {
        "happy": 15,
        "sad": 3,
        "anxious": 5
    },
    "current_streak": 7
}
```

### Appointments

#### Book Appointment
```
POST /chat/book-appointment/
```
Book a counseling appointment.

**Request Body:**
```json
{
    "counselor_id": 5,
    "title": "Initial Consultation",
    "description": "First meeting to discuss concerns",
    "scheduled_date": "2025-10-20T14:00:00Z",
    "duration_minutes": 60
}
```

#### Get Appointments
```
GET /chat/appointments/
```
Get user's appointments.

**Response:**
```json
{
    "upcoming_appointments": [
        {
            "id": 10,
            "counselor": "Dr. Smith",
            "title": "Follow-up Session",
            "scheduled_date": "2025-10-20T14:00:00Z",
            "status": "confirmed"
        }
    ],
    "past_appointments": [...]
}
```

### Goals & Progress

#### Set Goal
```
POST /chat/progress/
```
Create a new goal.

**Request Body:**
```json
{
    "title": "Exercise regularly",
    "description": "Exercise 3 times per week",
    "target_date": "2025-12-31"
}
```

#### Update Progress
```
POST /chat/progress/{goal_id}/
```
Update progress on a goal.

**Request Body:**
```json
{
    "content": "Completed 3 workouts this week",
    "mood_rating": 8
}
```

### Notifications

#### Get Unread Notifications
```
GET /chat/api/notifications/unread/
```
Get unread notifications with polling.

**Query Parameters:**
- `last_id`: Last notification ID received

**Response:**
```json
{
    "notifications": [
        {
            "id": 45,
            "title": "New Message",
            "message": "You have a new message from john",
            "notification_type": "message",
            "created_at": "2025-10-13T06:00:00.000Z",
            "related_id": 123
        }
    ],
    "count": 1
}
```

#### Mark Notification Read
```
POST /chat/mark-notification-read/{notification_id}/
```
Mark a notification as read.

### Subscription Management

#### View Plans
```
GET /subscriptions/
```
Get available subscription plans.

**Response:**
```json
{
    "plans": [
        {
            "id": 1,
            "name": "basic",
            "display_name": "Basic Plan",
            "description": "Essential features",
            "price_monthly": 9.99,
            "features": ["Chat", "Mood Tracking", "Basic Support"]
        }
    ]
}
```

#### Subscribe
```
POST /subscribe/{plan_name}/
```
Subscribe to a plan (requires payment processing).

**Request Body:**
```json
{
    "payment_method_id": "pm_1234567890"
}
```

### AI Companion

#### Send AI Message
```
POST /chat/ai/{conversation_id}/send/
```
Send message to AI companion.

**Request Body:**
```json
{
    "message": "I'm feeling anxious today"
}
```

**Response:**
```json
{
    "success": true,
    "ai_message": {
        "user_message": "I'm feeling anxious today",
        "ai_response": "I understand anxiety can be overwhelming...",
        "keywords_detected": ["anxiety"],
        "created_at": "2025-10-13T06:00:00.000Z"
    }
}
```

### Group Features

#### List Groups
```
GET /chat/groups/
```
Get available support groups.

**Response:**
```json
{
    "groups": [
        {
            "id": 1,
            "name": "Anxiety Support",
            "description": "Support group for anxiety",
            "category": "support",
            "member_count": 25
        }
    ]
}
```

#### Join Group
```
POST /chat/groups/{group_id}/join/
```
Join a support group.

#### Send Group Message
```
POST /chat/groups/{group_id}/chat/
```
Send message to group chat.

**Request Body:**
```json
{
    "message": "Hello everyone, thanks for the support"
}
```

### WebSocket API

#### Chat WebSocket
```
WebSocket: ws://localhost:8000/ws/chat/{session_id}/
```
Real-time chat communication.

**Message Types:**
- `message`: New chat message
- `typing`: Typing indicator
- `reaction`: Message reaction

**Example Message:**
```json
{
    "type": "message",
    "content": "Hello!",
    "message_type": "text"
}
```

### Error Handling

All API endpoints return appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

Error responses include:
```json
{
    "error": "Description of the error",
    "timestamp": "2025-10-13T06:00:00.000Z"
}
```

### Rate Limiting

API endpoints are rate limited to prevent abuse:
- General endpoints: 100 requests per minute
- Chat endpoints: 500 requests per minute
- Authentication endpoints: 10 requests per minute

### Data Export

#### Export Mood Data
```
GET /export-mood-data/
```
Export user's mood data as CSV.

**Response:** CSV file download

### Security Features

- End-to-end encryption for messages
- Two-factor authentication support
- Session management with automatic cleanup
- Input validation and sanitization
- SQL injection prevention
- XSS protection

### Pagination

List endpoints support pagination:
```
GET /chat/messages/?page=2&per_page=10
```

**Response includes:**
```json
{
    "results": [...],
    "total_pages": 5,
    "current_page": 2,
    "has_next": true,
    "has_previous": true
}
```

### Versioning

API versioning is handled through URL paths:
- Current version: v1 (default)
- Future versions: `/api/v2/endpoint/`

### Support

For API support or questions:
- Email: support@safetalk.com
- Documentation: https://docs.safetalk.com
- Status Page: https://status.safetalk.com