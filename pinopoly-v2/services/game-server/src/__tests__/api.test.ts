import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import express from 'express';
import request from 'supertest';
import { Server } from 'http';
import { Server as SocketServer } from 'socket.io';
import { RoomManager } from '../socket/RoomManager';
import { PrismaClient } from '@prisma/client';

// Mock the Prisma client module
vi.mock('../db/client', () => ({
  prisma: {
    game: {
      create: vi.fn().mockResolvedValue({}),
      findUnique: vi.fn().mockResolvedValue(null),
      update: vi.fn().mockResolvedValue({}),
    },
    gameParticipant: {
      create: vi.fn().mockResolvedValue({}),
    },
  },
}));

// Import after mocking
import { gamesRouter } from '../api/routes/games';

// Mock Prisma client for RoomManager
const mockPrisma = {
  game: {
    create: vi.fn().mockResolvedValue({}),
    findUnique: vi.fn().mockResolvedValue(null),
    update: vi.fn().mockResolvedValue({}),
  },
  gameParticipant: {
    create: vi.fn().mockResolvedValue({}),
  },
} as unknown as PrismaClient;

describe('Games API', () => {
  let app: express.Application;
  let httpServer: Server;
  let io: SocketServer;
  let roomManager: RoomManager;

  beforeAll(() => {
    app = express();
    app.use(express.json());

    httpServer = new Server(app);
    io = new SocketServer(httpServer);
    roomManager = new RoomManager(io, mockPrisma);

    app.set('roomManager', roomManager);
    app.use('/api/games', gamesRouter);

    // Error handler (handles Zod validation errors)
    app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
      // Check for Zod validation error
      if (err.name === 'ZodError') {
        return res.status(400).json({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Validation failed',
            details: err.errors,
          },
        });
      }

      const status = err.status || err.statusCode || 500;
      res.status(status).json({
        error: {
          code: err.code || 'INTERNAL_ERROR',
          message: err.message || 'Internal server error',
        },
      });
    });
  });

  afterAll(() => {
    io.close();
    httpServer.close();
  });

  describe('POST /api/games', () => {
    it('should create a new game with valid data', async () => {
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);

      expect(response.body).toHaveProperty('gameId');
      expect(response.body).toHaveProperty('roomCode');
      expect(response.body.roomCode).toHaveLength(6);
      expect(response.body.status).toBe('lobby');
      expect(response.body.config).toBeDefined();
    });

    it('should create a game with custom config', async () => {
      const response = await request(app)
        .post('/api/games')
        .send({
          hostName: 'TestHost',
          config: {
            maxPlayers: 6,
            startingMoney: 2000,
          },
        })
        .expect(201);

      expect(response.body.config.maxPlayers).toBe(6);
      expect(response.body.config.startingMoney).toBe(2000);
    });

    it('should reject invalid host name', async () => {
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'A' }) // Too short
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });
  });

  describe('GET /api/games/code/:roomCode', () => {
    it('should return game info for valid room code', async () => {
      // First create a game
      const createResponse = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);

      const roomCode = createResponse.body.roomCode;

      // Then get it
      const response = await request(app)
        .get(`/api/games/code/${roomCode}`)
        .expect(200);

      expect(response.body.roomCode).toBe(roomCode);
      expect(response.body.status).toBe('lobby');
      expect(response.body.playerCount).toBe(0);
    });

    it('should return 404 for non-existent room code', async () => {
      const response = await request(app)
        .get('/api/games/code/XXXXXX')
        .expect(404);

      expect(response.body).toHaveProperty('error');
    });
  });
});
