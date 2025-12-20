import { motion } from 'framer-motion';
import { useGameStore, usePlayers } from '../store/gameStore';
import { useSocket } from '../hooks/useSocket';

export function ResultsScreen() {
  const { gameState, roomCode } = useGameStore();
  const players = usePlayers();
  const { disconnect } = useSocket();

  // Sort players by net worth (money + property values)
  const rankedPlayers = [...players].sort((a, b) => {
    const aNetWorth = a.money + Object.values(gameState?.properties || {})
      .filter(p => p.ownerId === a.id)
      .reduce((sum, p) => sum + (p.price || 0) + (p.houses || 0) * (p.houseCost || 0), 0);

    const bNetWorth = b.money + Object.values(gameState?.properties || {})
      .filter(p => p.ownerId === b.id)
      .reduce((sum, p) => sum + (p.price || 0) + (p.houses || 0) * (p.houseCost || 0), 0);

    return bNetWorth - aNetWorth;
  });

  const winner = rankedPlayers[0];

  const handlePlayAgain = () => {
    disconnect();
    window.location.href = '/';
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen p-8">
      {/* Winner announcement */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', duration: 0.8 }}
        className="text-center mb-12"
      >
        <motion.div
          animate={{ rotate: [0, -5, 5, -5, 5, 0] }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="text-8xl mb-4"
        >
          🏆
        </motion.div>

        <h1 className="text-6xl font-display font-bold text-white mb-4">
          {winner?.name} WINS!
        </h1>

        <p className="text-2xl text-yellow-400">
          Net Worth: ${calculateNetWorth(winner, gameState).toLocaleString()}
        </p>
      </motion.div>

      {/* Leaderboard */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-2xl"
      >
        <h2 className="text-2xl font-display text-white mb-6 text-center">
          Final Standings
        </h2>

        <div className="space-y-4">
          {rankedPlayers.map((player, index) => (
            <motion.div
              key={player.id}
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 + index * 0.1 }}
              className={`flex items-center gap-4 p-4 rounded-xl ${
                index === 0 ? 'bg-yellow-500/20 border border-yellow-500/50' :
                index === 1 ? 'bg-gray-400/20 border border-gray-400/50' :
                index === 2 ? 'bg-orange-600/20 border border-orange-600/50' :
                'bg-white/5'
              }`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                index === 0 ? 'bg-yellow-500 text-black' :
                index === 1 ? 'bg-gray-400 text-black' :
                index === 2 ? 'bg-orange-600 text-white' :
                'bg-white/20 text-white'
              }`}>
                {index + 1}
              </div>

              <div className="flex-1">
                <p className="text-xl text-white font-bold">{player.name}</p>
                <p className="text-sm text-white/60">
                  {Object.values(gameState?.properties || {})
                    .filter(p => p.ownerId === player.id).length} properties
                </p>
              </div>

              <div className="text-right">
                <p className="text-xl text-green-400 font-bold">
                  ${calculateNetWorth(player, gameState).toLocaleString()}
                </p>
                <p className="text-sm text-white/60">
                  Cash: ${player.money.toLocaleString()}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Game stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-8 flex gap-8 text-center"
      >
        <div>
          <p className="text-3xl font-bold text-white">{gameState?.round || 0}</p>
          <p className="text-white/50">Rounds Played</p>
        </div>
        <div>
          <p className="text-3xl font-bold text-white">{players.length}</p>
          <p className="text-white/50">Players</p>
        </div>
        <div>
          <p className="text-3xl font-bold text-white">{roomCode}</p>
          <p className="text-white/50">Room Code</p>
        </div>
      </motion.div>

      {/* Play again button */}
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        onClick={handlePlayAgain}
        className="mt-12 px-12 py-4 bg-green-500 hover:bg-green-600
                 text-white text-xl font-bold rounded-xl transition-colors"
      >
        Play Again
      </motion.button>
    </div>
  );
}

function calculateNetWorth(player: any, gameState: any): number {
  if (!player || !gameState) return 0;

  const propertyValue = Object.values(gameState.properties || {})
    .filter((p: any) => p.ownerId === player.id)
    .reduce((sum: number, p: any) =>
      sum + (p.price || 0) + (p.houses || 0) * (p.houseCost || 0), 0);

  return player.money + propertyValue;
}
