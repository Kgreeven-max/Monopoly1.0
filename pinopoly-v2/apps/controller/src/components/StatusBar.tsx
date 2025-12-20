import { motion } from 'framer-motion';
import type { PlayerState } from '@pinopoly/game-engine';

interface StatusBarProps {
  player: PlayerState;
  isMyTurn: boolean;
}

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

export function StatusBar({ player, isMyTurn }: StatusBarProps) {
  const color = TOKEN_COLORS[player.token] || '#ffffff';
  const emoji = TOKEN_EMOJIS[player.token] || '🎲';

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative"
    >
      {/* Background with color tint */}
      <div
        className="absolute inset-0 opacity-20"
        style={{ backgroundColor: color }}
      />

      {/* Content */}
      <div className="relative flex items-center gap-3 p-4">
        {/* Token */}
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-2xl shadow-lg"
          style={{ backgroundColor: color }}
        >
          {emoji}
        </div>

        {/* Player info */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-white font-bold">{player.name}</span>
            {isMyTurn && (
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="px-2 py-0.5 bg-green-500 text-white text-xs font-bold rounded-full"
              >
                YOUR TURN
              </motion.span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-green-400 font-bold">
              ${player.money.toLocaleString()}
            </span>
            {player.inJail && (
              <span className="text-orange-400">• In Jail</span>
            )}
          </div>
        </div>

        {/* Position */}
        <div className="text-right">
          <p className="text-white/50 text-xs">Position</p>
          <p className="text-white font-bold">{player.position}</p>
        </div>
      </div>

      {/* Turn indicator bar */}
      {isMyTurn && (
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          className="h-1 bg-green-500 origin-left"
        />
      )}
    </motion.div>
  );
}
