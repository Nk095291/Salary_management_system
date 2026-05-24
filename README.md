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

## Deployment

### Backend (Railway + SQLite)

1. Create a [Railway](https://railway.app) project and deploy this repo.
2. Set the service **Root Directory** to `backend`.
3. **Networking** → generate a public domain for the API.
4. (Recommended) **Volumes** → add a volume mounted at `/data` so SQLite survives redeploys.
5. Set environment variables:

| Variable | Production example |
|----------|-------------------|
| `DJANGO_SECRET_KEY` | Long random string |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `your-api.up.railway.app` |
| `DJANGO_DB_PATH` | `/data/db.sqlite3` (when using a volume) |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.vercel.app` |
| `FRONTEND_LOGIN_URL` | `https://your-app.vercel.app/login` |

Railway runs migrations and starts Gunicorn via [`backend/Procfile`](backend/Procfile).

Post-deploy (Railway CLI or service shell):

```bash
railway run python manage.py create_hr --email you@example.com --no-input
railway run python manage.py seed_employees --count 10000 --clear
```

Without a volume, the SQLite file is recreated on each deploy—run `migrate` (automatic) and seed again if needed.

### Frontend (Vercel or Netlify)

1. Import the repo; set **Root Directory** to `frontend`.
2. Build command: `npm run build`; output directory: `dist`.
3. Set build-time env:

```
VITE_API_BASE_URL=https://your-api.up.railway.app
```

Leave `VITE_API_BASE_URL` empty locally so the Vite dev proxy handles `/api`.

SPA routing: [`frontend/vercel.json`](frontend/vercel.json) (Vercel) or [`frontend/public/_redirects`](frontend/public/_redirects) (Netlify).

**Deploy order:** backend → set `VITE_API_BASE_URL` on the frontend host → deploy frontend → set Railway `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` to the frontend URL → redeploy backend if CORS was a placeholder.

### Smoke test

- `GET https://<api>/api/health/`
- Log in from the production UI; open `/employees` and `/insights` after seeding.