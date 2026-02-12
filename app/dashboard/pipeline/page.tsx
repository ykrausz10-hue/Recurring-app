import { ApplicationStage } from '@prisma/client';
import { prisma } from '@/lib/prisma';

const stages: ApplicationStage[] = ['APPLIED', 'SCREEN', 'INTERVIEW', 'OFFER', 'HIRED', 'REJECTED'];

export default async function PipelinePage() {
  const applications = await prisma.application.findMany({ include: { job: true }, orderBy: { createdAt: 'desc' } });

  return (
    <main className="container">
      <h1>Pipeline Workflow</h1>
      <div className="pipeline">
        {stages.map((stage) => (
          <section key={stage} className="card">
            <h3>{stage}</h3>
            {applications.filter((app) => app.stage === stage).map((app) => (
              <article key={app.id} className="card" style={{ marginTop: 8 }}>
                <strong>{app.candidateName}</strong>
                <p className="muted">{app.job.title}</p>
                <form action={`/api/applications/${app.id}/stage`} method="post">
                  <select name="stage" defaultValue={app.stage}>
                    {stages.map((value) => <option key={value} value={value}>{value}</option>)}
                  </select>
                  <button className="button" type="submit">Update</button>
                </form>
              </article>
            ))}
          </section>
        ))}
      </div>
    </main>
  );
}
