import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface GameSummary {
  id: string;
  roomCode: string;
  status: 'lobby' | 'playing' | 'paused' | 'finished';
  playerCount: number;
  hostName: string;
  startedAt?: string;
  createdAt: string;
}

interface SystemStats {
  activeGames: number;
  totalPlayers: number;
  gamesPlayedToday: number;
  serverUptime: number;
  memoryUsage: number;
  cpuUsage: number;
}

interface AdminStore {
  // Auth state
  isAuthenticated: boolean;
  adminToken: string | null;

  // Data
  games: GameSummary[];
  stats: SystemStats | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (adminKey: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => void;
  fetchGames: () => Promise<void>;
  fetchStats: () => Promise<void>;
  endGame: (gameId: string) => Promise<void>;
  kickPlayer: (gameId: string, playerId: string) => Promise<void>;
}

export const useAdminStore = create<AdminStore>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      adminToken: null,
      games: [],
      stats: null,
      isLoading: false,
      error: null,

      // Auth actions
      login: async (adminKey: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/admin/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adminKey }),
          });

          if (!response.ok) {
            throw new Error('Invalid admin key');
          }

          const data = await response.json();
          set({
            isAuthenticated: true,
            adminToken: data.token,
            isLoading: false,
          });
          return true;
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
          });
          return false;
        }
      },

      logout: () => {
        set({
          isAuthenticated: false,
          adminToken: null,
          games: [],
          stats: null,
        });
      },

      checkAuth: () => {
        const { adminToken } = get();
        if (adminToken) {
          // Verify token is still valid
          fetch('/api/admin/status', {
            headers: { Authorization: `Bearer ${adminToken}` },
          }).catch(() => {
            set({ isAuthenticated: false, adminToken: null });
          });
        }
      },

      // Data actions
      fetchGames: async () => {
        const { adminToken } = get();
        if (!adminToken) return;

        set({ isLoading: true });
        try {
          const response = await fetch('/api/admin/games/active', {
            headers: { Authorization: `Bearer ${adminToken}` },
          });

          if (!response.ok) throw new Error('Failed to fetch games');

          const data = await response.json();
          set({ games: data.games, isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch games',
            isLoading: false,
          });
        }
      },

      fetchStats: async () => {
        const { adminToken } = get();
        if (!adminToken) return;

        try {
          const response = await fetch('/api/admin/status', {
            headers: { Authorization: `Bearer ${adminToken}` },
          });

          if (!response.ok) throw new Error('Failed to fetch stats');

          const data = await response.json();
          set({ stats: data });
        } catch (error) {
          console.error('Failed to fetch stats:', error);
        }
      },

      endGame: async (gameId: string) => {
        const { adminToken } = get();
        if (!adminToken) return;

        try {
          const response = await fetch(`/api/admin/games/${gameId}/end`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${adminToken}` },
          });

          if (!response.ok) throw new Error('Failed to end game');

          // Refresh games list
          get().fetchGames();
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to end game',
          });
        }
      },

      kickPlayer: async (gameId: string, playerId: string) => {
        const { adminToken } = get();
        if (!adminToken) return;

        try {
          const response = await fetch(`/api/admin/games/${gameId}/kick/${playerId}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${adminToken}` },
          });

          if (!response.ok) throw new Error('Failed to kick player');

          // Refresh games list
          get().fetchGames();
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to kick player',
          });
        }
      },
    }),
    {
      name: 'pinopoly-admin',
      partialize: (state) => ({
        adminToken: state.adminToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
