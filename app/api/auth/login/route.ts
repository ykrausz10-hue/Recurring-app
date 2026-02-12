import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { createSession, verifyPassword } from '@/lib/auth';

export async function POST(request: Request) {
  const form = await request.formData();
  const email = String(form.get('email') || '').toLowerCase();
  const password = String(form.get('password') || '');
  const user = await prisma.user.findUnique({ where: { email } });

  if (!user || !(await verifyPassword(password, user.passwordHash))) {
    return NextResponse.redirect(new URL('/login?error=invalid', request.url));
  }

  await createSession({ userId: user.id, role: user.role, email: user.email });
  return NextResponse.redirect(new URL('/dashboard', request.url));
}
