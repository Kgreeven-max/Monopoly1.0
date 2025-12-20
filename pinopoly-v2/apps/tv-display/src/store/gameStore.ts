import { create } from 'zustand';
import type { GameState, PlayerState, GameEvent } from '@pinopoly/game-engine';

interface GameStore {
  // Connection state
  roomCode: string | null;
  isHost: boolean;

  // Game state
  gameState: GameState | null;

  // Recent events for display
  recentEvents: GameEvent[];
  maxRecentEvents: number;

  // Dice display
  lastDiceRoll: [number, number] | null;
  isRolling: boolean;

  // Animation state
  movingPlayer: string | null;

  // Actions
  setRoomCode: (code: string) => void;
  setIsHost: (isHost: boolean) => void;
  setGameState: (state: GameState) => void;
  addEvent: (event: GameEvent) => void;
  setDiceRoll: (dice: [number, number] | null) => void;
  setIsRolling: (rolling: boolean) => void;
  setMovingPlayer: (playerId: string | null) => void;
  reset: () => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  roomCode: null,
  isHost: false,
  gameState: null,
  recentEvents: [],
  maxRecentEvents: 10,
  lastDiceRoll: null,
  isRolling: false,
  movingPlayer: null,

  // Actions
  setRoomCode: (code) => set({ roomCode: code }),

  setIsHost: (isHost) => set({ isHost }),

  setGameState: (state) => set({ gameState: state }),

  addEvent: (event) => set((state) => ({
    recentEvents: [event, ...state.recentEvents].slice(0, state.maxRecentEvents),
  })),

  setDiceRoll: (dice) => set({ lastDiceRoll: dice }),

  setIsRolling: (rolling) => set({ isRolling: rolling }),

  setMovingPlayer: (playerId) => set({ movingPlayer: playerId }),

  reset: () => set({
    roomCode: null,
    isHost: false,
    gameState: null,
    recentEvents: [],
    lastDiceRoll: null,
    isRolling: false,
    movingPlayer: null,
  }),
}));

// Selectors
export const useCurrentPlayer = (): PlayerState | null => {
  return useGameStore((state) => {
    if (!state.gameState) return null;
    const playerId = state.gameState.playerOrder[state.gameState.currentPlayerIndex];
    return state.gameState.players[playerId] || null;
  });
};

export const usePlayers = (): PlayerState[] => {
  return useGameStore((state) => {
    if (!state.gameState) return [];
    return state.gameState.playerOrder.map(id => state.gameState!.players[id]);
  });
};

export const usePlayerById = (playerId: string): PlayerState | null => {
  return useGameStore((state) => {
    if (!state.gameState) return null;
    return state.gameState.players[playerId] || null;
  });
};
