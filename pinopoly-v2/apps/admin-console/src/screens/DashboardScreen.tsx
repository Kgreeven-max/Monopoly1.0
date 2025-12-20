import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAdminStore } from '../store/adminStore';
import { StatsCards } from '../components/StatsCards';
import { GamesList } from '../components/GamesList';
import { GameDetails } from '../components/GameDetails';

export function DashboardScreen() {
  const { games, stats, fetchGames, fetchStats, logout } = useAdminStore();
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);

  // Fetch data on mount and periodically
  useEffect(() => {
    fetchGames();
    fetchStats();

    const interval = setInterval(() => {
      fetchGames();
      fetchStats();
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [fetchGames, fetchStats]);

  const selectedGame = games.find(g => g.id === selectedGameId);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🎮</span>
            <h1 className="text-xl font-bold text-white">Pinopoly Admin</h1>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">
              {games.length} active games
            </span>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white
                       bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-lg font-semibold text-white mb-4">System Overview</h2>
          <StatsCards stats={stats} />
        </motion.div>

        {/* Games section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Games list */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2"
          >
            <h2 className="text-lg font-semibold text-white mb-4">Active Games</h2>
            <GamesList
              games={games}
              selectedId={selectedGameId}
              onSelect={setSelectedGameId}
            />
          </motion.div>

          {/* Game details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-lg font-semibold text-white mb-4">Game Details</h2>
            {selectedGame ? (
              <GameDetails game={selectedGame} />
            ) : (
              <div className="card text-center py-12">
                <p className="text-slate-400">
                  Select a game to view details
                </p>
              </div>
            )}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
