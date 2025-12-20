/**
 * Players routes
 */

import { Router, Request, Response } from 'express';
import { prisma } from '../../db/client';
import { createError } from '../middleware/errorHandler';

export const playersRouter = Router();

// Get player stats
playersRouter.get('/:userId/stats', async (req: Request, res: Response, next) => {
  try {
    const { userId } = req.params;

    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        username: true,
        totalGamesPlayed: true,
        totalWins: true,
        lifetimeEarnings: true,
        createdAt: true,
      },
    });

    if (!user) {
      throw createError('Player not found', 404, 'PLAYER_NOT_FOUND');
    }

    // Calculate win rate
    const winRate = user.totalGamesPlayed > 0
      ? (user.totalWins / user.totalGamesPlayed * 100).toFixed(1)
      : '0.0';

    res.json({
      ...user,
      lifetimeEarnings: Number(user.lifetimeEarnings),
      winRate: `${winRate}%`,
    });
  } catch (error) {
    next(error);
  }
});

// Get player game history
playersRouter.get('/:userId/games', async (req: Request, res: Response, next) => {
  try {
    const { userId } = req.params;
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const offset = parseInt(req.query.offset as string) || 0;

    const participations = await prisma.gameParticipant.findMany({
      where: { userId },
      orderBy: { joinedAt: 'desc' },
      take: limit,
      skip: offset,
      include: {
        game: {
          select: {
            id: true,
            roomCode: true,
            status: true,
            startedAt: true,
            endedAt: true,
            durationSeconds: true,
          },
        },
      },
    });

    res.json({
      games: participations.map(p => ({
        gameId: p.game.id,
        roomCode: p.game.roomCode,
        status: p.game.status,
        startedAt: p.game.startedAt,
        endedAt: p.game.endedAt,
        durationSeconds: p.game.durationSeconds,
        playerName: p.playerName,
        token: p.token,
        finalPosition: p.finalPosition,
        finalNetWorth: p.finalNetWorth ? Number(p.finalNetWorth) : null,
      })),
    });
  } catch (error) {
    next(error);
  }
});

// Leaderboard
playersRouter.get('/leaderboard', async (req: Request, res: Response, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const sortBy = req.query.sortBy as string || 'wins';

    let orderBy: any = { totalWins: 'desc' };
    if (sortBy === 'games') {
      orderBy = { totalGamesPlayed: 'desc' };
    } else if (sortBy === 'earnings') {
      orderBy = { lifetimeEarnings: 'desc' };
    }

    const players = await prisma.user.findMany({
      where: {
        totalGamesPlayed: { gt: 0 },
      },
      orderBy,
      take: limit,
      select: {
        id: true,
        username: true,
        totalGamesPlayed: true,
        totalWins: true,
        lifetimeEarnings: true,
      },
    });

    res.json({
      leaderboard: players.map((p, index) => ({
        rank: index + 1,
        ...p,
        lifetimeEarnings: Number(p.lifetimeEarnings),
        winRate: p.totalGamesPlayed > 0
          ? `${(p.totalWins / p.totalGamesPlayed * 100).toFixed(1)}%`
          : '0.0%',
      })),
    });
  } catch (error) {
    next(error);
  }
});
