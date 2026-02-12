import { prisma } from '@/lib/prisma';

async function addLicense(formData: FormData) {
  'use server';
  const candidateId = String(formData.get('candidateId') || '');
  await prisma.license.create({
    data: {
      candidateId,
      type: String(formData.get('type') || ''),
      number: String(formData.get('number') || ''),
      expiryDate: new Date(String(formData.get('expiryDate') || ''))
    }
  });
}

export default async function LicensesPage() {
  const [candidates, licenses] = await Promise.all([
    prisma.candidateProfile.findMany({ include: { user: true } }),
    prisma.license.findMany({ include: { candidate: { include: { user: true } } }, orderBy: { expiryDate: 'asc' } })
  ]);

  return (
    <main className="container">
      <h1>License & Certification Tracking</h1>
      <form action={addLicense} className="card">
        <select name="candidateId" required>
          <option value="">Choose candidate</option>
          {candidates.map((c) => <option key={c.id} value={c.id}>{c.user.name}</option>)}
        </select>
        <input name="type" placeholder="License type (e.g. RN)" required />
        <input name="number" placeholder="License number" required />
        <input name="expiryDate" type="date" required />
        <button className="button" type="submit">Track license</button>
      </form>
      <div className="grid" style={{ marginTop: 16 }}>
        {licenses.map((license) => {
          const daysLeft = Math.ceil((license.expiryDate.getTime() - Date.now()) / 86400000);
          return (
            <div key={license.id} className="card">
              <h3>{license.candidate.user.name}</h3>
              <p>{license.type} • {license.number}</p>
              <p>Expires: {license.expiryDate.toDateString()}</p>
              {daysLeft <= 30 && <p className="badge">Reminder: expires in {daysLeft} day(s)</p>}
            </div>
          );
        })}
      </div>
    </main>
  );
}
