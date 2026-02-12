import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const formData = await request.formData();
  const stage = String(formData.get('stage') || 'APPLIED');
  await prisma.application.update({ where: { id: params.id }, data: { stage: stage as any } });
  return NextResponse.redirect(new URL('/dashboard/pipeline', request.url));
}
