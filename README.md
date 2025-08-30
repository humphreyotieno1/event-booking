# Event Booking & Attendance API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive **Event Booking & Attendance Management System** built with Django REST Framework, featuring role-based access control, real-time analytics, and external event integration.

## 🚀 **Quick Start**

```bash
# Clone and setup
git clone https://github.com/yourusername/event-booking.git
cd event-booking
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install and configure
pip install -r requirements.txt
./env_switch.sh development  # Sets up development environment
python manage.py migrate
python manage.py createsuperuser

# Start services
python manage.py runserver
# Access: http://127.0.0.1:8000/api/docs/
```

## 🎯 **Key Features**

- **🔐 Role-Based Access Control**: Public, Authenticated, Organizer, and Admin levels
- **📊 Real-time Analytics**: Comprehensive dashboards for organizers and admins
- **🌍 External Integration**: Ticketmaster, SeatGeek, and more event platforms
- **📱 RESTful API**: Clean, documented API with Swagger/OpenAPI
- **🚀 Performance**: Redis caching, Celery tasks, and optimized queries

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Booking System                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React/Vue)  │  Mobile Apps  │  Third-party    │
├─────────────────────────────────────────────────────────────┤
│                    Django REST API                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   Events   │   Accounts  │    RSVP     │  External   │  │
│  │     App    │     App     │     App     │   Events    │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Celery  │  RabbitMQ  │  Storage  │
└─────────────────────────────────────────────────────────────┘
```

## 🔌 **API Endpoints**

### **Base URL**: `/api/`

The API is organized into four distinct access levels:

#### **🌐 Public Endpoints (No Authentication)**
- `GET /events/` - List all events
- `GET /events/{id}/` - Get event details
- `GET /categories/` - List event categories
- `GET /tags/` - List event tags

#### **🔐 Authenticated User Endpoints (Login Required)**
- `GET /events/{id}/attendees/` - Get event attendees
- `GET /events/{id}/rsvp_status/` - Check RSVP status
- `GET /events/{id}/stats/` - Get event statistics
- `POST /rsvp/events/{id}/rsvp/` - RSVP to events
- `GET /accounts/profile/` - User profile management

#### **🎯 Organizer Endpoints (Organizer Role Required)**
- `POST /events/` - Create new events
- `PUT /events/{id}/` - Update own events
- `GET /organizer/events/organizer_dashboard/` - Organizer dashboard
- `GET /organizer/events/event_analytics/` - Event analytics

#### **👑 Admin Endpoints (Staff/Superuser Required)**
- `GET /admin/events/dashboard_stats/` - System analytics
- `GET /admin/events/user_analytics/` - User analytics
- `POST /admin/categories/` - Manage categories
- `POST /admin/tags/` - Manage tags

## 📚 **Documentation**

- **[Main API Documentation](http://localhost:8000/api/docs/)** - Interactive Swagger UI
- **[ReDoc Documentation](http://localhost:8000/api/redoc/)** - Alternative API docs
- **[Events App](events/README.md)** - Core event management
- **[Accounts App](accounts/README.md)** - User authentication & management
- **[RSVP App](rsvp/README.md)** - Attendance management
- **[External Events App](external_events/README.md)** - External API integration


### **Environment Variables (.env)**
```env
   DEBUG=True
   SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/event_booking
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### **Database & Services**
```bash
# Start PostgreSQL, Redis, RabbitMQ
# Then run:
   python manage.py migrate
python manage.py createsuperuser

# Start Celery (optional)
celery -A app worker -l info
celery -A app beat -l info
```

## 💻 **Usage Examples**

### **Python Client**
```python
import requests

# Register and login
response = requests.post('http://localhost:8000/api/accounts/register/', {
    'username': 'john_doe',
    'email': 'john@example.com',
    'password': 'securepass123'
})

# Login to get token
response = requests.post('http://localhost:8000/api/accounts/login/', {
    'username': 'john_doe',
    'password': 'securepass123'
})
token = response.json()['tokens']['access']

# Create event (organizer only)
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:8000/api/events/', {
    'title': 'Tech Meetup 2024',
    'description': 'Join us for tech talks',
    'location': 'Tech Hub, Downtown',
    'start_time': '2024-12-31T18:00:00Z'
}, headers=headers)
```

### **cURL Examples**
```bash
# Register user
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"securepass123"}'

# Login
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","password":"securepass123"}'

# Create event (with token)
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Tech Meetup","description":"Awesome tech event","location":"Tech Hub","start_time":"2024-12-31T18:00:00Z"}'
```

## 🧪 **Testing**

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test events
python manage.py test accounts
python manage.py test rsvp
python manage.py test external_events

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 **Deployment**

### **Production Settings**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
```

### **Docker Deployment**
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/event_booking
    depends_on: [db, redis, rabbitmq]
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=event_booking
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
```

## 🔐 **Access Control System**

The system implements sophisticated role-based access control:

- **Public Users**: Basic event browsing and discovery
- **Authenticated Users**: Personal event management and RSVP operations
- **Organizers**: Event creation, management, and analytics for their events
- **Administrators**: Full system administration and analytics

### **Permission Classes**
- `IsOrganizerOrReadOnly` - Controls event creation access
- `IsEventOwnerOrReadOnly` - Controls event modification access
- `IsAdminUser` - Restricts access to admin users only
- `IsOrganizer` - Restricts access to organizer users only

## 📊 **Performance Features**

- **Redis Caching**: High-performance data caching and session management
- **Celery Integration**: Asynchronous task processing for emails and notifications
- **Database Optimization**: Advanced query optimization with select_related/prefetch_related
- **Background Processing**: Non-blocking operations for better user experience

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and commit: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Create a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 **Support & Contact**

- **API Documentation**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)


---

**Event Booking & Attendance API** - Building the future of event management! 🎉
