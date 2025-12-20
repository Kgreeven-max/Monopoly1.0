import { useCallback, useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { usePlayerStore } from '../store/playerStore';
import { SocketEvents } from '@pinopoly/shared';
import type { GameState } from '@pinopoly/game-engine';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || '';

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  joinGame: (roomCode: string, playerName: string, token: string) => void;
  disconnect: () => void;
  emit: (event: string, data?: any) => void;
}

export function useSocket(): UseSocketReturn {
  const socketRef = useRef<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const {
    setPlayer,
    setRoomCode,
    setGameState,
    setIsHost,
    reset,
  } = usePlayerStore();

  // Initialize socket connection
  const initSocket = useCallback(() => {
    if (socketRef.current?.connected) return;

    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: false,
    });

    socketRef.current = socket;

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
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    reset();
  }, [reset]);

  // Generic emit
  const emit = useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  }, []);

  // NOTE: We intentionally do NOT disconnect on component unmount.
  // The socket should persist across screen changes (JoinScreen -> LobbyScreen -> GameScreen).
  // Only disconnect when explicitly called via disconnect() function (e.g., when leaving game).
  // The socket will be cleaned up when the browser tab closes or user navigates away.

  return {
    socket: socketRef.current,
    isConnected,
    joinGame,
    disconnect,
    emit,
  };
}
