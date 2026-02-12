import Link from 'next/link';
import { prisma } from '@/lib/prisma';

export default async function CareersPage() {
  const jobs = await prisma.jobPosting.findMany({ where: { isActive: true }, include: { facility: true }, orderBy: { createdAt: 'desc' } });
  return (
    <main className="container">
      <h1>Career Opportunities</h1>
      <p className="muted">Mobile-friendly application in under 3 minutes.</p>
      <div className="grid tile-grid">
        {jobs.map((job) => (
          <div key={job.id} className="card">
            <h3>{job.title}</h3>
            <p>{job.department}</p>
            <p className="muted">{job.facility.name} • {job.facility.location}</p>
            <p>{job.description.slice(0, 140)}...</p>
            <Link className="button" href={`/apply/${job.id}`}>Apply</Link>
          </div>
        ))}
      </div>
    </main>
  );
}
