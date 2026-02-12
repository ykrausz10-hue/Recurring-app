# Recurring App — Milestone 3

This milestone includes everything from Milestone 2 plus:

- ATS pipeline board for admins (`/admin/ats`)
- Candidate profile view (`/admin/applications/<id>`)
- Candidate status progression (submitted → screening → interview → offer → hired/rejected)
- Interview notes and candidate task tracking

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

## Vercel live preview (Next.js)

For deploying a Next.js preview environment on Vercel (with Neon/Supabase Postgres), follow:

- `docs/VERCEL_DEPLOYMENT.md`

Config files included:

- `vercel.json`
- `.env.example`
