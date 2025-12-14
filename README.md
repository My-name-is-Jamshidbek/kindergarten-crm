# Kindergarten CRM (Django)

A simple full-stack Django 5.x + Bootstrap 5 app to manage:
- Classrooms
- Children
- Guardians

`core` provides CRUD screens (login required) and a public home page.

## Requirements

- Python 3.11+ (this repo works with 3.11/3.12)
- PostgreSQL (optional; SQLite works out of the box)

## Quick start (SQLite)

```bash
cd kindergarten-crm
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set SECRET_KEY

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
python manage.py runserver
```

Open:
- http://127.0.0.1:8000/ (public home)
- http://127.0.0.1:8000/classrooms/ (CRUD; login required)
- http://127.0.0.1:8000/admin/ (admin)

## PostgreSQL

Set `DATABASE_URL` in `.env`, for example:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kindergarten_crm
```

Then run:

```bash
python manage.py migrate
python manage.py runserver
```

## Auth

This project uses Django’s built-in auth:
- Login: `/accounts/login/`
- Logout: `/accounts/logout/`
- Password reset: `/accounts/password_reset/`

Password reset emails are printed to the console via Django’s console email backend.

## Notes

- No secrets are committed. Configure everything via `.env` / environment variables.
- Static/media are configured for development. For production, serve static files via your web server.

## Attendance

- Attendance list: `/attendance/`
- Pick a date and optionally filter by classroom/status.
- If you open a date that has no attendance records yet, the app auto-creates `Expected` records for all **Active** children.
- Use the row buttons to quickly mark Present/Late/Absent/Half-day, or click **Edit** for check-in/out times, absence reason, and notes.
- To bulk mark a classroom as Present: select a classroom filter, then use **Bulk mark Present**.
