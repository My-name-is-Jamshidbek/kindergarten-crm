# Anvar Bog'cha CRM Mobile

Flutter mobile client for the educator role.

## Features

- Educator-only token login
- Educator dashboard
- Attendance list with date, group, status, and search filters
- Quick attendance status actions
- Attendance detail editing: status, check-in, check-out, absence reason, notes
- Bulk mark selected group as present
- Guardian contact lookup with search and copy actions

## Run

Start the Django backend from the repo root:

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Run Flutter:

```bash
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api
```

For Android emulator:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api
```
