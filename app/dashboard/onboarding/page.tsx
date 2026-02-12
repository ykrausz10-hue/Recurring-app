import { prisma } from '@/lib/prisma';

async function createTask(formData: FormData) {
  'use server';
  await prisma.onboardingTask.create({
    data: {
      candidateId: String(formData.get('candidateId') || ''),
      title: String(formData.get('title') || ''),
      dueDate: formData.get('dueDate') ? new Date(String(formData.get('dueDate'))) : undefined
    }
  });
}

export default async function OnboardingPage() {
  const [candidates, tasks] = await Promise.all([
    prisma.candidateProfile.findMany({ include: { user: true } }),
    prisma.onboardingTask.findMany({ include: { candidate: { include: { user: true } } }, orderBy: { isComplete: 'asc' } })
  ]);

  return (
    <main className="container">
      <h1>Onboarding Checklist</h1>
      <form action={createTask} className="card">
        <select name="candidateId" required>
          <option value="">Choose new hire</option>
          {candidates.map((c) => <option key={c.id} value={c.id}>{c.user.name}</option>)}
        </select>
        <input name="title" placeholder="Task title (e.g. Background check)" required />
        <input name="dueDate" type="date" />
        <button className="button" type="submit">Add task</button>
      </form>
      <div className="grid" style={{ marginTop: 16 }}>
        {tasks.map((task) => (
          <div key={task.id} className="card">
            <h3>{task.title}</h3>
            <p>Candidate: {task.candidate.user.name}</p>
            <p>Status: {task.isComplete ? 'Complete' : 'Open'}</p>
            <p>Due: {task.dueDate?.toDateString() || 'No due date'}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
