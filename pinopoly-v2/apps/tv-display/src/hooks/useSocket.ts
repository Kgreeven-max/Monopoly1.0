import { useCallback, useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useGameStore } from '../store/gameStore';
import { SocketEvents } from '@pinopoly/shared';
import type { GameState, GameEvent } from '@pinopoly/game-engine';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

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

    // Connection events
    socket.on('connect', () => {
      setIsConnected(true);
      setRoomCode(roomCode);

      // Authenticate as display
      socket.emit(SocketEvents.AUTH_DISPLAY, { gameCode: roomCode });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setIsConnected(false);
    });

    // Game state events
    socket.on(SocketEvents.GAME_STATE, (state: GameState) => {
      setGameState(state);
    });

    socket.on(SocketEvents.PLAYER_JOINED, (data: { player: any; gameState: GameState }) => {
      setGameState(data.gameState);
      addEvent({
        type: 'PLAYER_JOINED',
        playerId: data.player.id,
        data: { playerName: data.player.name },
        timestamp: Date.now(),
      });
    });

    socket.on(SocketEvents.PLAYER_LEFT, (data: { playerId: string; gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.GAME_STARTED, (state: GameState) => {
      setGameState(state);
    });

    // Dice roll animation
    socket.on(SocketEvents.DICE_ROLLING, () => {
      setIsRolling(true);
    });

    socket.on(SocketEvents.DICE_RESULT, (data: { dice: [number, number]; playerId: string }) => {
      setIsRolling(false);
      setDiceRoll(data.dice);
      setMovingPlayer(data.playerId);
    });

    // Movement complete
    socket.on(SocketEvents.MOVEMENT_COMPLETE, () => {
      setMovingPlayer(null);
    });

    // Game events for the event log
    socket.on(SocketEvents.GAME_EVENT, (event: GameEvent) => {
      addEvent(event);
    });

    // Turn change
    socket.on(SocketEvents.TURN_CHANGED, (data: { playerId: string; gameState: GameState }) => {
      setGameState(data.gameState);
    });

    // Property events
    socket.on(SocketEvents.PROPERTY_PURCHASED, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    socket.on(SocketEvents.RENT_PAID, (data: { gameState: GameState }) => {
      setGameState(data.gameState);
    });

    // Game end
    socket.on(SocketEvents.GAME_ENDED, (data: { gameState: GameState; winner: any }) => {
      setGameState(data.gameState);
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
