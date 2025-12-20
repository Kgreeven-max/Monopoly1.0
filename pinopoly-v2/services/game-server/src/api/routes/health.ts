/**
 * Health check routes
 */

import { Router } from 'express';
import { prisma } from '../../db/client';

export const healthRouter = Router();

healthRouter.get('/', async (_req, res) => {
  const startTime = Date.now();

  try {
    // Check database connection
    await prisma.$queryRaw`SELECT 1`;
    const dbLatency = Date.now() - startTime;

    res.json({
      status: 'healthy',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      database: {
        status: 'connected',
        latencyMs: dbLatency,
      },
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      database: {
        status: 'disconnected',
        error: String(error),
      },
    });
  }
});

healthRouter.get('/ready', async (_req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    res.status(200).send('ready');
  } catch {
    res.status(503).send('not ready');
  }
});

healthRouter.get('/live', (_req, res) => {
  res.status(200).send('alive');
});
