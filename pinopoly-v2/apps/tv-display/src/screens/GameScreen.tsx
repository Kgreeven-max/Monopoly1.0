import { motion } from 'framer-motion';
import { useGameStore, usePlayers, useCurrentPlayer } from '../store/gameStore';
import { GameBoard } from '../components/board/GameBoard';
import { PlayerPanel } from '../components/PlayerPanel';
import { DiceDisplay } from '../components/DiceDisplay';
import { EventLog } from '../components/EventLog';
import { TurnIndicator } from '../components/TurnIndicator';

export function GameScreen() {
  const { gameState, roomCode, lastDiceRoll, isRolling } = useGameStore();
  const players = usePlayers();
  const currentPlayer = useCurrentPlayer();

  if (!gameState) return null;

  return (
    <div className="flex h-screen p-4 gap-4">
      {/* Left sidebar - Players */}
      <motion.div
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-72 flex flex-col gap-4"
      >
        <div className="bg-white/10 backdrop-blur rounded-xl p-4">
          <h2 className="text-lg font-display text-white/70 mb-2">Room</h2>
          <p className="text-3xl font-mono font-bold text-white tracking-wider">
            {roomCode}
          </p>
        </div>

        <div className="flex-1 bg-white/5 backdrop-blur rounded-xl p-4 overflow-y-auto">
          <h2 className="text-lg font-display text-white/70 mb-4">Players</h2>
          <div className="space-y-3">
            {players.map((player) => (
              <PlayerPanel
                key={player.id}
                player={player}
                isCurrentTurn={currentPlayer?.id === player.id}
              />
            ))}
          </div>
        </div>

        {/* Turn indicator */}
        {currentPlayer && (
          <TurnIndicator
            player={currentPlayer}
            phase={gameState.phase}
          />
        )}
      </motion.div>

      {/* Center - Game board */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex-1 flex items-center justify-center relative"
      >
        <GameBoard
          gameState={gameState}
          players={players}
        />

        {/* Dice overlay */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
          <DiceDisplay
            dice={lastDiceRoll}
            isRolling={isRolling}
          />
        </div>
      </motion.div>

      {/* Right sidebar - Events */}
      <motion.div
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-80 flex flex-col gap-4"
      >
        {/* Game info */}
        <div className="bg-white/10 backdrop-blur rounded-xl p-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-sm text-white/50">Round</h2>
              <p className="text-2xl font-bold text-white">{gameState.round}</p>
            </div>
            <div className="text-right">
              <h2 className="text-sm text-white/50">Free Parking</h2>
              <p className="text-2xl font-bold text-green-400">
                ${gameState.freeParkingPool.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Economy indicator */}
        <div className="bg-white/10 backdrop-blur rounded-xl p-4">
          <h2 className="text-sm text-white/50 mb-2">Economy</h2>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full text-sm font-bold ${
              gameState.economy.phase === 'boom' ? 'bg-green-500' :
              gameState.economy.phase === 'bust' ? 'bg-red-500' :
              gameState.economy.phase === 'recovery' ? 'bg-yellow-500' :
              'bg-blue-500'
            }`}>
              {gameState.economy.phase.toUpperCase()}
            </div>
            <div className="text-white">
              {(gameState.economy.multiplier * 100).toFixed(0)}%
            </div>
          </div>
        </div>

        {/* Event log */}
        <div className="flex-1 bg-white/5 backdrop-blur rounded-xl overflow-hidden">
          <EventLog />
        </div>
      </motion.div>
    </div>
  );
}
