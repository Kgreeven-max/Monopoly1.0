/**
 * Games routes
 */

import { Router, Request, Response } from 'express';
import { prisma } from '../../db/client';
import { RoomManager } from '../../socket/RoomManager';
import { createError } from '../middleware/errorHandler';
import { z } from 'zod';

export const gamesRouter = Router();

// Validation schemas
const createGameSchema = z.object({
  hostName: z.string().min(2).max(50),
  config: z.object({
    maxPlayers: z.number().min(2).max(8).optional(),
    startingMoney: z.number().min(500).max(5000).optional(),
    freeParkingEnabled: z.boolean().optional(),
    auctionRequired: z.boolean().optional(),
    economicCyclesEnabled: z.boolean().optional(),
  }).optional(),
});

// Create new game
gamesRouter.post('/', async (req: Request, res: Response, next) => {
  try {
    const data = createGameSchema.parse(req.body);
    const roomManager: RoomManager = req.app.get('roomManager');

    if (!roomManager) {
      throw createError('Server not ready', 503, 'SERVER_NOT_READY');
    }

    // Create game room
    const room = await roomManager.createGame(
      'host-placeholder', // Will be set when host connects via socket
      data.config || {}
    );

    res.status(201).json({
      gameId: room.id,
      roomCode: room.code,
      status: 'lobby',
      config: room.state.config,
    });
  } catch (error) {
    next(error);
  }
});

// Get game by room code
gamesRouter.get('/code/:roomCode', async (req: Request, res: Response, next) => {
  try {
    const { roomCode } = req.params;
    const roomManager: RoomManager = req.app.get('roomManager');

    // Check active rooms first
    const room = roomManager?.getRoom(roomCode);
    if (room) {
      return res.json({
        gameId: room.id,
        roomCode: room.code,
        status: room.state.status,
        playerCount: Object.keys(room.state.players).length,
        maxPlayers: room.state.config.maxPlayers,
      });
    }

    // Check database
    const game = await prisma.game.findUnique({
      where: { roomCode },
      include: {
        _count: {
          select: { participants: true },
        },
      },
    });

    if (!game) {
      throw createError('Game not found', 404, 'GAME_NOT_FOUND');
    }

    res.json({
      gameId: game.id,
      roomCode: game.roomCode,
      status: game.status,
      playerCount: game._count.participants,
      maxPlayers: (game.gameConfig as any)?.maxPlayers || 8,
    });
  } catch (error) {
    next(error);
  }
});

// Get game by ID
gamesRouter.get('/:gameId', async (req: Request, res: Response, next) => {
  try {
    const { gameId } = req.params;

    const game = await prisma.game.findUnique({
      where: { id: gameId },
      include: {
        participants: true,
        host: {
          select: { id: true, username: true },
        },
        winner: {
          select: { id: true, username: true },
        },
      },
    });

    if (!game) {
      throw createError('Game not found', 404, 'GAME_NOT_FOUND');
    }

    res.json(game);
  } catch (error) {
    next(error);
  }
});

// List recent games
gamesRouter.get('/', async (req: Request, res: Response, next) => {
  try {
    const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
    const offset = parseInt(req.query.offset as string) || 0;
    const status = req.query.status as string;

    const where = status ? { status } : {};

    const [games, total] = await Promise.all([
      prisma.game.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        take: limit,
        skip: offset,
        include: {
          _count: {
            select: { participants: true },
          },
        },
      }),
      prisma.game.count({ where }),
    ]);

    res.json({
      games,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + games.length < total,
      },
    });
  } catch (error) {
    next(error);
  }
});
