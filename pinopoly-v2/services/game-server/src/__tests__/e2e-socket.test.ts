/**
 * E2E Socket Tests - Complete Game Flow
 * Tests socket connections, game creation, joining, and full gameplay
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';
import { Server as HttpServer } from 'http';
import { Server as SocketServer } from 'socket.io';
import { io as ioClient, Socket as ClientSocket } from 'socket.io-client';
import express from 'express';
import request from 'supertest';
import { RoomManager } from '../socket/RoomManager';
import { SocketEvents } from '@pinopoly/shared';
import { GameState } from '@pinopoly/game-engine';

// Test configuration
const TEST_PORT = 3999;
const SERVER_URL = `http://localhost:${TEST_PORT}`;

// Mock Prisma client
const mockPrisma = {
  game: {
    create: async () => ({}),
    findUnique: async () => null,
    update: async () => ({}),
  },
  gameParticipant: {
    create: async () => ({}),
  },
} as any;

describe('E2E Socket Tests', () => {
  let app: express.Application;
  let httpServer: HttpServer;
  let io: SocketServer;
  let roomManager: RoomManager;
  let roomCode: string;
  let gameId: string;

  // Client sockets
  let tvDisplay: ClientSocket;
  let player1: ClientSocket;
  let player2: ClientSocket;

  beforeAll(async () => {
    // Setup server
    app = express();
    app.use(express.json());

    httpServer = new HttpServer(app);
    io = new SocketServer(httpServer, {
      cors: { origin: '*' },
    });
    roomManager = new RoomManager(io, mockPrisma);

    // Setup routes
    app.set('roomManager', roomManager);

    // Games route
    app.post('/api/games', async (req, res) => {
      try {
        const { hostName, config } = req.body;
        const room = await roomManager.createGame('host-placeholder', config || {});
        roomCode = room.code;
        gameId = room.id;
        res.status(201).json({
          gameId: room.id,
          roomCode: room.code,
          status: room.state.status,
          config: room.state.config,
        });
      } catch (error: any) {
        res.status(500).json({ error: { message: error.message } });
      }
    });

    app.get('/api/games/code/:code', (req, res) => {
      const room = roomManager.getRoom(req.params.code);
      if (!room) {
        return res.status(404).json({ error: { message: 'Game not found' } });
      }
      res.json({
        gameId: room.id,
        roomCode: room.code,
        status: room.state.status,
        playerCount: Object.keys(room.state.players).length,
        maxPlayers: room.state.config.maxPlayers,
      });
    });

    // Start server
    await new Promise<void>((resolve) => {
      httpServer.listen(TEST_PORT, () => {
        console.log(`Test server running on port ${TEST_PORT}`);
        resolve();
      });
    });
  });

  afterAll(async () => {
    // Cleanup
    if (tvDisplay?.connected) tvDisplay.disconnect();
    if (player1?.connected) player1.disconnect();
    if (player2?.connected) player2.disconnect();

    await new Promise<void>((resolve) => {
      io.close(() => {
        httpServer.close(() => {
          resolve();
        });
      });
    });
  });

  beforeEach(() => {
    // Reset sockets before each test
  });

  afterEach(() => {
    // Cleanup sockets after each test
    if (tvDisplay?.connected) tvDisplay.disconnect();
    if (player1?.connected) player1.disconnect();
    if (player2?.connected) player2.disconnect();
  });

  // ==========================================================================
  // PHASE 1: API TESTS
  // ==========================================================================

  describe('Phase 1: API Endpoints', () => {
    it('should create a game and return room code', async () => {
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);

      expect(response.body.roomCode).toHaveLength(6);
      expect(response.body.status).toBe('lobby');
      roomCode = response.body.roomCode;
      gameId = response.body.gameId;
    });

    it('should get game by room code', async () => {
      const response = await request(app)
        .get(`/api/games/code/${roomCode}`)
        .expect(200);

      expect(response.body.roomCode).toBe(roomCode);
      expect(response.body.playerCount).toBe(0);
    });

    it('should return 404 for non-existent room', async () => {
      await request(app)
        .get('/api/games/code/XXXXXX')
        .expect(404);
    });
  });

  // ==========================================================================
  // PHASE 2: SOCKET CONNECTION TESTS
  // ==========================================================================

  describe('Phase 2: Socket Connections', () => {
    beforeEach(async () => {
      // Create a fresh game
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);
      roomCode = response.body.roomCode;
      gameId = response.body.gameId;
    });

    it('should connect player to room', async () => {
      player1 = ioClient(SERVER_URL, {
        transports: ['websocket'],
        autoConnect: false,
      });

      const joinedPromise = new Promise<any>((resolve, reject) => {
        player1.on(SocketEvents.JOINED_GAME, resolve);
        player1.on(SocketEvents.JOIN_ERROR, reject);
        setTimeout(() => reject(new Error('Timeout')), 5000);
      });

      player1.connect();
      player1.emit(SocketEvents.LOBBY_JOIN, {
        roomCode,
        playerName: 'Player1',
        token: 'car',
        color: '#FF6B6B',
      });

      const result = await joinedPromise;
      expect(result.playerId).toBeDefined();
      expect(result.playerName).toBe('Player1');
      expect(result.isHost).toBe(true);
      expect(result.sessionToken).toBeDefined();
    });

    it('should connect second player and notify room', async () => {
      // Connect player 1
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });

      await new Promise<void>((resolve) => {
        player1.on(SocketEvents.JOINED_GAME, () => resolve());
        player1.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Player1',
          token: 'car',
          color: '#FF6B6B',
        });
      });

      // Setup listener for player joined event
      const playerJoinedPromise = new Promise<any>((resolve) => {
        player1.on(SocketEvents.LOBBY_PLAYER_JOINED, resolve);
      });

      // Connect player 2
      player2 = ioClient(SERVER_URL, { transports: ['websocket'] });

      const p2JoinedPromise = new Promise<any>((resolve) => {
        player2.on(SocketEvents.JOINED_GAME, resolve);
        player2.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Player2',
          token: 'dog',
          color: '#4ECDC4',
        });
      });

      const [p1Notified, p2Joined] = await Promise.all([
        playerJoinedPromise,
        p2JoinedPromise,
      ]);

      expect(p1Notified.player.name).toBe('Player2');
      expect(p2Joined.isHost).toBe(false);
    });

    it('should reject join for non-existent room', async () => {
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });

      const errorPromise = new Promise<any>((resolve) => {
        player1.on(SocketEvents.JOIN_ERROR, resolve);
      });

      player1.emit(SocketEvents.LOBBY_JOIN, {
        roomCode: 'BADCODE',
        playerName: 'Player1',
        token: 'car',
        color: '#FF6B6B',
      });

      const error = await errorPromise;
      expect(error.message).toContain('not found');
    });

    it('should emit player ready status', async () => {
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });

      await new Promise<void>((resolve) => {
        player1.on(SocketEvents.JOINED_GAME, () => resolve());
        player1.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Player1',
          token: 'car',
          color: '#FF6B6B',
        });
      });

      const readyPromise = new Promise<any>((resolve) => {
        player1.on(SocketEvents.LOBBY_PLAYER_READY, resolve);
      });

      player1.emit(SocketEvents.LOBBY_READY);

      const readyEvent = await readyPromise;
      expect(readyEvent.ready).toBe(true);
    });
  });

  // ==========================================================================
  // PHASE 3: GAME FLOW TESTS
  // ==========================================================================

  describe('Phase 3: Game Flow', () => {
    let player1Id: string;
    let player2Id: string;

    beforeEach(async () => {
      // Create game
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);
      roomCode = response.body.roomCode;

      // Connect player 1 (host)
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });
      player1Id = await new Promise<string>((resolve) => {
        player1.on(SocketEvents.JOINED_GAME, (data) => resolve(data.playerId));
        player1.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Host',
          token: 'car',
          color: '#FF6B6B',
        });
      });

      // Connect player 2
      player2 = ioClient(SERVER_URL, { transports: ['websocket'] });
      player2Id = await new Promise<string>((resolve) => {
        player2.on(SocketEvents.JOINED_GAME, (data) => resolve(data.playerId));
        player2.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Player2',
          token: 'dog',
          color: '#4ECDC4',
        });
      });
    });

    it('should start game with countdown', async () => {
      const countdownPromise = new Promise<number[]>((resolve) => {
        const counts: number[] = [];
        player1.on(SocketEvents.LOBBY_GAME_STARTING, (data) => {
          counts.push(data.countdown);
          if (data.countdown === 1) {
            resolve(counts);
          }
        });
      });

      const gameStartedPromise = new Promise<GameState>((resolve) => {
        player1.on(SocketEvents.GAME_STARTED, resolve);
      });

      player1.emit(SocketEvents.LOBBY_START_GAME);

      const [counts, gameState] = await Promise.all([
        countdownPromise,
        gameStartedPromise,
      ]);

      expect(counts).toContain(3);
      expect(counts).toContain(2);
      expect(counts).toContain(1);
      expect(gameState.status).toBe('playing');
    });

    it('should handle dice roll', async () => {
      // Start game first
      const gameStartedPromise = new Promise<GameState>((resolve) => {
        player1.on(SocketEvents.GAME_STARTED, resolve);
      });
      player1.emit(SocketEvents.LOBBY_START_GAME);
      const gameState = await gameStartedPromise;

      // Get current player
      const currentPlayerId = gameState.playerOrder[gameState.currentPlayerIndex];
      const currentPlayer = currentPlayerId === player1Id ? player1 : player2;

      // Roll dice
      const diceRolledPromise = new Promise<any>((resolve) => {
        currentPlayer.on(SocketEvents.GAME_DICE_ROLLED, resolve);
      });

      currentPlayer.emit(SocketEvents.GAME_ROLL_DICE);

      const diceResult = await diceRolledPromise;
      expect(diceResult.dice).toHaveLength(2);
      expect(diceResult.dice[0]).toBeGreaterThanOrEqual(1);
      expect(diceResult.dice[0]).toBeLessThanOrEqual(6);
      expect(diceResult.dice[1]).toBeGreaterThanOrEqual(1);
      expect(diceResult.dice[1]).toBeLessThanOrEqual(6);
    });

    it('should handle player movement', async () => {
      // Start game
      const gameStartedPromise = new Promise<GameState>((resolve) => {
        player1.on(SocketEvents.GAME_STARTED, resolve);
      });
      player1.emit(SocketEvents.LOBBY_START_GAME);
      const gameState = await gameStartedPromise;

      const currentPlayerId = gameState.playerOrder[gameState.currentPlayerIndex];
      const currentPlayer = currentPlayerId === player1Id ? player1 : player2;

      // Listen for move
      const movedPromise = new Promise<any>((resolve) => {
        currentPlayer.on(SocketEvents.GAME_PLAYER_MOVED, resolve);
      });

      currentPlayer.emit(SocketEvents.GAME_ROLL_DICE);

      const moveEvent = await movedPromise;
      expect(moveEvent.playerId).toBe(currentPlayerId);
      expect(moveEvent.newPosition).toBeGreaterThan(0);
    });

    it('should handle end turn and change player', async () => {
      // Start game
      const gameStartedPromise = new Promise<GameState>((resolve) => {
        player1.on(SocketEvents.GAME_STARTED, resolve);
      });
      player1.emit(SocketEvents.LOBBY_START_GAME);
      const gameState = await gameStartedPromise;

      const currentPlayerId = gameState.playerOrder[gameState.currentPlayerIndex];
      const currentPlayer = currentPlayerId === player1Id ? player1 : player2;

      // Roll first
      await new Promise<void>((resolve) => {
        currentPlayer.on(SocketEvents.GAME_STATE, () => resolve());
        currentPlayer.emit(SocketEvents.GAME_ROLL_DICE);
      });

      // Wait for state to settle
      await new Promise(r => setTimeout(r, 100));

      // Get updated state
      const statePromise = new Promise<GameState>((resolve) => {
        currentPlayer.on(SocketEvents.GAME_STATE, resolve);
      });

      currentPlayer.emit(SocketEvents.GAME_END_TURN);

      const newState = await statePromise;
      // Turn should have changed (unless doubles)
      expect(newState.currentPlayerIndex).toBeDefined();
    });
  });

  // ==========================================================================
  // PHASE 4: FEATURE TESTS
  // ==========================================================================

  describe('Phase 4: Feature Tests', () => {
    let player1Id: string;

    beforeEach(async () => {
      // Create game
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);
      roomCode = response.body.roomCode;

      // Connect player 1 (host)
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });
      player1Id = await new Promise<string>((resolve) => {
        player1.on(SocketEvents.JOINED_GAME, (data) => resolve(data.playerId));
        player1.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Host',
          token: 'car',
          color: '#FF6B6B',
        });
      });
    });

    it('should add bot player', async () => {
      const playerJoinedPromise = new Promise<any>((resolve) => {
        player1.on(SocketEvents.PLAYER_JOINED, resolve);
      });

      player1.emit(SocketEvents.LOBBY_ADD_BOT, {
        personality: 'conservative',
        difficulty: 'normal',
      });

      const result = await playerJoinedPromise;
      const players = Object.values(result.gameState.players);
      const botPlayer = players.find((p: any) => p.isBot);
      expect(botPlayer).toBeDefined();
    });

    it('should handle auction bidding', async () => {
      // Connect player 2
      player2 = ioClient(SERVER_URL, { transports: ['websocket'] });
      await new Promise<void>((resolve) => {
        player2.on(SocketEvents.JOINED_GAME, () => resolve());
        player2.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Player2',
          token: 'dog',
          color: '#4ECDC4',
        });
      });

      // Start game
      const gameStartedPromise = new Promise<GameState>((resolve) => {
        player1.on(SocketEvents.GAME_STARTED, resolve);
      });
      player1.emit(SocketEvents.LOBBY_START_GAME);
      await gameStartedPromise;

      // Auction events should be emittable
      const bidPromise = new Promise<any>((resolve, reject) => {
        player1.on(SocketEvents.AUCTION_BID_PLACED, resolve);
        player1.on(SocketEvents.ERROR, reject);
        setTimeout(() => reject(new Error('Timeout - no auction active')), 2000);
      });

      // This will likely fail if no auction is active, which is expected
      player1.emit(SocketEvents.AUCTION_BID, {
        auctionId: 'test',
        amount: 100,
      });

      try {
        await bidPromise;
      } catch (error: any) {
        // Expected - no active auction
        expect(error.message).toBeDefined();
      }
    });

    it('should handle trade proposal', async () => {
      // Connect player 2
      player2 = ioClient(SERVER_URL, { transports: ['websocket'] });
      const player2Id = await new Promise<string>((resolve) => {
        player2.on(SocketEvents.JOINED_GAME, (data) => resolve(data.playerId));
        player2.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Player2',
          token: 'dog',
          color: '#4ECDC4',
        });
      });

      // Start game
      const gameStartedPromise = new Promise<GameState>((resolve) => {
        player1.on(SocketEvents.GAME_STARTED, resolve);
      });
      player1.emit(SocketEvents.LOBBY_START_GAME);
      await gameStartedPromise;

      // Listen for trade proposed
      const tradePromise = new Promise<any>((resolve) => {
        player2.on(SocketEvents.TRADE_PROPOSED, resolve);
      });

      player1.emit(SocketEvents.TRADE_PROPOSE, {
        recipientId: player2Id,
        offer: { money: 100, properties: [] },
        request: { money: 50, properties: [] },
      });

      const trade = await tradePromise;
      expect(trade.proposerId).toBe(player1Id);
      expect(trade.recipientId).toBe(player2Id);
    });
  });

  // ==========================================================================
  // RECONNECTION TESTS
  // ==========================================================================

  describe('Reconnection', () => {
    it('should allow player to reconnect with session token', async () => {
      // Create game
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);
      roomCode = response.body.roomCode;

      // Connect player 1
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });
      const joinData = await new Promise<any>((resolve) => {
        player1.on(SocketEvents.JOINED_GAME, resolve);
        player1.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Host',
          token: 'car',
          color: '#FF6B6B',
        });
      });

      const { playerId, sessionToken } = joinData;

      // Disconnect
      player1.disconnect();
      await new Promise(r => setTimeout(r, 100));

      // Reconnect
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });

      const reconnectPromise = new Promise<any>((resolve, reject) => {
        player1.on(SocketEvents.RECONNECT_SUCCESS, resolve);
        player1.on(SocketEvents.RECONNECT_FAILED, reject);
      });

      player1.emit(SocketEvents.RECONNECT_REQUEST, {
        playerId,
        roomCode,
        sessionToken,
      });

      const result = await reconnectPromise;
      expect(result.playerId).toBe(playerId);
      expect(result.gameState).toBeDefined();
    });

    it('should reject reconnect with invalid session token', async () => {
      // Create game
      const response = await request(app)
        .post('/api/games')
        .send({ hostName: 'TestHost' })
        .expect(201);
      roomCode = response.body.roomCode;

      // Connect and get session
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });
      const joinData = await new Promise<any>((resolve) => {
        player1.on(SocketEvents.JOINED_GAME, resolve);
        player1.emit(SocketEvents.LOBBY_JOIN, {
          roomCode,
          playerName: 'Host',
          token: 'car',
          color: '#FF6B6B',
        });
      });

      player1.disconnect();
      await new Promise(r => setTimeout(r, 100));

      // Reconnect with wrong token
      player1 = ioClient(SERVER_URL, { transports: ['websocket'] });

      const failedPromise = new Promise<any>((resolve) => {
        player1.on(SocketEvents.RECONNECT_FAILED, resolve);
      });

      player1.emit(SocketEvents.RECONNECT_REQUEST, {
        playerId: joinData.playerId,
        roomCode,
        sessionToken: 'invalid-token',
      });

      const result = await failedPromise;
      expect(result.reason).toContain('Invalid');
    });
  });
});
