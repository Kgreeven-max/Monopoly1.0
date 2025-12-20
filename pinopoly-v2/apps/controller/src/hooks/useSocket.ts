import { useCallback, useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { usePlayerStore } from '../store/playerStore';
import { useAnimation } from '../contexts/AnimationContext';
import { SocketEvents } from '@pinopoly/shared';
import type { GameState } from '@pinopoly/game-engine';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

/**
 * CLEAN ARCHITECTURE - Socket Hook
 *
 * Key Principle: GAME_STATE is the ONLY event that updates state.
 * Animation events trigger UI effects only, they do NOT update state.
 */

// Module-level singleton socket instance - shared across all components
let socketInstance: Socket | null = null;
let isSocketInitialized = false;

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  joinGame: (roomCode: string, playerName: string, token: string, color?: string) => void;
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

  // Animation context - for triggering UI effects
  const animation = useAnimation();

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

    // ===========================================
    // CONNECTION EVENTS
    // ===========================================

    socket.on('connect', () => {
      console.log('[Socket] Connected');
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('[Socket] Disconnected');
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('[Socket] Connection error:', error);
      setIsConnected(false);
    });

    // ===========================================
    // STATE EVENTS - These update the Zustand store
    // ===========================================

    // Initial join - sets up player identity and initial state
    socket.on(SocketEvents.JOINED_GAME, (data: {
      playerId: string;
      playerName: string;
      token: string;
      isHost: boolean;
      gameState: GameState;
    }) => {
      console.log('[Socket] Joined game:', data.playerId);
      setPlayer(data.playerId, data.playerName, data.token);
      setIsHost(data.isHost);
      setGameState(data.gameState);
    });

    // GAME_STATE - THE SINGLE SOURCE OF TRUTH
    // This is the ONLY event that should update game state
    socket.on(SocketEvents.GAME_STATE, (state: GameState) => {
      console.log('[Socket] Game state update, phase:', state.phase, 'round:', state.round);
      setGameState(state);
    });

    // ===========================================
    // ERROR EVENTS
    // ===========================================

    socket.on(SocketEvents.JOIN_ERROR, (error: { message: string }) => {
      console.error('[Socket] Join error:', error.message);
      alert(error.message);
    });

    socket.on(SocketEvents.ERROR, (error: { code: string; message: string }) => {
      console.error('[Socket] Error:', error.code, error.message);
    });

    socket.on(SocketEvents.KICKED, () => {
      alert('You have been kicked from the game');
      reset();
    });

    // ===========================================
    // ANIMATION EVENTS - UI effects only, NO state updates
    // ===========================================

    // Dice roll animation
    socket.on(SocketEvents.GAME_DICE_ROLLED, (data: {
      playerId: string;
      dice: [number, number];
    }) => {
      console.log('[Socket] Dice rolled:', data.dice);
      animation.showDiceResult(data.dice);
    });

    // Player movement animation
    socket.on(SocketEvents.GAME_PLAYER_MOVED, (data: {
      playerId: string;
      from: number;
      to: number;
      spaces: number;
    }) => {
      console.log('[Socket] Player moved:', data.from, '->', data.to);
      animation.startPlayerMove(data.playerId, data.from, data.to, data.spaces);
    });

    // Card reveal animation
    socket.on(SocketEvents.GAME_CARD_DRAWN, (data: {
      playerId: string;
      cardId: string;
      deck: 'chance' | 'community_chest';
    }) => {
      console.log('[Socket] Card drawn:', data.cardId);
      animation.startCardReveal(data.cardId, data.deck);
    });

    return socket;
  }, [setPlayer, setRoomCode, setGameState, setIsHost, reset, animation]);

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
      console.log('[Socket] Emit:', event, data);
      socketInstance.emit(event, data);
    } else {
      console.warn('[Socket] Cannot emit, not connected:', event);
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
