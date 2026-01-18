import { useCallback, useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useGameStore } from '../store/gameStore';
import { SocketEvents } from '@pinopoly/shared';
import type { GameState, GameEvent } from '@pinopoly/game-engine';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

/**
 * CLEAN ARCHITECTURE - TV Display Socket Hook
 *
 * Key Principle: GAME_STATE is the ONLY event that updates state.
 * Animation events trigger UI effects only, they do NOT update state.
 */

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  connect: (roomCode: string) => void;
  disconnect: () => void;
  emit: (event: string, data?: any) => void;
}

export function useSocket(): UseSocketReturn {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const {
    setRoomCode,
    setGameState,
    addEvent,
    setDiceRoll,
    setIsRolling,
    setMovingPlayer,
    reset,
  } = useGameStore();

  const connect = useCallback((roomCode: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.disconnect();
    }

    const socket = io(SOCKET_URL, {
      query: { roomCode, role: 'display' },
      transports: ['websocket', 'polling'],
    });

    socketRef.current = socket;

    // ===========================================
    // CONNECTION EVENTS
    // ===========================================

    socket.on('connect', () => {
      console.log('[TV Socket] Connected');
      setIsConnected(true);
      setRoomCode(roomCode);

      // Authenticate as display
      socket.emit(SocketEvents.AUTH_DISPLAY, { gameCode: roomCode });
    });

    socket.on('disconnect', () => {
      console.log('[TV Socket] Disconnected');
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('[TV Socket] Connection error:', error);
      setIsConnected(false);
    });

    // ===========================================
    // STATE EVENTS - These update the Zustand store
    // ===========================================

    // GAME_STATE - THE SINGLE SOURCE OF TRUTH
    // This is the ONLY event that should update game state
    socket.on(SocketEvents.GAME_STATE, (state: GameState) => {
      console.log('[TV Socket] Game state update, phase:', state.phase, 'round:', state.round);
      console.log('[TV Socket] Player positions:', Object.values(state.players).map(p => ({ name: p.name, position: p.position })));
      setGameState(state);
    });

    // ===========================================
    // ANIMATION EVENTS - UI effects only, NO state updates
    // ===========================================

    // Dice roll animation
    socket.on(SocketEvents.GAME_DICE_ROLLED, (data: {
      playerId: string;
      dice: [number, number];
    }) => {
      console.log('[TV Socket] Dice rolled:', data.dice);
      setIsRolling(false);
      setDiceRoll(data.dice);
      setMovingPlayer(data.playerId);

      // Auto-clear dice after animation
      setTimeout(() => {
        setDiceRoll(null);
      }, 3000);
    });

    // Player movement animation
    socket.on(SocketEvents.GAME_PLAYER_MOVED, (data: {
      playerId: string;
      from: number;
      to: number;
      spaces: number;
    }) => {
      console.log('[TV Socket] Player moved:', data.from, '->', data.to);
      setMovingPlayer(data.playerId);

      // Auto-clear after animation (adjust timing based on spaces)
      setTimeout(() => {
        setMovingPlayer(null);
      }, 1500 + (data.spaces * 200));
    });

    // Card reveal animation
    socket.on(SocketEvents.GAME_CARD_DRAWN, (data: {
      playerId: string;
      cardId: string;
      deck: 'chance' | 'community_chest';
    }) => {
      console.log('[TV Socket] Card drawn:', data.cardId);
      addEvent({
        id: `card-${Date.now()}`,
        type: 'CARD_DRAWN',
        playerId: data.playerId,
        payload: { cardId: data.cardId, deck: data.deck },
        round: 0,
        timestamp: Date.now(),
      });
    });

    // ===========================================
    // EVENT LOG - For UI event display only
    // ===========================================

    socket.on(SocketEvents.GAME_EVENT, (event: GameEvent) => {
      addEvent(event);
    });

    socket.connect();
  }, [setRoomCode, setGameState, addEvent, setDiceRoll, setIsRolling, setMovingPlayer]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    reset();
  }, [reset]);

  // Generic emit function
  const emit = useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  return {
    socket: socketRef.current,
    isConnected,
    connect,
    disconnect,
    emit,
  };
}
