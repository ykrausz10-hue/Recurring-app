# Nursing Homes Recruiting + Onboarding App

A clean admin dashboard inspired by Empeon-style workflows, built with **Next.js + Postgres + Prisma + Docker** for multi-facility nursing home teams.

## Tech stack
- Next.js 14 (App Router)
- PostgreSQL
- Prisma ORM
- Email/password auth with role-based access (Candidate, Recruiter, Hiring Manager, Admin, Super Admin)
- Docker + docker-compose

## MVP Features (Implemented)
- Job posting + career page by facility
- Mobile-friendly application form + document upload
- ATS pipeline stages: Applied → Screen → Interview → Offer → Hired/Rejected
- Messaging templates (email-first, SMS-ready)
- Interview scheduling with availability + calendar link field
- License/cert tracking with expiry reminders
- Offer letter + basic e-sign flow
- Onboarding checklist
- Configurable dashboard tiles/widgets

---

## Quick start (simple)
1. Copy environment values:
   ```bash
   cp .env.example .env
   ```
2. Start database + app in Docker:
   ```bash
   docker compose up --build
   ```
3. In another terminal, set up schema and sample data:
   ```bash
   docker compose exec web npm run db:push
   docker compose exec web npm run db:seed
   ```
4. Open `http://localhost:3000`
5. Login with seeded admin:
   - Email: `admin@nursinghub.local`
   - Password: `Admin1234!`

---

## Milestone plan (MVP first, then v1)

### Milestone 1 — Platform foundation (DONE)
**What changed**
- Initialized Next.js app + Prisma schema + PostgreSQL connection.
- Added role model and multi-facility data model.
- Added Docker + docker-compose for one-command local startup.

**How I test it (exact commands)**
```bash
npm install
npm run db:generate
npm run build
```

**Setup you must do**
```bash
cp .env.example .env
docker compose up --build
docker compose exec web npm run db:push
docker compose exec web npm run db:seed
```

**What “done” looks like**
- App starts on localhost:3000
- Database is connected
- Seeded admin can log in

---

### Milestone 2 — Recruiting MVP core (DONE)
**What changed**
- Career page lists open jobs by facility.
- Candidate application form is mobile-friendly and accepts document upload.
- ATS pipeline board supports stage movement across required stages.
- Added reusable messaging templates (email + SMS-ready structure).

**How I test it (exact commands)**
```bash
npm run dev
```
Then manually:
1. Open `/careers`
2. Submit an application from `/apply/[jobId]`
3. Open `/dashboard/pipeline` and move candidate stage
4. Open `/dashboard/templates` and save a template

**Setup you must do**
- Seed data command from Milestone 1.

**What “done” looks like**
- Candidate can apply end-to-end.
- Recruiter can move candidates through pipeline.
- Team can save recruiting email templates.

---

### Milestone 3 — Hiring + onboarding MVP completion (DONE)
**What changed**
- Interview scheduling page with candidate availability/calendar context.
- License/cert tracker with “expiring in 30 days” reminders.
- Offer letter creation + basic typed-name e-sign.
- Onboarding checklist for new hires.

**How I test it (exact commands)**
```bash
npm run dev
```
Then manually:
1. `/dashboard/interviews` schedule interview
2. `/dashboard/licenses` add a license expiring soon
3. `/dashboard/offers` create and sign offer
4. `/dashboard/onboarding` add onboarding tasks

**Setup you must do**
- Ensure at least one candidate profile exists for license/onboarding forms.

**What “done” looks like**
- Recruiters/managers can move from applicant to signed offer and onboarding tasks.

---

## v1 Expansion roadmap (Next)
1. **Permissions hardening**
   - Enforce role-based route guards + per-facility data isolation in middleware.
2. **Comms upgrade**
   - Real email sending (Resend/SendGrid), SMS provider (Twilio), template variables.
3. **Scheduling upgrade**
   - Calendar integrations (Google/Microsoft), interviewer availability slots.
4. **Document workflows**
   - Multiple uploads, checklist-required docs, secure object storage (S3).
5. **Compliance + audit**
   - Full activity logs, EEOC fields, immutable offer signature trail.
6. **Analytics dashboard**
   - Time-to-hire, source effectiveness, drop-off rates, facility comparisons.

## Optional local (without Docker)
If you already have PostgreSQL running locally:
```bash
npm install
npm run db:generate
npm run db:push
npm run db:seed
npm run dev
```
