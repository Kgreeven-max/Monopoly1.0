/**
 * Prisma database client
 */

import { PrismaClient } from '@prisma/client';
import { config } from '../config';

// Prevent multiple instances during hot reload in development
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: config.nodeEnv === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

if (config.nodeEnv !== 'production') {
  globalForPrisma.prisma = prisma;
}

export type { PrismaClient };
