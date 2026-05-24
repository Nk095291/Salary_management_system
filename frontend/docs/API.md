# Frontend API Contract

This document describes the Django REST API consumed by the React app.

## Overview

| Item | Value |
|------|--------|
| Base URL (dev) | `/api` (proxied to `http://127.0.0.1:8000` via Vite) |
| Content-Type | `application/json` |
| Auth | JWT Bearer token on protected routes |

```http
Authorization: Bearer <access_token>
```

Store tokens after login:

- `localStorage.access_token`
- `localStorage.refresh_token`

---

## Auth

### Login

`POST /api/auth/login/`

**Request**

```json
{
  "email": "hr@company.com",
  "password": "your-password"
}
```

**Response** `200`

```json
{
  "access": "<jwt-access>",
  "refresh": "<jwt-refresh>"
}
```

**Errors**

- `401` — invalid credentials

### Refresh access token

`POST /api/auth/refresh/`

**Request**

```json
{
  "refresh": "<jwt-refresh>"
}
```

**Response** `200`

```json
{
  "access": "<new-jwt-access>"
}
```

### Current user (HR profile)

`GET /api/auth/me/`

**Headers:** `Authorization: Bearer <access>`

**Response** `200`

```json
{
  "id": 1,
  "email": "hr@company.com",
  "first_name": "HR",
  "last_name": "Manager",
  "employee": {
    "id": 1,
    "job_title": "HR Manager",
    "department": "Human Resources",
    "country": "United States"
  }
}
```

`employee` may be `null` if not linked.

---

## Employees

All employee endpoints require HR JWT authentication.

### List employees

`GET /api/employees/`

**Query parameters**

| Param | Type | Description |
|-------|------|-------------|
| `page` | number | Page number (default 1) |
| `page_size` | number | Items per page (default 25, max 100) |
| `department` | string | Exact match filter |
| `country` | string | Exact match filter |
| `status` | string | Exact match filter (`Active`, `On Leave`, `Terminated`) |

**Response** `200`

```json
{
  "count": 150,
  "next": "http://127.0.0.1:8000/api/employees/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "first_name": "Jane",
      "last_name": "Doe",
      "personal_email": "jane.personal@example.com",
      "company_email": "jane@company.com",
      "gender": "Female",
      "date_of_birth": null,
      "department": "Engineering",
      "job_title": "Software Engineer",
      "seniority_level": "Mid",
      "employment_type": "Full-time",
      "country": "United States",
      "salary": "75000.00",
      "currency": "USD",
      "date_joining": "2020-01-15",
      "date_relieving": null,
      "status": "Active",
      "created_at": "2026-05-23T10:00:00Z",
      "updated_at": "2026-05-23T10:00:00Z"
    }
  ]
}
```

### Retrieve employee

`GET /api/employees/{id}/`

**Response** `200` — single `Employee` object (same shape as list item).

### Create employee

`POST /api/employees/`

**Request** — omit `id`, `created_at`, `updated_at` (server assigns `id`).

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "personal_email": "john.personal@example.com",
  "company_email": "john@company.com",
  "gender": "Male",
  "date_of_birth": null,
  "department": "Engineering",
  "job_title": "Software Engineer",
  "seniority_level": "Mid",
  "employment_type": "Full-time",
  "country": "United States",
  "salary": "80000.00",
  "currency": "USD",
  "date_joining": "2021-05-01",
  "date_relieving": null,
  "status": "Active"
}
```

**Response** `201` — created `Employee` including database `id`.

### Update employee

`PATCH /api/employees/{id}/`

Partial update; `id` is not writable.

**Response** `200` — updated `Employee`.

### Delete employee

`DELETE /api/employees/{id}/`

**Response** `204` — no body.

---

## TypeScript types

See [`src/types/api.ts`](../src/types/api.ts) for interfaces used in the app.

```typescript
interface EmployeeSummary {
  id: number;
  job_title: string;
  department: string;
  country: string;
}

interface HRUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  employee: EmployeeSummary | null;
}

interface Employee { /* full fields */ }

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

---

## Enums (exact API strings)

| Field | Values |
|-------|--------|
| `gender` | `Male`, `Female`, `Non-binary`, `Prefer not to say` |
| `seniority_level` | `Junior`, `Mid`, `Senior`, `Lead`, `Principal` |
| `employment_type` | `Full-time`, `Part-time`, `Contract`, `Internship` |
| `status` | `Active`, `On Leave`, `Terminated` |
| `currency` | `USD`, `INR`, `GBP`, `EUR`, `AUD`, `CAD` |

---

## Errors

| Status | Meaning |
|--------|---------|
| `400` | Validation error — body may be `{ "field_name": ["message"] }` |
| `401` | Missing or invalid token |
| `403` | Authenticated but not allowed (non-HR) |
| `404` | Resource not found |

---

## Example flow

1. `POST /api/auth/login/` with email/password → save `access` and `refresh`.
2. `GET /api/auth/me/` with Bearer token → show profile.
3. `GET /api/employees/?department=Engineering&page=1` → render table.
4. `POST /api/employees/` → create row → refresh list.
5. `PATCH /api/employees/5/` → update row.
6. `DELETE /api/employees/5/` → remove row.

On `401`, attempt `POST /api/auth/refresh/` once; if that fails, clear tokens and redirect to `/login`.
