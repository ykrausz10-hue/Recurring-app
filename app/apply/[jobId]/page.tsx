import { prisma } from '@/lib/prisma';

export default async function ApplyPage({ params }: { params: { jobId: string } }) {
  const job = await prisma.jobPosting.findUnique({ where: { id: params.jobId }, include: { facility: true } });
  if (!job) return <main className="container">Job not found.</main>;

  return (
    <main className="container" style={{ maxWidth: 640 }}>
      <h1>Apply: {job.title}</h1>
      <p className="muted">{job.facility.name} • {job.facility.location}</p>
      <form action="/api/upload" method="post" encType="multipart/form-data">
        <input type="hidden" name="jobId" value={job.id} />
        <input type="hidden" name="facilityId" value={job.facilityId} />
        <input name="candidateName" placeholder="Full name" required />
        <input name="candidateEmail" type="email" placeholder="Email" required />
        <input name="candidatePhone" placeholder="Phone" />
        <textarea name="availability" placeholder="Best days/times for interview" rows={3} />
        <input name="calendarLink" placeholder="Calendar link (optional)" />
        <label>Upload resume/license docs
          <input type="file" name="document" accept=".pdf,.doc,.docx,.png,.jpg" />
        </label>
        <button className="button" type="submit">Submit Application</button>
      </form>
    </main>
  );
}
