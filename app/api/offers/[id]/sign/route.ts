import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const formData = await request.formData();
  const signedBy = String(formData.get('signedBy') || '');
  await prisma.offer.update({ where: { id: params.id }, data: { signedBy, signedAt: new Date(), status: 'SIGNED' } });
  return NextResponse.redirect(new URL('/dashboard/offers', request.url));
}
