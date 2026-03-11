# 🏛️ Civic Issue Reporting System — Backend

A **FastAPI**-based REST API for civic issue (complaint) reporting, featuring JWT authentication, role-based access control (RBAC), and asynchronous PostgreSQL access via SQLAlchemy.

Citizens can submit geo-tagged complaints with images, while admins can triage, prioritize, and resolve them.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
  - [Authentication](#authentication-auth)
  - [Processing Service (Write)](#processing-service-write-operations)
  - [Query Service (Read)](#query-service-read-operations)
- [Data Models](#data-models)
- [Authentication & Authorization](#authentication--authorization)
- [Error Handling](#error-handling)

---

## Architecture Overview

The backend follows a **layered service architecture** that cleanly separates concerns:

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│                   (main.py)                          │
├──────────┬──────────────────┬───────────────────────┤
│  Auth    │  Processing Svc  │    Query Service      │
│  Routes  │  Routes (Write)  │    Routes (Read)      │
├──────────┤──────────────────┤───────────────────────┤
│  Auth    │  Processing      │    Query              │
│  Utils   │  Service Layer   │    Service Layer      │
├──────────┴──────────────────┴───────────────────────┤
│           Schemas (Pydantic validation)             │
├─────────────────────────────────────────────────────┤
│           Models  (SQLAlchemy ORM)                  │
├─────────────────────────────────────────────────────┤
│           Core   (Config + Async DB Session)        │
└─────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **CQRS-inspired split** — Write operations live in `processing_service/`, read operations in `query_service/`. This makes it easy to scale or optimize reads and writes independently.
- **Fully async** — All database access uses `asyncpg` + SQLAlchemy's async engine, enabling high concurrency.
- **Dependency injection** — Database sessions and the current user are injected via FastAPI's `Depends()`.

---

## Tech Stack

| Category       | Technology                         |
|----------------|------------------------------------|
| Framework      | FastAPI 0.109                      |
| Server         | Uvicorn 0.27                       |
| ORM            | SQLAlchemy 2.0 (async)             |
| DB Driver      | asyncpg 0.29                       |
| Database       | PostgreSQL                         |
| Validation     | Pydantic 2.5                       |
| Auth           | JWT via `python-jose`, bcrypt      |
| Config         | pydantic-settings (`.env` loader)  |

---

## Project Structure

```
CitizenBackend/
├── .env                           # Environment variables (not committed)
├── .gitignore
├── requirements.txt               # Python dependencies
├── README.md
└── app/
    ├── __init__.py
    ├── main.py                    # App entrypoint, CORS, router registration
    │
    ├── core/                      # Shared infrastructure
    │   ├── config.py              #   Settings loaded from .env via pydantic-settings
    │   └── database.py            #   Async engine, session factory, Base model
    │
    ├── models/                    # SQLAlchemy ORM models
    │   └── models.py              #   User, Complaint, enums (UserRole, Status, Priority)
    │
    ├── schemas/                   # Pydantic request/response schemas
    │   └── schemas.py             #   UserCreate, ComplaintCreate, ComplaintResponse, etc.
    │
    ├── auth/                      # Authentication module
    │   ├── auth_utils.py          #   Password hashing (bcrypt), JWT create/decode,
    │   │                          #   get_current_user & require_admin dependencies
    │   └── routes.py              #   POST /register, POST /login, GET /me
    │
    ├── processing_service/        # Write operations (CQRS command side)
    │   ├── service.py             #   Business logic: create, update, resolve, delete
    │   └── routes.py              #   POST/PATCH/DELETE endpoints
    │
    └── query_service/             # Read operations (CQRS query side)
        ├── service.py             #   Business logic: get by ID, list, filter, paginate
        └── routes.py              #   GET endpoints
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **PostgreSQL** (running instance with an empty database)

### 1. Clone & create virtual environment

```bash
git clone <repo-url> && cd CitizenBackend
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the project root (or copy from the example below):

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/citizen_db
JWT_SECRET_KEY=your-super-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=false
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

> **Note:** `DATABASE_URL` must use the `postgresql+asyncpg://` scheme for the async driver.

### 4. Run the server

```bash
# Development (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Explore the API

| UI          | URL                              |
|-------------|----------------------------------|
| Swagger UI  | http://localhost:8000/docs       |
| ReDoc       | http://localhost:8000/redoc      |
| Health      | http://localhost:8000/health     |

---

## Environment Variables

| Variable                          | Required | Default | Description                                |
|-----------------------------------|----------|---------|--------------------------------------------|
| `DATABASE_URL`                    | ✅       | —       | Async PostgreSQL connection string          |
| `JWT_SECRET_KEY`                  | ✅       | —       | Secret for signing JWT tokens (≥ 32 chars) |
| `JWT_ALGORITHM`                   | ❌       | `HS256` | JWT signing algorithm                       |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | ❌       | `60`    | Token lifetime in minutes                   |
| `DEBUG`                           | ❌       | `false` | Enables SQLAlchemy query echo               |
| `DEFAULT_PAGE_SIZE`               | ❌       | `20`    | Default items per page                      |
| `MAX_PAGE_SIZE`                   | ❌       | `100`   | Maximum allowed items per page              |

---

## API Reference

All endpoints return JSON. Protected endpoints require a **Bearer token** in the `Authorization` header.

### Authentication (`/auth`)

| Method | Endpoint         | Description                  | Auth Required |
|--------|------------------|------------------------------|:-------------:|
| POST   | `/auth/register` | Register a new user account  |      ❌       |
| POST   | `/auth/login`    | Login → receive JWT token    |      ❌       |
| GET    | `/auth/me`       | Get current user's profile   |      ✅       |

<details>
<summary><strong>POST /auth/register</strong> — Request & Response</summary>

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123",
  "role": "user"
}
```

**Response (`201 Created`):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "user"
}
```
</details>

<details>
<summary><strong>POST /auth/login</strong> — Request & Response</summary>

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```
</details>

---

### Processing Service — Write Operations (`/complaints`)

| Method | Endpoint                         | Description                          |   Auth    |
|--------|----------------------------------|--------------------------------------|:---------:|
| POST   | `/complaints`                    | Create a new complaint               |   User    |
| PATCH  | `/complaints/{id}/status`        | Update status and/or priority        |   Admin   |
| PATCH  | `/complaints/{id}/resolve`       | Mark complaint as resolved           |   Admin   |
| PATCH  | `/complaints/{id}/image`         | Upload / update image URL            |   Owner   |
| DELETE | `/complaints/{id}`               | Delete a complaint                   |   Admin   |

<details>
<summary><strong>POST /complaints</strong> — Create a complaint</summary>

**Request Body:**
```json
{
  "title": "Pothole on Main Street",
  "description": "Large pothole causing traffic issues near the intersection.",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "image_url": "https://example.com/pothole.jpg",
  "priority": "high"
}
```

**Response (`201 Created`):**
```json
{
  "id": 1,
  "user_id": 1,
  "title": "Pothole on Main Street",
  "description": "Large pothole causing traffic issues near the intersection.",
  "latitude": 28.6139,
  "longitude": 77.209,
  "image_url": "https://example.com/pothole.jpg",
  "status": "pending",
  "priority": "high",
  "created_at": "2026-03-11T10:30:00",
  "updated_at": "2026-03-11T10:30:00"
}
```
</details>

---

### Query Service — Read Operations (`/complaints`)

| Method | Endpoint                         | Description                             |   Auth    |
|--------|----------------------------------|-----------------------------------------|:---------:|
| GET    | `/complaints/{id}`               | Get a single complaint by ID            |   User    |
| GET    | `/complaints/user/me`            | Get current user's own complaints       |   User    |
| GET    | `/complaints/user/{user_id}`     | Get a specific user's complaints        |   Admin   |
| GET    | `/complaints`                    | List all complaints (filtered/paginated)|   Admin   |

#### Query Parameters (for list endpoints)

| Parameter   | Type   | Default | Description                                    |
|-------------|--------|---------|------------------------------------------------|
| `page`      | int    | `1`     | Page number (≥ 1)                              |
| `page_size` | int    | `20`    | Items per page (1–100)                         |
| `status`    | string | —       | Filter: `pending`, `verified`, or `resolved`   |
| `priority`  | string | —       | Filter: `low`, `medium`, or `high`             |

<details>
<summary><strong>GET /complaints/user/me</strong> — Paginated response</summary>

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Pothole on Main Street",
      "description": "...",
      "latitude": 28.6139,
      "longitude": 77.209,
      "image_url": "https://example.com/pothole.jpg",
      "status": "pending",
      "priority": "high",
      "created_at": "2026-03-11T10:30:00",
      "updated_at": "2026-03-11T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```
</details>

---

## Data Models

### `users` Table

| Column     | Type         | Constraints        | Description              |
|------------|--------------|--------------------|--------------------------|
| `id`       | Integer (PK) | Auto-increment     | Unique user identifier   |
| `name`     | String(255)  | NOT NULL           | User's display name      |
| `email`    | String(255)  | UNIQUE, NOT NULL   | Login email              |
| `password` | String(255)  | NOT NULL           | Bcrypt-hashed password   |
| `role`     | String(50)   | NOT NULL, default `user` | `admin` or `user`  |

### `complaints` Table

| Column       | Type            | Constraints             | Description                          |
|--------------|-----------------|-------------------------|--------------------------------------|
| `id`         | Integer (PK)    | Auto-increment          | Unique complaint identifier          |
| `user_id`    | Integer (FK)    | → `users.id`, NOT NULL  | Author of the complaint              |
| `title`      | String(255)     | NOT NULL                | Short summary                        |
| `description`| Text            | NOT NULL                | Detailed description                 |
| `latitude`   | Float           | NOT NULL                | GPS latitude (-90 to 90)             |
| `longitude`  | Float           | NOT NULL                | GPS longitude (-180 to 180)          |
| `image_url`  | String(500)     | Nullable                | Optional photo evidence              |
| `status`     | Enum            | NOT NULL, default `pending` | `pending` → `verified` → `resolved` |
| `priority`   | Enum            | NOT NULL, default `medium`  | `low`, `medium`, `high`          |
| `created_at` | DateTime        | NOT NULL                | Record creation timestamp            |
| `updated_at` | DateTime        | NOT NULL                | Last modification timestamp          |

### Enums

| Enum              | Values                            |
|-------------------|-----------------------------------|
| `UserRole`        | `admin`, `user`                   |
| `ComplaintStatus`  | `pending`, `verified`, `resolved`|
| `Priority`        | `low`, `medium`, `high`           |

---

## Authentication & Authorization

### How it works

1. **Register** → Password is pre-hashed with SHA-256 (to handle inputs > 72 bytes), then hashed with **bcrypt**.
2. **Login** → Returns a signed **JWT** containing `{ sub: "<user_id>", role: "<role>" }`.
3. **Protected routes** → The `Authorization: Bearer <token>` header is validated automatically via FastAPI dependency injection.

### Role-based access

| Role    | Capabilities                                                                  |
|---------|-------------------------------------------------------------------------------|
| `user`  | Register, login, create complaints, view own complaints, update own images    |
| `admin` | All user capabilities + view all complaints, update status/priority, resolve, delete |

### Key dependencies (in `auth_utils.py`)

| Dependency             | Purpose                                          |
|------------------------|--------------------------------------------------|
| `get_current_user`     | Extracts & validates JWT → returns `User` object |
| `get_current_active_user` | Same as above (extensible for active checks)  |
| `require_admin`        | Validates JWT + ensures `role == "admin"`        |

---

## Error Handling

The API returns standard HTTP status codes with JSON error bodies:

| Status Code | Meaning                                              |
|-------------|------------------------------------------------------|
| `400`       | Bad request (e.g., email already registered)         |
| `401`       | Unauthorized (missing/invalid token)                 |
| `403`       | Forbidden (insufficient role)                        |
| `404`       | Resource not found                                   |
| `422`       | Validation error (Pydantic schema mismatch)          |

**Error response format:**
```json
{
  "detail": "Human-readable error message"
}
```

---

## License

This project is for educational / personal use.