import { useCallback, useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { usePlayerStore } from '../store/playerStore';
import { SocketEvents } from '@pinopoly/shared';
import type { GameState } from '@pinopoly/game-engine';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

// Module-level singleton socket instance - shared across all components
let socketInstance: Socket | null = null;
let isSocketInitialized = false;

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  joinGame: (roomCode: string, playerName: string, token: string) => void;
  disconnect: () => void;
  emit: (event: string, data?: any) => void;
}

export function useSocket(): UseSocketReturn {
  const [isConnected, setIsConnected] = useState(socketInstance?.connected ?? false);

  const {
    setPlayer,
    setRoomCode,
    setGameState,
    setIsHost,
    reset,
  } = usePlayerStore();

  // Initialize socket connection (singleton pattern)
  const initSocket = useCallback(() => {
    if (socketInstance?.connected) return socketInstance;
    if (isSocketInitialized && socketInstance) return socketInstance;

    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: false,
    });

    socketInstance = socket;
    isSocketInitialized = true;

    socket.on('connect', () => {
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setIsConnected(false);
    });

    // Game events
    socket.on(SocketEvents.JOINED_GAME, (data: {
      playerId: string;
      playerName: string;
      token: string;
      isHost: boolean;
      gameState: GameState;
    }) => {
      setPlayer(data.playerId, data.playerName, data.token);
      setIsHost(data.isHost);
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.JOIN_ERROR, (error: { message: string }) => {
      console.error('Join error:', error.message);
      alert(error.message);
    });

    socket.on(SocketEvents.GAME_STATE, (state: GameState) => {
      setGameState(state);
    });

    socket.on(SocketEvents.PLAYER_JOINED, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.PLAYER_LEFT, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.GAME_STARTED, (state: GameState) => {
      setGameState(state);
    });

    socket.on(SocketEvents.TURN_CHANGED, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.DICE_RESULT, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.PROPERTY_PURCHASED, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.RENT_PAID, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.GAME_ENDED, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.KICKED, () => {
      alert('You have been kicked from the game');
      reset();
    });

    return socket;
  }, [setPlayer, setRoomCode, setGameState, setIsHost, reset]);

  // Sync connection state when socket already exists
  useEffect(() => {
    if (socketInstance) {
      setIsConnected(socketInstance.connected);

      const handleConnect = () => setIsConnected(true);
      const handleDisconnect = () => setIsConnected(false);

      socketInstance.on('connect', handleConnect);
      socketInstance.on('disconnect', handleDisconnect);

      return () => {
        socketInstance?.off('connect', handleConnect);
        socketInstance?.off('disconnect', handleDisconnect);
      };
    }
  }, []);

  // Join game
  const joinGame = useCallback((roomCode: string, playerName: string, token: string, color?: string) => {
    const socket = initSocket();
    if (!socket) return;

    setRoomCode(roomCode);

    if (!socket.connected) {
      socket.connect();
    }

    // Use provided color or pick one based on token
    const playerColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'];
    const tokenIndex = ['car', 'dog', 'hat', 'ship', 'boot', 'thimble', 'iron', 'wheelbarrow'].indexOf(token);
    const assignedColor = color || playerColors[tokenIndex >= 0 ? tokenIndex : 0];

    socket.emit(SocketEvents.JOIN_GAME, {
      roomCode: roomCode.toUpperCase(),
      playerName,
      token,
      color: assignedColor,
    });
  }, [initSocket, setRoomCode]);

  // Disconnect
  const disconnect = useCallback(() => {
    if (socketInstance) {
      socketInstance.disconnect();
      socketInstance = null;
      isSocketInitialized = false;
    }
    reset();
  }, [reset]);

  // Generic emit - uses module-level socket
  const emit = useCallback((event: string, data?: any) => {
    if (socketInstance?.connected) {
      console.log('[useSocket] Emitting:', event, data);
      socketInstance.emit(event, data);
    } else {
      console.warn('[useSocket] Cannot emit, socket not connected:', event);
    }
  }, []);

  return {
    socket: socketInstance,
    isConnected,
    joinGame,
    disconnect,
    emit,
  };
}
