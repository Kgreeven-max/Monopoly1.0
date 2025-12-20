import { motion } from 'framer-motion';
import { usePlayerStore, useMyPlayer } from '../store/playerStore';
import { useSocket } from '../hooks/useSocket';
import { SocketEvents } from '@pinopoly/shared';

const TOKEN_EMOJIS: Record<string, string> = {
  car: '🚗',
  dog: '🐕',
  hat: '🎩',
  ship: '🚢',
  boot: '👢',
  thimble: '🧵',
  iron: '🔧',
  wheelbarrow: '🛒',
};

export function LobbyScreen() {
  const { gameState, roomCode, isHost } = usePlayerStore();
  const myPlayer = useMyPlayer();
  const { emit, disconnect } = useSocket();

  if (!gameState || !myPlayer) return null;

  const players = gameState.playerOrder.map(id => gameState.players[id]);
  const canStart = players.length >= 2 && isHost;

  const handleStartGame = () => {
    emit(SocketEvents.START_GAME);
  };

  const handleLeave = () => {
    disconnect();
  };

  const handleAddBot = () => {
    // Select a random personality for variety
    const personalities = ['conservative', 'aggressive', 'strategic', 'opportunistic', 'shark', 'investor'];
    const randomPersonality = personalities[Math.floor(Math.random() * personalities.length)];
    emit(SocketEvents.ADD_BOT, { personality: randomPersonality, difficulty: 'normal' });
  };

  return (
    <div className="min-h-screen flex flex-col p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h1 className="text-3xl font-display font-bold text-white">
          PINOPOLY
        </h1>
        <p className="text-gray-400">Waiting for players...</p>
      </motion.div>

      {/* Room code display */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white/10 backdrop-blur rounded-2xl p-6 mb-6 text-center"
      >
        <p className="text-white/50 text-sm mb-2">Room Code</p>
        <p className="text-4xl font-mono font-bold text-white tracking-[0.3em]">
          {roomCode}
        </p>
      </motion.div>

      {/* My player card */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-green-500/20 border border-green-500/50 rounded-2xl p-4 mb-6"
      >
        <div className="flex items-center gap-4">
          <div className="text-4xl">
            {TOKEN_EMOJIS[myPlayer.token]}
          </div>
          <div className="flex-1">
            <p className="text-white font-bold text-lg">{myPlayer.name}</p>
            <p className="text-green-400 text-sm">
              {isHost ? '👑 Host' : 'Player'}
            </p>
          </div>
          <div className="text-green-400 text-sm">
            You
          </div>
        </div>
      </motion.div>

      {/* Other players */}
      <div className="flex-1 overflow-y-auto mb-6">
        <p className="text-white/50 text-sm mb-3">
          Players ({players.length}/{gameState.config.maxPlayers})
        </p>

        <div className="space-y-3">
          {players
            .filter(p => p.id !== myPlayer.id)
            .map((player, index) => (
              <motion.div
                key={player.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/10 rounded-xl p-4"
              >
                <div className="flex items-center gap-4">
                  <div className="text-3xl">
                    {TOKEN_EMOJIS[player.token]}
                  </div>
                  <div className="flex-1">
                    <p className="text-white font-bold">{player.name}</p>
                    {player.isBot && (
                      <p className="text-purple-400 text-sm capitalize">
                        🤖 {player.personality}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
        </div>

        {players.length < 2 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-yellow-400 mt-4"
          >
            Need at least 2 players to start
          </motion.p>
        )}
      </div>

      {/* Actions */}
      <div className="space-y-3">
        {isHost && (
          <>
            <button
              onClick={handleStartGame}
              disabled={!canStart}
              className="btn-action btn-primary disabled:btn-disabled"
            >
              {canStart ? 'Start Game' : `Need ${2 - players.length} More Player(s)`}
            </button>

            {players.length < gameState.config.maxPlayers && (
              <button
                onClick={handleAddBot}
                className="btn-action btn-secondary"
              >
                Add Bot Player
              </button>
            )}
          </>
        )}

        <button
          onClick={handleLeave}
          className="btn-action bg-white/10 hover:bg-white/20 text-white"
        >
          Leave Game
        </button>
      </div>
    </div>
  );
}
