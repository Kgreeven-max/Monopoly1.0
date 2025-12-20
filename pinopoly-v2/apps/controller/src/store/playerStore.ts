import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { GameState, PlayerState } from '@pinopoly/game-engine';

interface PlayerStore {
  // Player identity
  playerId: string | null;
  playerName: string | null;
  token: string | null;
  isHost: boolean;

  // Connection state
  roomCode: string | null;

  // Game state
  gameState: GameState | null;

  // UI state
  showPropertyDetails: number | null;
  pendingAction: string | null;

  // Actions
  setPlayer: (id: string, name: string, token: string) => void;
  setIsHost: (isHost: boolean) => void;
  setRoomCode: (code: string) => void;
  setGameState: (state: GameState) => void;
  showProperty: (position: number | null) => void;
  setPendingAction: (action: string | null) => void;
  reset: () => void;
}

export const usePlayerStore = create<PlayerStore>()(
  persist(
    (set) => ({
      // Initial state
      playerId: null,
      playerName: null,
      token: null,
      isHost: false,
      roomCode: null,
      gameState: null,
      showPropertyDetails: null,
      pendingAction: null,

      // Actions
      setPlayer: (id, name, token) => set({
        playerId: id,
        playerName: name,
        token,
      }),

      setIsHost: (isHost) => set({ isHost }),

      setRoomCode: (code) => set({ roomCode: code }),

      setGameState: (state) => set({ gameState: state }),

      showProperty: (position) => set({ showPropertyDetails: position }),

      setPendingAction: (action) => set({ pendingAction: action }),

      reset: () => set({
        playerId: null,
        playerName: null,
        token: null,
        isHost: false,
        roomCode: null,
        gameState: null,
        showPropertyDetails: null,
        pendingAction: null,
      }),
    }),
    {
      name: 'pinopoly-player',
      partialize: (state) => ({
        playerName: state.playerName,
        token: state.token,
      }),
    }
  )
);

// Selectors
export const useMyPlayer = (): PlayerState | null => {
  return usePlayerStore((state) => {
    if (!state.gameState || !state.playerId) return null;
    return state.gameState.players[state.playerId] || null;
  });
};

export const useIsMyTurn = (): boolean => {
  return usePlayerStore((state) => {
    if (!state.gameState || !state.playerId) return false;
    const currentPlayerId = state.gameState.playerOrder[state.gameState.currentPlayerIndex];
    return currentPlayerId === state.playerId;
  });
};

export const useCurrentPhase = (): string | null => {
  return usePlayerStore((state) => state.gameState?.phase || null);
};

export const useMyProperties = () => {
  return usePlayerStore((state) => {
    if (!state.gameState || !state.playerId) return [];
    return Object.entries(state.gameState.properties)
      .filter(([_, prop]) => prop.ownerId === state.playerId)
      .map(([pos, prop]) => ({ position: parseInt(pos), ...prop }));
  });
};
