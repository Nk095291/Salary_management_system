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
python manage.py runserver
```

API: http://127.0.0.1:8000/api/health/

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

The Vite dev server proxies `/api` requests to Django on port 8000.