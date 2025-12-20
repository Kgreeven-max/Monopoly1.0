import { motion } from 'framer-motion';
import type { PlayerState, TurnPhase } from '@pinopoly/game-engine';

interface TurnIndicatorProps {
  player: PlayerState;
  phase: TurnPhase;
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

const PHASE_MESSAGES: Record<TurnPhase, string> = {
  preRoll: 'Preparing to roll...',
  roll: 'Rolling dice...',
  postRoll: 'Taking action...',
  jail: 'In jail...',
  bankrupt: 'Managing finances...',
  trading: 'Trading...',
  end: 'Ending turn...',
};

export function TurnIndicator({ player, phase }: TurnIndicatorProps) {
  const color = TOKEN_COLORS[player.token] || '#ffffff';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/10 backdrop-blur rounded-xl p-4"
      style={{ borderLeft: `4px solid ${color}` }}
    >
      <div className="flex items-center gap-3">
        <motion.div
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
          className="w-10 h-10 rounded-full flex items-center justify-center text-lg"
          style={{ backgroundColor: color }}
        >
          {getTokenEmoji(player.token)}
        </motion.div>

        <div className="flex-1">
          <p className="text-white font-bold text-lg">{player.name}'s Turn</p>
          <p className="text-white/60 text-sm">{PHASE_MESSAGES[phase]}</p>
        </div>

        {/* Phase indicator dots */}
        <div className="flex gap-1">
          {['preRoll', 'roll', 'postRoll', 'end'].map((p, i) => (
            <div
              key={p}
              className={`w-2 h-2 rounded-full transition-colors ${
                getPhaseOrder(phase) >= i ? 'bg-green-500' : 'bg-white/20'
              }`}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

function getPhaseOrder(phase: TurnPhase): number {
  const order: Record<TurnPhase, number> = {
    preRoll: 0,
    roll: 1,
    postRoll: 2,
    jail: 1,
    bankrupt: 2,
    trading: 2,
    end: 3,
  };
  return order[phase] || 0;
}

function getTokenEmoji(token: string): string {
  const emojis: Record<string, string> = {
    car: '🚗',
    dog: '🐕',
    hat: '🎩',
    ship: '🚢',
    boot: '👢',
    thimble: '🧵',
    iron: '🔧',
    wheelbarrow: '🛒',
  };
  return emojis[token] || '🎲';
}
