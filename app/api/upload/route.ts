import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(request: Request) {
  const formData = await request.formData();
  const jobId = String(formData.get('jobId') || '');
  const facilityId = String(formData.get('facilityId') || '');
  const candidateName = String(formData.get('candidateName') || '');
  const candidateEmail = String(formData.get('candidateEmail') || '');
  const candidatePhone = String(formData.get('candidatePhone') || '');
  const availability = String(formData.get('availability') || '');
  const calendarLink = String(formData.get('calendarLink') || '');
  const file = formData.get('document') as File | null;

  const app = await prisma.application.create({
    data: {
      jobId,
      facilityId,
      candidateName,
      candidateEmail,
      candidatePhone,
      availability,
      calendarLink
    }
  });

  if (file && file.size > 0) {
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const uploadsDir = path.join(process.cwd(), 'public', 'uploads');
    await mkdir(uploadsDir, { recursive: true });

    const fileName = `${Date.now()}-${file.name}`;
    await writeFile(path.join(uploadsDir, fileName), buffer);

    await prisma.applicationDocument.create({
      data: {
        applicationId: app.id,
        name: file.name,
        fileUrl: `/uploads/${fileName}`
      }
    });
  }

  return NextResponse.redirect(new URL('/careers?applied=1', request.url));
}
