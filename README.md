# Civic Issue Reporting System - Backend

A FastAPI backend for a civic issue reporting system with JWT authentication and role-based access control.

## Project Structure

```
app/
├── __init__.py
├── main.py                    # FastAPI application entry point
├── core/
│   ├── __init__.py
│   ├── config.py              # Environment configuration
│   └── database.py            # Database connection and session
├── auth/
│   ├── __init__.py
│   ├── auth_utils.py          # JWT & password utilities
│   └── routes.py              # Authentication endpoints
├── models/
│   ├── __init__.py
│   └── models.py              # SQLAlchemy models
├── schemas/
│   ├── __init__.py
│   └── schemas.py             # Pydantic schemas
├── processing_service/
│   ├── __init__.py
│   ├── service.py             # Write operations logic
│   └── routes.py              # Processing endpoints
└── query_service/
    ├── __init__.py
    ├── service.py             # Read operations logic
    └── routes.py              # Query endpoints
```

## Requirements

- Python 3.10+
- PostgreSQL database

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Update `DATABASE_URL` with your PostgreSQL connection string
- Set a secure `JWT_SECRET_KEY` (minimum 32 characters)

### 4. Run the application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access the interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login and get JWT token | No |
| GET | `/auth/me` | Get current user info | Yes |

### Processing Service (`/complaints`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/complaints` | Create a new complaint | User |
| PATCH | `/complaints/{id}/status` | Update complaint status/priority | Admin |
| PATCH | `/complaints/{id}/resolve` | Mark complaint as resolved | Admin |
| PATCH | `/complaints/{id}/image` | Upload image URL | Owner |
| DELETE | `/complaints/{id}` | Delete a complaint | Admin |

### Query Service (`/complaints`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/complaints/{id}` | Get complaint by ID | User |
| GET | `/complaints/user/me` | Get current user's complaints | User |
| GET | `/complaints/user/{user_id}` | Get user's complaints | Admin |
| GET | `/complaints` | List all complaints | Admin |

### Query Parameters

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `status`: Filter by status (pending/verified/resolved)
- `priority`: Filter by priority (low/medium/high)

## User Roles

- **user**: Can create complaints, view own complaints, update own complaint images
- **admin**: Full access to all endpoints, can update status/priority, delete complaints

## Database Tables

### Users
- `id` (PK)
- `name`
- `email` (unique)
- `role` (admin/user)

### Complaints
- `id` (PK)
- `user_id` (FK)
- `title`
- `description`
- `latitude`
- `longitude`
- `image_url`
- `status` (pending/verified/resolved)
- `priority` (low/medium/high)
- `created_at`
- `updated_at`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Required |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | 60 |
| `DEBUG` | Enable debug mode | false |
| `DEFAULT_PAGE_SIZE` | Default pagination size | 20 |
| `MAX_PAGE_SIZE` | Maximum pagination size | 100 |