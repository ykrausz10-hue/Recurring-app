# Recurring App — Milestone 1

This milestone scaffolds a runnable Python WSGI app with:

- SQLite database setup and seeding.
- Login + logout using cookie sessions.
- Role-based access control for admin-only routes.
- Empeon-like dashboard with tile cards.

## Run

```bash
python -m recurring_app.server
```

App URL: `http://localhost:8000`

## Default users

- `admin@recurring.local` / `Admin123!`
- `manager@recurring.local` / `Manager123!`
- `employee@recurring.local` / `Employee123!`

## Test

```bash
pytest
```
