import { prisma } from '@/lib/prisma';

async function createOffer(formData: FormData) {
  'use server';
  await prisma.offer.create({
    data: {
      applicationId: String(formData.get('applicationId') || ''),
      letterBody: String(formData.get('letterBody') || '')
    }
  });
}

export default async function OffersPage() {
  const [applications, offers] = await Promise.all([
    prisma.application.findMany({ orderBy: { createdAt: 'desc' } }),
    prisma.offer.findMany({ include: { application: true }, orderBy: { application: { candidateName: 'asc' } } })
  ]);

  return (
    <main className="container">
      <h1>Offer Letter + Basic E-Sign</h1>
      <form action={createOffer} className="card">
        <select name="applicationId" required>
          <option value="">Choose candidate</option>
          {applications.map((app) => <option key={app.id} value={app.id}>{app.candidateName}</option>)}
        </select>
        <textarea name="letterBody" rows={5} placeholder="Offer letter body" required />
        <button className="button" type="submit">Create offer</button>
      </form>

      <div className="grid" style={{ marginTop: 16 }}>
        {offers.map((offer) => (
          <div key={offer.id} className="card">
            <h3>{offer.application.candidateName}</h3>
            <p>{offer.letterBody}</p>
            <p>Status: <span className="badge">{offer.status}</span></p>
            {!offer.signedBy ? (
              <form action={`/api/offers/${offer.id}/sign`} method="post">
                <input name="signedBy" placeholder="Type full legal name" required />
                <button className="button" type="submit">E-sign</button>
              </form>
            ) : <p>Signed by {offer.signedBy} on {offer.signedAt?.toDateString()}</p>}
          </div>
        ))}
      </div>
    </main>
  );
}
