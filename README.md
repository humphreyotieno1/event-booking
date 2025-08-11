# Event Booking & Attendance API

![Project Banner](https://via.placeholder.com/1200x300?text=Event+Booking+API) <!-- Placeholder; replace with actual banner if available -->

## Table of Contents
- [Project Overview](#project-overview)
- [Objectives & Use Cases](#objectives--use-cases)
- [Problem Statement](#problem-statement)
- [Core Features](#core-features)
- [Expanded Features for Robustness & Scalability](#expanded-features-for-robustness--scalability)
- [Technical Stack](#technical-stack)
- [Database Schema (ERD)](#database-schema-erd)
- [API Endpoints](#api-endpoints)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Deployment](#deployment)
- [Best Practices & Extensibility](#best-practices--extensibility)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Project Overview
This is a RESTful backend API for managing event creation, RSVPs, and attendance tracking, built with Django and Django REST Framework (DRF). It replicates core functionalities of platforms like Meetup or Eventbrite on a smaller scale, with built-in extensibility for future growth. The API supports user authentication, event management, and optional integration with external event providers (e.g., Ticketmaster or SeatGeek).

Originally conceived as a capstone project, this application has been expanded for robustness and scalability. Key enhancements include advanced search capabilities, caching for performance, asynchronous task handling, and modular design to support features like payments, notifications, and user profiles. The system is designed to handle increased load through horizontal scaling, with considerations for microservices if needed in the future.

## Objectives & Use Cases
- **Build a Modular Backend**: Demonstrate proficiency in Django/DRF, authentication, permissions, and RESTful design.
- **User Roles**: Differentiate between organizers (event creators) and attendees.
- **Scalability Focus**: Implement caching, pagination, and async processing to support growing user bases.
- **Integration**: Optionally pull in real-world events from external APIs for a hybrid local/external event ecosystem.
- **Use Cases**:
  - Organizers create and manage events with capacity limits.
  - Users browse, search, and RSVP to events.
  - Admins monitor attendance and integrate external data.
  - Future: Add ticketing, live streaming, or social sharing.

## Problem Statement
Organizing events and managing attendance can be fragmented, especially when blending custom events with real-world ones from providers like Ticketmaster. This API solves this by providing:
- A centralized platform for event lifecycle management (create, update, delete).
- RSVP handling with capacity enforcement and status tracking.
- Searchable event browsing with filters.
- Seamless integration of external events to enrich the platform's offerings.

Without such a system, users face silos between personal events and public ones, leading to inefficient planning.

## Core Features
These form the foundation based on the initial planning:

- **Authentication**:
  - User registration and login via JWT.
  - Role-based access: Organizers can create/edit events; all users can RSVP.

- **Event Management**:
  - CRUD operations for events (title, description, location, start/end times, capacity).
  - Ownership tied to creators.

- **RSVP & Attendance**:
  - RSVP with status ("Going" or "Cancelled").
  - Enforce event capacity limits.
  - View attendee lists and counts.

- **Browse & Search**:
  - Filter events by title, date range, organizer, or location.
  - Pagination for large result sets.

- **External API Integration**:
  - Fetch events from Ticketmaster or SeatGeek.
  - Import external events into the local database.

## Expanded Features for Robustness & Scalability
To make the application more robust and scalable, the following enhancements have been incorporated or planned:

- **Advanced Search & Filtering**:
  - Full-text search using PostgreSQL's built-in search capabilities.
  - Additional filters: By category, tags, or popularity (e.g., based on RSVPs).

- **User Profiles**:
  - Extended user model with bio, profile picture, and preferences (e.g., event categories of interest).

- **Event Enhancements**:
  - Categories and tags for better organization.
  - Image uploads for event banners.
  - Recurring events support (e.g., weekly meetups).
  - Waitlist functionality if capacity is reached.

- **Notifications**:
  - Email/SMS reminders for upcoming events (using Celery for async tasks).
  - Push notifications via integration with Firebase or similar.

- **Ratings & Reviews**:
  - Post-event feedback system with star ratings and comments.

- **Payments (Future-Proofed)**:
  - Hooks for integrating Stripe or PayPal for paid events/ticketing.

- **Analytics**:
  - Basic dashboards for organizers (e.g., attendance stats, popular events).

- **Scalability Measures**:
  - Caching with Redis for frequent queries (e.g., event lists).
  - Asynchronous processing with Celery + RabbitMQ for tasks like email sending or external API calls.
  - Rate limiting and throttling via DRF to prevent abuse.
  - Database optimizations: Indexes on search fields, partitioning for large tables.

- **Security Enhancements**:
  - OAuth2 support for social logins.
  - Two-factor authentication (2FA).
  - Data validation and sanitization to prevent injections.

These expansions ensure the app can scale from a small project to a production-grade service handling thousands of users.

## Technical Stack
- **Backend**: Django 4.x + Django REST Framework.
- **Authentication**: djangorestframework-simplejwt for JWT.
- **Database**: PostgreSQL (production) / SQLite (development).
- **API Documentation**: drf-yasg for Swagger/OpenAPI.
- **Caching & Async**: Redis (caching), Celery + RabbitMQ (tasks).
- **External APIs**: Ticketmaster/SeatGeek (free tiers).
- **Testing**: Django's built-in testing + pytest.
- **Deployment**: Render or Railway (with Docker support).
- **Other Tools**: Git for version control, Docker for containerization, Sentry for error monitoring.

## Database Schema (ERD)
The schema has been expanded slightly for robustness (e.g., adding categories and tags). Below is the updated DBML code and a description. The original ERD image provided has been used as a base.

### Updated DBML Code
```
Table users {
  id int [pk, increment]
  username varchar [unique]
  email varchar [unique]
  password varchar
  is_organizer boolean [default: false]
  bio text [null]
  profile_picture varchar [null] // URL to image
}

Table event_categories {
  id int [pk, increment]
  name varchar [unique]
  description text
}

Table event_tags {
  id int [pk, increment]
  name varchar [unique]
}

Table events {
  id int [pk, increment]
  title varchar
  description text
  location varchar
  start_time datetime
  end_time datetime
  created_by int [ref: > users.id]
  max_attendees int [null]
  external_event_id varchar [null]
  category_id int [ref: > event_categories.id, null]
  is_recurring boolean [default: false]
  recurrence_pattern varchar [null] // e.g., 'weekly'
}

Table event_tags_mapping {
  event_id int [ref: > events.id]
  tag_id int [ref: > event_tags.id]
  [pk: event_id, tag_id]
}

Enum RSVPStatus {
  going
  interested // Added for more granularity
  cancelled
}

Table rsvps {
  id int [pk, increment]
  user_id int [ref: > users.id]
  event_id int [ref: > events.id]
  status RSVPStatus
  created_at datetime [default: `now()`]
}

Table reviews {
  id int [pk, increment]
  user_id int [ref: > users.id]
  event_id int [ref: > events.id]
  rating int // 1-5
  comment text
  created_at datetime [default: `now()`]
}
```

- **Relationships**:
  - One-to-Many: User → Events (created_by).
  - Many-to-Many: Events ↔ Users via RSVPs.
  - One-to-Many: Category → Events.
  - Many-to-Many: Events ↔ Tags.
  - Indexes: Added on frequently queried fields like `events.start_time`, `events.title` for performance.

For visualization, refer to the provided ERD image (exported from dbdiagram.io) and update it with these additions.

## API Endpoints
All endpoints require authentication except registration/login. Use JWT in the `Authorization: Bearer <token>` header.

| Endpoint | Method | Description | Permissions | Query Params / Body |
|----------|--------|-------------|-------------|---------------------|
| `/api/register/` | POST | Register a new user | Open | Body: {username, email, password, is_organizer} |
| `/api/login/` | POST | Obtain JWT token | Open | Body: {username, password} |
| `/api/events/` | GET | List all events (paginated) | Authenticated | ?page=1&limit=10&search=title&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&category_id=1 |
| `/api/events/` | POST | Create a new event | Organizers only | Body: {title, description, location, start_time, end_time, max_attendees, category_id, tags: [1,2]} |
| `/api/events/<id>/` | GET | View specific event | Authenticated | - |
| `/api/events/<id>/` | PUT | Update event | Owner only | Body: Partial updates |
| `/api/events/<id>/` | DELETE | Delete event | Owner only | - |
| `/api/events/<id>/rsvp/` | POST | RSVP to event | Authenticated | Body: {status: "going"} |
| `/api/events/<id>/cancel/` | POST | Cancel RSVP | Authenticated | - |
| `/api/events/<id>/attendees/` | GET | List attendees | Authenticated | ?status=going |
| `/api/events/<id>/reviews/` | GET, POST | Get/Add reviews | Attendees only (POST) | POST Body: {rating, comment} |
| `/api/events/search/` | GET | Advanced search | Authenticated | ?q=query&category=tech&tags=conference&sort=popularity |
| `/api/external-events/` | GET | Fetch from external API | Authenticated | ?provider=ticketmaster&query=concert&location=NY |
| `/api/external-events/<ext_id>/import/` | POST | Import external event | Organizers only | Body: {map fields if needed} |
| `/api/users/profile/` | GET, PUT | View/Update profile | Authenticated | PUT Body: {bio, profile_picture} |

API docs available at `/swagger/` after setup.

## Installation & Setup
1. **Prerequisites**:
   - Python 3.10+
   - PostgreSQL 13+
   - Redis (for caching)
   - Virtualenv

2. **Clone Repository**:
   ```
   git clone https://github.com/yourusername/event-booking-api.git
   cd event-booking-api
   ```

3. **Setup Virtual Environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```
   (Includes django, djangorestframework, djangorestframework-simplejwt, drf-yasg, psycopg2, celery, redis, etc.)

5. **Environment Variables**:
   Create `.env` file:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:pass@localhost/dbname
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
   TICKETMASTER_API_KEY=your-key
   ```

6. **Database Migrations**:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create Superuser**:
   ```
   python manage.py createsuperuser
   ```

## Running the Application
- **Development Server**:
  ```
  python manage.py runserver
  ```
  Access at `http://127.0.0.1:8000/`.

- **Celery Worker** (for async tasks):
  ```
  celery -A project_name worker -l info
  ```

- **API Testing**: Use Postman or Swagger UI at `/swagger/`.

## Testing
- Run unit/integration tests:
  ```
  python manage.py test
  ```
- Coverage: Use `coverage run` and `coverage report`.

## Deployment
- **Platform**: Render/Railway.
- **Steps**:
  1. Dockerize: Use provided `Dockerfile`.
  2. Push to GitHub.
  3. Connect repo to Render; set env vars.
  4. Deploy: Auto-builds on push.
- **CI/CD**: GitHub Actions workflow for testing/linting.
- **Monitoring**: Integrate Sentry for errors.

## Best Practices & Extensibility
- **Code Structure**: Modular apps (accounts, events, rsvp, external_events).
- **Permissions**: Custom DRF permissions for roles.
- **Logging**: Django's logging + structlog.
- **Extensibility**: Add microservices for notifications/payments. Hooks for frontend (e.g., React integration).
- **Performance**: Query optimization, prefetch_related for relationships.

## Contributing
- Fork the repo.
- Create feature branch: `git checkout -b feature/new-feature`.
- Commit changes: `git commit -m 'Add new feature'`.
- Push: `git push origin feature/new-feature`.
- Open PR.

## License
MIT License. See [LICENSE](LICENSE) file.

## Contact
Author: Humphrey Ouma  
Email: humphrey@example.com  
GitHub: [yourusername](https://github.com/yourusername)