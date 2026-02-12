import { PrismaClient, Role } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const downtown = await prisma.facility.upsert({
    where: { id: 'facility-downtown' },
    update: {},
    create: { id: 'facility-downtown', name: 'Downtown Care Center', location: 'Chicago, IL' }
  });

  const lakeside = await prisma.facility.upsert({
    where: { id: 'facility-lakeside' },
    update: {},
    create: { id: 'facility-lakeside', name: 'Lakeside Nursing Home', location: 'Milwaukee, WI' }
  });

  const adminPassword = await bcrypt.hash('Admin1234!', 10);
  await prisma.user.upsert({
    where: { email: 'admin@nursinghub.local' },
    update: {},
    create: {
      name: 'Super Admin',
      email: 'admin@nursinghub.local',
      passwordHash: adminPassword,
      role: Role.SUPER_ADMIN,
      facilityId: downtown.id
    }
  });

  await prisma.jobPosting.createMany({
    data: [
      {
        title: 'RN - Night Shift',
        department: 'Clinical',
        description: 'Lead overnight patient care and medication administration.',
        facilityId: downtown.id
      },
      {
        title: 'CNA - Day Shift',
        department: 'Resident Care',
        description: 'Support ADLs, charting and family communication.',
        facilityId: lakeside.id
      }
    ],
    skipDuplicates: true
  });
}

main()
  .then(async () => prisma.$disconnect())
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
