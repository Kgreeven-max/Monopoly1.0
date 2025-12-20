/**
 * Admin routes
 */

import { Router, Request, Response, NextFunction } from 'express';
import { prisma } from '../../db/client';
import { RoomManager } from '../../socket/RoomManager';
import { config } from '../../config';
import { createError } from '../middleware/errorHandler';

export const adminRouter = Router();

// Admin authentication middleware
function adminAuth(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (token !== config.admin.token) {
    throw createError('Unauthorized', 401, 'UNAUTHORIZED');
  }

  next();
}

// Login endpoint (no auth required)
adminRouter.post('/auth', (req: Request, res: Response) => {
  const { adminKey } = req.body;

  if (adminKey !== config.admin.token) {
    res.status(401).json({ error: 'Invalid admin key' });
    return;
  }

  // Return the token (in production, you'd generate a JWT)
  res.json({ token: config.admin.token });
});

// Apply admin auth to all other routes
adminRouter.use(adminAuth);

// Get server status
adminRouter.get('/status', async (_req: Request, res: Response, next) => {
  try {
    const roomManager: RoomManager = _req.app.get('roomManager');

    // Get active games count from room manager
    const activeGamesQuery = await prisma.game.count({
      where: { status: { in: ['lobby', 'playing', 'paused'] } },
    });

    // Get today's stats
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const todayGames = await prisma.game.count({
      where: { createdAt: { gte: today } },
    });

    const todayCompleted = await prisma.game.count({
      where: {
        endedAt: { gte: today },
        status: 'finished',
      },
    });

    res.json({
      server: {
        version: '2.0.0',
        environment: config.nodeEnv,
        uptime: process.uptime(),
        memoryUsage: process.memoryUsage(),
      },
      games: {
        active: activeGamesQuery,
        todayStarted: todayGames,
        todayCompleted,
        maxConcurrent: config.game.maxConcurrentGames,
      },
    });
  } catch (error) {
    next(error);
  }
});

// List active games
adminRouter.get('/games/active', async (req: Request, res: Response, next) => {
  try {
    const games = await prisma.game.findMany({
      where: { status: { in: ['lobby', 'playing', 'paused'] } },
      orderBy: { createdAt: 'desc' },
      include: {
        participants: true,
        host: {
          select: { id: true, username: true },
        },
      },
    });

    res.json({ games });
  } catch (error) {
    next(error);
  }
});

// Get specific game details
adminRouter.get('/games/:gameId', async (req: Request, res: Response, next) => {
  try {
    const { gameId } = req.params;
    const roomManager: RoomManager = req.app.get('roomManager');

    // Try to get live state from room manager
    const room = roomManager?.getRoomByPlayerId(gameId);

    const game = await prisma.game.findUnique({
      where: { id: gameId },
      include: {
        participants: true,
        auditLogs: {
          orderBy: { timestamp: 'desc' },
          take: 50,
        },
      },
    });

    if (!game) {
      throw createError('Game not found', 404, 'GAME_NOT_FOUND');
    }

    res.json({
      game,
      liveState: room?.state || null,
    });
  } catch (error) {
    next(error);
  }
});

// End a game forcefully
adminRouter.post('/games/:gameId/end', async (req: Request, res: Response, next) => {
  try {
    const { gameId } = req.params;
    const { reason } = req.body;

    const game = await prisma.game.update({
      where: { id: gameId },
      data: {
        status: 'finished',
        endedAt: new Date(),
      },
    });

    // Log admin action
    await prisma.auditLog.create({
      data: {
        gameId,
        actionType: 'ADMIN_END_GAME',
        actionData: { reason },
      },
    });

    // TODO: Notify players via socket

    res.json({ success: true, game });
  } catch (error) {
    next(error);
  }
});

// Get audit logs
adminRouter.get('/audit', async (req: Request, res: Response, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit as string) || 100, 500);
    const offset = parseInt(req.query.offset as string) || 0;
    const gameId = req.query.gameId as string;
    const actionType = req.query.actionType as string;

    const where: any = {};
    if (gameId) where.gameId = gameId;
    if (actionType) where.actionType = actionType;

    const [logs, total] = await Promise.all([
      prisma.auditLog.findMany({
        where,
        orderBy: { timestamp: 'desc' },
        take: limit,
        skip: offset,
      }),
      prisma.auditLog.count({ where }),
    ]);

    res.json({
      logs,
      pagination: { total, limit, offset },
    });
  } catch (error) {
    next(error);
  }
});

// Get daily stats
adminRouter.get('/stats/daily', async (req: Request, res: Response, next) => {
  try {
    const days = Math.min(parseInt(req.query.days as string) || 30, 90);

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    startDate.setHours(0, 0, 0, 0);

    const stats = await prisma.dailyStats.findMany({
      where: { date: { gte: startDate } },
      orderBy: { date: 'desc' },
    });

    res.json({ stats });
  } catch (error) {
    next(error);
  }
});
