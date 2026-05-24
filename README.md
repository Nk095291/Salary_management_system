# TEST — Django + React

Monorepo with a Django REST API backend and a React (Vite) frontend.

## Project structure

```
.
├── backend/          # Django API
├── frontend/         # React app (Vite)
└── README.md
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- Git

## Backend setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py create_hr
python manage.py runserver
```

API:

- http://127.0.0.1:8000/api/health/
- `POST /api/auth/login/` — body: `{"email": "...", "password": "..."}`
- `POST /api/auth/refresh/` — body: `{"refresh": "..."}`
- `GET /api/auth/me/` — header: `Authorization: Bearer <access>`

Employee CRUD (requires `Authorization: Bearer <access>` from an HR user):

- `GET /api/employees/` — list (paginated; optional `?department=`, `?country=`, `?status=`)
- `POST /api/employees/` — create
- `GET /api/employees/{id}/` — retrieve
- `PATCH /api/employees/{id}/` — partial update
- `PUT /api/employees/{id}/` — full update
- `DELETE /api/employees/{id}/` — delete

Salary insights (HR JWT required):

- `GET /api/insights/overview/`
- `GET /api/insights/by-country/`
- `GET /api/insights/by-department/`
- `GET /api/insights/by-job-title/?country=...`
- `GET /api/insights/pay-equity/`

`create_hr` prompts for email, generates a password, emails credentials, and prints the password in the console when `DEBUG=True`.

Seed employees (10,000 by default; names from `backend/data/first_names.txt` and `backend/data/last_names.txt`):

```powershell
python manage.py seed_employees
python manage.py seed_employees --count 10000 --clear
```

Employees are identified by numeric database `id` in the API and UI (`/api/employees/{id}/`). Use `--employee-pk` with `create_hr` to link an existing employee record.

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

The Vite dev server proxies `/api` requests to Django on port 8000.

**Frontend API contract:** [frontend/docs/API.md](frontend/docs/API.md)

### UI routes

| Route | Page |
|-------|------|
| `/login` | HR login |
| `/profile` | Current user from `/api/auth/me/` |
| `/employees` | Employee list, filters, CRUD |
| `/insights` | Salary insights dashboards |