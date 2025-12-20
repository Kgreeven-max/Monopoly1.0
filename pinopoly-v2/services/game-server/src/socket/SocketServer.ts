/**
 * Socket.IO Server Setup
 */

import { Server as HttpServer } from 'http';
import { Server, Socket } from 'socket.io';
import { config } from '../config';
import { SocketEvents } from '@pinopoly/shared';
import { verifyToken } from '../services/AuthService';
import type { RoomManager } from './RoomManager';

export interface AuthenticatedSocket extends Socket {
  playerId?: string;
  gameId?: string;
  role?: 'player' | 'display' | 'admin';
}

// Reference to RoomManager set after initialization
let roomManagerRef: RoomManager | null = null;

export function setRoomManager(rm: RoomManager): void {
  roomManagerRef = rm;
}

export function createSocketServer(httpServer: HttpServer): Server {
  const io = new Server(httpServer, {
    cors: {
      origin: config.cors.origins,
      credentials: true,
    },
    path: '/socket.io',
    transports: ['websocket', 'polling'],
    pingTimeout: 60000,
    pingInterval: 25000,
  });

  // Connection logging
  io.on('connection', (socket: AuthenticatedSocket) => {
    console.log(`Socket connected: ${socket.id}`);

    // Handle authentication
    socket.on(SocketEvents.AUTH_PLAYER, async (data) => {
      try {
        const { token, gameCode } = data;
        const decoded = verifyToken(token);

        if (!decoded) {
          socket.emit(SocketEvents.AUTH_ERROR, { message: 'Invalid token' });
          return;
        }

        socket.playerId = decoded.playerId;
        socket.gameId = decoded.gameId;
        socket.role = 'player';

        // Join game room
        socket.join(gameCode);
        socket.join(`player:${decoded.playerId}`);

        socket.emit(SocketEvents.AUTH_SUCCESS, {
          playerId: decoded.playerId,
          playerName: decoded.playerName,
          role: 'player',
        });

        console.log(`Player authenticated: ${decoded.playerName} in game ${gameCode}`);
      } catch (error) {
        socket.emit(SocketEvents.AUTH_ERROR, { message: 'Authentication failed' });
      }
    });

    socket.on(SocketEvents.AUTH_DISPLAY, async (data) => {
      try {
        const { gameCode } = data;

        // Simple display token validation
        socket.role = 'display';
        socket.gameId = gameCode;

        socket.join(gameCode);
        socket.join(`display:${gameCode}`);

        socket.emit(SocketEvents.AUTH_SUCCESS, {
          role: 'display',
        });

        // Send initial game state if room exists
        if (roomManagerRef) {
          const room = roomManagerRef.getRoom(gameCode);
          if (room) {
            socket.emit(SocketEvents.GAME_STATE, room.state);
            console.log(`Display connected to game ${gameCode} - sent initial state`);
          } else {
            console.log(`Display connected to game ${gameCode} - no room found yet`);
          }
        } else {
          console.log(`Display connected to game ${gameCode} - roomManager not ready`);
        }
      } catch (error) {
        socket.emit(SocketEvents.AUTH_ERROR, { message: 'Display authentication failed' });
      }
    });

    socket.on(SocketEvents.AUTH_ADMIN, async (data) => {
      try {
        const { adminToken } = data;

        if (adminToken !== config.admin.token) {
          socket.emit(SocketEvents.AUTH_ERROR, { message: 'Invalid admin token' });
          return;
        }

        socket.role = 'admin';
        socket.join('admin');

        socket.emit(SocketEvents.AUTH_SUCCESS, {
          role: 'admin',
        });

        console.log('Admin connected');
      } catch (error) {
        socket.emit(SocketEvents.AUTH_ERROR, { message: 'Admin authentication failed' });
      }
    });

    // Disconnect handling
    socket.on('disconnect', (reason) => {
      console.log(`Socket disconnected: ${socket.id} - ${reason}`);

      if (socket.playerId && socket.gameId) {
        // Notify room of disconnection
        io.to(socket.gameId).emit('player:disconnected', {
          playerId: socket.playerId,
        });
      }
    });

    // Error handling
    socket.on('error', (error) => {
      console.error(`Socket error: ${socket.id}`, error);
    });
  });

  return io;
}

export type { Server };
