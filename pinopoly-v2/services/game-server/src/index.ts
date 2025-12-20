/**
 * Pinopoly Game Server
 * Main entry point
 */

import 'dotenv/config';
import { createServer } from 'http';
import { app } from './app';
import { createSocketServer, setRoomManager } from './socket/SocketServer';
import { RoomManager } from './socket/RoomManager';
import { prisma } from './db/client';
import { createBotWorker } from './workers/BotWorker';
import { config } from './config';

async function main() {
  // Create HTTP server
  const httpServer = createServer(app);

  // Initialize Socket.IO
  const io = createSocketServer(httpServer);

  // Initialize Room Manager
  const roomManager = new RoomManager(io, prisma);

  // Set RoomManager reference for socket handlers
  setRoomManager(roomManager);

  // Attach room manager to app for route access
  app.set('roomManager', roomManager);
  app.set('io', io);

  // Initialize Bot Worker (if Redis available)
  if (config.redis.url) {
    try {
      const botWorker = createBotWorker((gameId, decision) => {
        roomManager.handleBotDecision(gameId, decision);
      });
      console.log('Bot worker initialized');
    } catch (error) {
      console.warn('Bot worker not available (Redis connection failed)');
    }
  }

  // Start server
  httpServer.listen(config.port, () => {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║                    PINOPOLY GAME SERVER                     ║
╠════════════════════════════════════════════════════════════╣
║  Version:     2.0.0                                         ║
║  Environment: ${config.nodeEnv.padEnd(43)}║
║  Port:        ${String(config.port).padEnd(43)}║
║  API:         http://localhost:${config.port}/api${' '.repeat(23)}║
║  WebSocket:   ws://localhost:${config.port}/socket.io${' '.repeat(15)}║
║  Health:      http://localhost:${config.port}/health${' '.repeat(19)}║
╚════════════════════════════════════════════════════════════╝
    `);
  });

  // Graceful shutdown
  const shutdown = async () => {
    console.log('\nShutting down gracefully...');

    // Close socket connections
    io.close();

    // Close database connection
    await prisma.$disconnect();

    // Close HTTP server
    httpServer.close(() => {
      console.log('Server closed');
      process.exit(0);
    });

    // Force exit after timeout
    setTimeout(() => {
      console.error('Forced shutdown after timeout');
      process.exit(1);
    }, 10000);
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
