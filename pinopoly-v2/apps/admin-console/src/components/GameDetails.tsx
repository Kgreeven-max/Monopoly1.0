import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAdminStore } from '../store/adminStore';

interface GameSummary {
  id: string;
  roomCode: string;
  status: 'lobby' | 'playing' | 'paused' | 'finished';
  playerCount: number;
  hostName: string;
  startedAt?: string;
  createdAt: string;
}

interface GameDetailsProps {
  game: GameSummary;
}

export function GameDetails({ game }: GameDetailsProps) {
  const { endGame } = useAdminStore();
  const [showConfirm, setShowConfirm] = useState(false);

  const handleEndGame = async () => {
    await endGame(game.id);
    setShowConfirm(false);
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm text-slate-400">Room Code</p>
          <p className="text-3xl font-mono font-bold text-white">{game.roomCode}</p>
        </div>
        <span className={`badge ${getStatusBadgeClass(game.status)}`}>
          {game.status}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-700 rounded-lg p-4">
          <p className="text-sm text-slate-400">Players</p>
          <p className="text-2xl font-bold text-white">{game.playerCount}</p>
        </div>
        <div className="bg-slate-700 rounded-lg p-4">
          <p className="text-sm text-slate-400">Host</p>
          <p className="text-lg font-medium text-white truncate">{game.hostName}</p>
        </div>
      </div>

      {/* Timeline */}
      <div className="mb-6">
        <p className="text-sm text-slate-400 mb-3">Timeline</p>
        <div className="space-y-2">
          <TimelineItem
            label="Created"
            time={game.createdAt}
            icon="🎯"
          />
          {game.startedAt && (
            <TimelineItem
              label="Started"
              time={game.startedAt}
              icon="▶️"
            />
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-slate-700 pt-4">
        <p className="text-sm text-slate-400 mb-3">Actions</p>

        {!showConfirm ? (
          <div className="space-y-2">
            <button
              onClick={() => window.open(`/?room=${game.roomCode}`, '_blank')}
              className="w-full py-2 px-4 bg-slate-700 hover:bg-slate-600
                       text-white rounded-lg transition-colors text-sm"
            >
              👁️ View Game
            </button>

            {game.status !== 'finished' && (
              <button
                onClick={() => setShowConfirm(true)}
                className="w-full py-2 px-4 bg-red-500/20 hover:bg-red-500/30
                         text-red-400 rounded-lg transition-colors text-sm"
              >
                ⏹️ End Game
              </button>
            )}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-red-500/10 border border-red-500/50 rounded-lg p-4"
          >
            <p className="text-red-400 text-sm mb-3">
              Are you sure you want to end this game? This action cannot be undone.
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleEndGame}
                className="flex-1 py-2 bg-red-600 hover:bg-red-700
                         text-white rounded-lg transition-colors text-sm"
              >
                Confirm End
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 bg-slate-700 hover:bg-slate-600
                         text-white rounded-lg transition-colors text-sm"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

interface TimelineItemProps {
  label: string;
  time: string;
  icon: string;
}

function TimelineItem({ label, time, icon }: TimelineItemProps) {
  const date = new Date(time);

  return (
    <div className="flex items-center gap-3">
      <span className="text-lg">{icon}</span>
      <div className="flex-1">
        <p className="text-white text-sm">{label}</p>
        <p className="text-slate-400 text-xs">
          {date.toLocaleDateString()} at {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}

function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'lobby':
      return 'badge-info';
    case 'playing':
      return 'badge-success';
    case 'paused':
      return 'badge-warning';
    case 'finished':
      return 'badge-danger';
    default:
      return '';
  }
}
