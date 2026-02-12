# Recurring App — Milestone 2

This milestone includes everything from Milestone 1 plus:

- Admin job posting CRUD (`/admin/jobs`)
- Public jobs board (`/jobs`)
- Candidate apply flow (`/jobs/<id>/apply`)

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
