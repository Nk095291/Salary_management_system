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

`create_hr` prompts for email, generates a password, emails credentials, and prints the password in the console when `DEBUG=True`.

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

The Vite dev server proxies `/api` requests to Django on port 8000.