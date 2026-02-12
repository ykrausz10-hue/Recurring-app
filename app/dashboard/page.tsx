import Link from 'next/link';
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import { DashboardWidgets } from '@/components/dashboard-widgets';

export default async function DashboardPage() {
  const session = await getSession();
  if (!session) redirect('/login');

  const [applications, interviews, licensesDue, tasks] = await Promise.all([
    prisma.application.count(),
    prisma.interview.count(),
    prisma.license.count({ where: { expiryDate: { lte: new Date(Date.now() + 30 * 86400000) } } }),
    prisma.onboardingTask.count({ where: { isComplete: false } })
  ]);

  return (
    <main className="container">
      <h1>Admin Dashboard</h1>
      <p className="muted">Welcome {session.email}. Role: <span className="badge">{session.role}</span></p>
      <DashboardWidgets stats={{ applications, interviews, licensesDue, tasks }} />

      <div className="grid tile-grid" style={{ marginTop: 20 }}>
        <Link className="card" href="/dashboard/pipeline"><h3>ATS Pipeline</h3></Link>
        <Link className="card" href="/dashboard/templates"><h3>Messaging Templates</h3></Link>
        <Link className="card" href="/dashboard/interviews"><h3>Interview Scheduling</h3></Link>
        <Link className="card" href="/dashboard/licenses"><h3>License Tracking</h3></Link>
        <Link className="card" href="/dashboard/offers"><h3>Offers & E-Sign</h3></Link>
        <Link className="card" href="/dashboard/onboarding"><h3>Onboarding Checklist</h3></Link>
      </div>

      <form action="/api/auth/logout" method="post" style={{ marginTop: 16 }}>
        <button className="button secondary" type="submit">Logout</button>
      </form>
    </main>
  );
}
