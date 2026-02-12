import { prisma } from '@/lib/prisma';

async function scheduleInterview(formData: FormData) {
  'use server';
  const applicationId = String(formData.get('applicationId') || '');
  const scheduledFor = String(formData.get('scheduledFor') || '');
  const interviewer = String(formData.get('interviewer') || '');
  await prisma.interview.create({
    data: {
      applicationId,
      scheduledFor: scheduledFor ? new Date(scheduledFor) : undefined,
      interviewer
    }
  });
}

export default async function InterviewsPage() {
  const [apps, interviews] = await Promise.all([
    prisma.application.findMany({ orderBy: { createdAt: 'desc' } }),
    prisma.interview.findMany({ include: { application: true }, orderBy: { createdAt: 'desc' } })
  ]);

  return (
    <main className="container">
      <h1>Interview Scheduling</h1>
      <form action={scheduleInterview} className="card">
        <select name="applicationId" required>
          <option value="">Select candidate</option>
          {apps.map((app) => <option key={app.id} value={app.id}>{app.candidateName}</option>)}
        </select>
        <input name="scheduledFor" type="datetime-local" />
        <input name="interviewer" placeholder="Interviewer name" />
        <button className="button" type="submit">Schedule</button>
      </form>
      <div className="grid" style={{ marginTop: 16 }}>
        {interviews.map((item) => (
          <div key={item.id} className="card">
            <h3>{item.application.candidateName}</h3>
            <p>When: {item.scheduledFor?.toLocaleString() || 'Pending'}</p>
            <p>Interviewer: {item.interviewer || 'TBD'}</p>
            <p>Calendar link: {item.application.calendarLink || 'Not provided'}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
