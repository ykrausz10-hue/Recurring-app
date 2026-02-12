# Live Preview Deployment (Vercel + Hosted Postgres)

This guide shows how to get a **public preview URL** you can open on your iPad after every push.

> Note: This repository currently contains a Python app. The steps below are for deploying a **Next.js frontend** to Vercel, as requested.

---

## 1) Prerequisites

- A GitHub repo containing your Next.js app.
- A Vercel account (https://vercel.com).
- A hosted Postgres database (Neon or Supabase).

---

## 2) Add config to the repo

These files are already included:

- `vercel.json` (sets framework to Next.js)
- `.env.example` (documents required environment variables)

If your app also needs migrations during build/deploy, keep migration scripts in package scripts (example):

```json
{
  "scripts": {
    "build": "next build",
    "db:migrate": "prisma migrate deploy"
  }
}
```

---

## 3) Create a hosted Postgres database

### Option A: Neon

1. Create a project in Neon.
2. Create a database and copy the connection string.
3. Use the pooled/standard Postgres URL with SSL enabled.

### Option B: Supabase

1. Create a project in Supabase.
2. Open **Project Settings → Database**.
3. Copy the Postgres connection string.
4. Ensure SSL is required in the connection URL.

Store these values for Vercel:

- `DATABASE_URL`
- `DIRECT_URL` (optional but useful for migration tooling)

---

## 4) Import project into Vercel

1. Go to Vercel dashboard → **Add New… → Project**.
2. Import your GitHub repo.
3. Framework preset should auto-detect as **Next.js** (or set manually).
4. Add environment variables in **Project Settings → Environment Variables**:
   - `DATABASE_URL`
   - `DIRECT_URL` (if used)
   - `NEXT_PUBLIC_APP_URL` (set after first deployment, then redeploy)
5. Click **Deploy**.

Vercel generates:
- Production URL: `https://<project>.vercel.app`
- Preview URLs per branch/PR: `https://<project>-<hash>-<team>.vercel.app`

---

## 5) Enable automatic Preview Deployments

In Vercel project settings:

1. Go to **Git** settings.
2. Confirm **Preview Deployments** are enabled for pull requests.
3. Every PR now receives a unique public URL.

This is the URL to open on your iPad for testing.

---

## 6) (Optional) Run migrations on deploy

If you use Prisma/Drizzle/Knex/etc., configure one of these:

- **Preferred**: Run migrations in CI before promoting builds.
- **Alternative**: Use Vercel build command (careful with repeated runs).

Example build command:

```bash
npm run db:migrate && npm run build
```

---

## 7) Verify from iPad

1. Open the preview URL in Safari on iPad.
2. Log in and test critical flows.
3. Repeat after each PR update (new deployment is automatic).

---

## 8) Troubleshooting

- **Build fails with DB errors**: verify `DATABASE_URL` is set in the same Vercel environment (Preview vs Production).
- **SSL errors**: ensure `sslmode=require` is present when required.
- **Server/client env confusion**: only expose public values with `NEXT_PUBLIC_` prefix.
- **Preview URL can’t reach API**: set `NEXT_PUBLIC_APP_URL` to the deployed domain and redeploy.
