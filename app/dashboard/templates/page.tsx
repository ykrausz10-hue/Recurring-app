import { prisma } from '@/lib/prisma';

async function createTemplate(formData: FormData) {
  'use server';
  await prisma.messageTemplate.create({
    data: {
      name: String(formData.get('name') || ''),
      subject: String(formData.get('subject') || ''),
      body: String(formData.get('body') || ''),
      channel: String(formData.get('channel') || 'EMAIL')
    }
  });
}

export default async function TemplatesPage() {
  const templates = await prisma.messageTemplate.findMany({ orderBy: { createdAt: 'desc' } });

  return (
    <main className="container">
      <h1>Messaging Templates</h1>
      <p className="muted">MVP includes reusable email templates. SMS can be added later.</p>
      <form action={createTemplate} className="card">
        <input name="name" placeholder="Template name" required />
        <input name="subject" placeholder="Email subject" required />
        <textarea name="body" placeholder="Message body" rows={4} required />
        <select name="channel" defaultValue="EMAIL"><option value="EMAIL">Email</option><option value="SMS">SMS</option></select>
        <button className="button" type="submit">Save template</button>
      </form>
      <div className="grid" style={{ marginTop: 16 }}>
        {templates.map((t) => <div key={t.id} className="card"><h3>{t.name}</h3><p><strong>{t.subject}</strong></p><p>{t.body}</p></div>)}
      </div>
    </main>
  );
}
