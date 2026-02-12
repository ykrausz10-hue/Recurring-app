import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="container">
      <h1>Recruiting + Onboarding for Multi-Facility Nursing Homes</h1>
      <p className="muted">MVP includes job posting, mobile application, ATS pipeline, messaging templates, interviews, license tracking, offers, and onboarding checklist.</p>
      <div className="grid tile-grid">
        <div className="card"><h3>Post Jobs</h3><p>Recruiters can publish open roles by facility.</p></div>
        <div className="card"><h3>Track Pipeline</h3><p>Move candidates from Applied to Hired/Rejected.</p></div>
        <div className="card"><h3>Send Offers</h3><p>Create offer letters and collect basic e-signatures.</p></div>
        <div className="card"><h3>Onboard Hires</h3><p>Complete checklists with reminders.</p></div>
      </div>
      <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
        <Link className="button" href="/careers">View Career Page</Link>
        <Link className="button secondary" href="/dashboard">Open Dashboard</Link>
      </div>
    </main>
  );
}
