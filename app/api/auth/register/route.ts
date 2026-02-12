import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { createSession, hashPassword } from '@/lib/auth';

export async function POST(request: Request) {
  const form = await request.formData();
  const name = String(form.get('name') || '');
  const email = String(form.get('email') || '').toLowerCase();
  const password = String(form.get('password') || '');
  const role = String(form.get('role') || 'CANDIDATE');

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) return NextResponse.redirect(new URL('/register?error=exists', request.url));

  const passwordHash = await hashPassword(password);
  const user = await prisma.user.create({
    data: { name, email, passwordHash, role: role as any }
  });

  await createSession({ userId: user.id, role: user.role, email: user.email });
  return NextResponse.redirect(new URL('/dashboard', request.url));
}
