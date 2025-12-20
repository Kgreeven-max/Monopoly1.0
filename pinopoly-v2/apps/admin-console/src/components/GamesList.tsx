import { motion } from 'framer-motion';

interface GameSummary {
  id: string;
  roomCode: string;
  status: 'lobby' | 'playing' | 'paused' | 'finished';
  playerCount: number;
  hostName: string;
  startedAt?: string;
  createdAt: string;
}

interface GamesListProps {
  games: GameSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function GamesList({ games, selectedId, onSelect }: GamesListProps) {
  if (games.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-slate-400 mb-2">No active games</p>
        <p className="text-sm text-slate-500">
          Games will appear here when players create them
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {games.map((game, index) => (
        <motion.div
          key={game.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          onClick={() => onSelect(game.id)}
          className={`
            card cursor-pointer transition-all
            ${selectedId === game.id
              ? 'ring-2 ring-blue-500 bg-slate-700'
              : 'hover:bg-slate-700'
            }
          `}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Room code */}
              <div className="text-2xl font-mono font-bold text-white">
                {game.roomCode}
              </div>

              {/* Status badge */}
              <span className={`badge ${getStatusBadgeClass(game.status)}`}>
                {game.status}
              </span>
            </div>

            {/* Player count */}
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-white font-medium">{game.playerCount} players</p>
                <p className="text-sm text-slate-400">Host: {game.hostName}</p>
              </div>

              <div className="text-slate-400">→</div>
            </div>
          </div>

          {/* Time info */}
          <div className="mt-3 pt-3 border-t border-slate-700 flex justify-between text-sm text-slate-400">
            <span>Created: {formatTime(game.createdAt)}</span>
            {game.startedAt && (
              <span>Started: {formatTime(game.startedAt)}</span>
            )}
          </div>
        </motion.div>
      ))}
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

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
