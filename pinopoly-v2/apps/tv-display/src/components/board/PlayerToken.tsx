import { motion } from 'framer-motion';
import type { PlayerState } from '@pinopoly/game-engine';

interface PlayerTokenProps {
  player: PlayerState;
  position: { x: number; y: number; rotation: number };
  stackIndex: number;
  totalAtPosition: number;
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

export function PlayerToken({
  player,
  position,
  stackIndex,
  totalAtPosition,
}: PlayerTokenProps) {
  const color = TOKEN_COLORS[player.token] || '#ffffff';
  const emoji = TOKEN_EMOJIS[player.token] || '🎲';

  // Calculate offset for stacking multiple tokens
  const stackOffset = calculateStackOffset(stackIndex, totalAtPosition);

  return (
    <motion.div
      key={`token-${player.id}-${player.position}`}
      layout
      style={{
        position: 'absolute',
        left: `${position.x + stackOffset.x}%`,
        top: `${position.y + stackOffset.y}%`,
        zIndex: 20 + stackIndex,
      }}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
      }}
      className="z-20 transform -translate-x-1/2 -translate-y-1/2"
    >
      <div className="relative">
        {/* Token body */}
        <div
          className="w-6 h-6 rounded-full flex items-center justify-center text-sm shadow-lg border-2 border-white"
          style={{ backgroundColor: color }}
        >
          {emoji}
        </div>

        {/* Player name tooltip on hover */}
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 opacity-0 hover:opacity-100 pointer-events-none transition-opacity">
          <div className="bg-black/80 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap">
            {player.name}
          </div>
        </div>

        {/* In jail indicator */}
        {player.inJail && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-orange-500 rounded-full flex items-center justify-center text-[8px]">
            🔒
          </div>
        )}
      </div>
    </motion.div>
  );
}

function calculateStackOffset(
  stackIndex: number,
  totalAtPosition: number
): { x: number; y: number } {
  if (totalAtPosition === 1) {
    return { x: 0, y: 0 };
  }

  // Arrange tokens in a small circle around the center
  const angle = (stackIndex / totalAtPosition) * Math.PI * 2;
  const radius = 1.5; // Percentage offset

  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  };
}
