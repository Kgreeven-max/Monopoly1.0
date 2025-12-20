import { motion } from 'framer-motion';
import { usePlayerStore, useMyPlayer } from '../store/playerStore';
import { useSocket } from '../hooks/useSocket';

export function ResultsScreen() {
  const { gameState } = usePlayerStore();
  const myPlayer = useMyPlayer();
  const { disconnect } = useSocket();

  if (!gameState || !myPlayer) return null;

  // Calculate rankings
  const players = gameState.playerOrder
    .map(id => gameState.players[id])
    .sort((a, b) => {
      const aNetWorth = calculateNetWorth(a, gameState);
      const bNetWorth = calculateNetWorth(b, gameState);
      return bNetWorth - aNetWorth;
    });

  const myRank = players.findIndex(p => p.id === myPlayer.id) + 1;
  const isWinner = myRank === 1;

  const handlePlayAgain = () => {
    disconnect();
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen flex flex-col p-6">
      {/* Result header */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center mb-8"
      >
        {isWinner ? (
          <>
            <motion.div
              animate={{ rotate: [0, -10, 10, -10, 10, 0] }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="text-7xl mb-4"
            >
              🏆
            </motion.div>
            <h1 className="text-4xl font-display font-bold text-yellow-400 mb-2">
              YOU WON!
            </h1>
          </>
        ) : (
          <>
            <div className="text-7xl mb-4">
              {myRank === 2 ? '🥈' : myRank === 3 ? '🥉' : '🎮'}
            </div>
            <h1 className="text-4xl font-display font-bold text-white mb-2">
              Game Over
            </h1>
            <p className="text-white/60">
              You finished #{myRank}
            </p>
          </>
        )}
      </motion.div>

      {/* My stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className={`rounded-2xl p-6 mb-6 ${
          isWinner
            ? 'bg-yellow-500/20 border border-yellow-500/50'
            : 'bg-white/10'
        }`}
      >
        <p className="text-white/50 text-sm mb-2">Your Final Stats</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-3xl font-bold text-green-400">
              ${calculateNetWorth(myPlayer, gameState).toLocaleString()}
            </p>
            <p className="text-white/50 text-sm">Net Worth</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-blue-400">
              {countProperties(myPlayer.id, gameState)}
            </p>
            <p className="text-white/50 text-sm">Properties</p>
          </div>
        </div>
      </motion.div>

      {/* Leaderboard */}
      <div className="flex-1 overflow-y-auto mb-6">
        <p className="text-white/50 text-sm mb-3">Final Standings</p>

        <div className="space-y-2">
          {players.map((player, index) => (
            <motion.div
              key={player.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              className={`rounded-xl p-4 flex items-center gap-3 ${
                player.id === myPlayer.id
                  ? 'bg-green-500/20 border border-green-500/50'
                  : 'bg-white/10'
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                index === 0 ? 'bg-yellow-500 text-black' :
                index === 1 ? 'bg-gray-400 text-black' :
                index === 2 ? 'bg-orange-600 text-white' :
                'bg-white/20 text-white'
              }`}>
                {index + 1}
              </div>

              <div className="flex-1">
                <p className="text-white font-bold">
                  {player.name}
                  {player.id === myPlayer.id && (
                    <span className="text-green-400 text-sm ml-2">(You)</span>
                  )}
                </p>
              </div>

              <div className="text-right">
                <p className="text-green-400 font-bold">
                  ${calculateNetWorth(player, gameState).toLocaleString()}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Play again */}
      <button
        onClick={handlePlayAgain}
        className="btn-action btn-primary"
      >
        Play Again
      </button>
    </div>
  );
}

function calculateNetWorth(player: any, gameState: any): number {
  const propertyValue = Object.values(gameState.properties || {})
    .filter((p: any) => p.ownerId === player.id)
    .reduce((sum: number, p: any) =>
      sum + (p.price || 0) + (p.houses || 0) * (p.houseCost || 0), 0);

  return player.money + propertyValue;
}

function countProperties(playerId: string, gameState: any): number {
  return Object.values(gameState.properties || {})
    .filter((p: any) => p.ownerId === playerId).length;
}
