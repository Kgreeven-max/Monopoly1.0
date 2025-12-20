import { motion, AnimatePresence } from 'framer-motion';
import { useGameStore, usePlayers } from '../store/gameStore';
import { QRCode } from '../components/QRCode';
import { PlayerCard } from '../components/PlayerCard';

const TOKEN_COLORS: Record<string, string> = {
  car: '#e74c3c',
  dog: '#3498db',
  hat: '#2ecc71',
  ship: '#9b59b6',
  boot: '#f39c12',
  thimble: '#1abc9c',
  iron: '#e91e63',
  wheelbarrow: '#00bcd4',
};

export function LobbyScreen() {
  const { roomCode, gameState, isHost } = useGameStore();
  const players = usePlayers();

  const joinUrl = `${window.location.origin}/play?room=${roomCode}`;
  const minPlayers = 2;
  const canStart = players.length >= minPlayers && isHost;

  return (
    <div className="flex h-screen p-8 gap-8">
      {/* Left side - Room info and QR code */}
      <div className="flex-1 flex flex-col items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-6xl font-display font-bold text-white mb-4">
            PINOPOLY
          </h1>
          <p className="text-xl text-gray-400">Game Lobby</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 mb-8"
        >
          <p className="text-gray-400 text-center mb-4">Room Code</p>
          <p className="text-7xl font-mono font-bold text-white tracking-[0.3em] text-center">
            {roomCode}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl p-4"
        >
          <QRCode url={joinUrl} size={200} />
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 text-gray-400 text-center"
        >
          Scan to join or visit<br />
          <span className="text-white font-mono">{joinUrl}</span>
        </motion.p>
      </div>

      {/* Right side - Players list */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-display text-white">
            Players ({players.length}/{gameState?.config.maxPlayers || 8})
          </h2>
          {players.length < minPlayers && (
            <span className="text-yellow-400">
              Need {minPlayers - players.length} more to start
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <AnimatePresence mode="popLayout">
              {players.map((player, index) => (
                <motion.div
                  key={player.id}
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -50 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <PlayerCard
                    player={player}
                    color={TOKEN_COLORS[player.token] || '#ffffff'}
                    isHost={index === 0}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {players.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center h-full"
            >
              <p className="text-2xl text-gray-500">
                Waiting for players to join...
              </p>
            </motion.div>
          )}
        </div>

        {/* Start button (for host) */}
        {isHost && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6"
          >
            <button
              disabled={!canStart}
              className="w-full py-5 text-2xl font-bold rounded-xl transition-all
                       bg-green-500 hover:bg-green-600 disabled:bg-gray-600
                       disabled:cursor-not-allowed text-white"
            >
              {canStart ? 'Start Game' : `Waiting for Players (${players.length}/${minPlayers})`}
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
