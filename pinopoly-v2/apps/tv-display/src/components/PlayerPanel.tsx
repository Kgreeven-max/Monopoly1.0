import { motion } from 'framer-motion';
import type { PlayerState } from '@pinopoly/game-engine';
import { useGameStore } from '../store/gameStore';

interface PlayerPanelProps {
  player: PlayerState;
  isCurrentTurn: boolean;
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

export function PlayerPanel({ player, isCurrentTurn }: PlayerPanelProps) {
  const { gameState } = useGameStore();

  // Count owned properties
  const ownedProperties = Object.values(gameState?.properties || {})
    .filter(p => p.ownerId === player.id);

  const totalHouses = ownedProperties.reduce((sum, p) => sum + (p.houses || 0), 0);
  const hotels = ownedProperties.filter(p => (p.houses || 0) >= 5).length;

  const color = TOKEN_COLORS[player.token] || '#ffffff';

  return (
    <motion.div
      animate={{
        scale: isCurrentTurn ? 1.02 : 1,
        borderColor: isCurrentTurn ? color : 'transparent',
      }}
      className={`p-3 rounded-lg border-2 transition-colors ${
        isCurrentTurn ? 'bg-white/15' : 'bg-white/5'
      } ${player.isBankrupt ? 'opacity-50' : ''}`}
    >
      <div className="flex items-center gap-2 mb-2">
        {/* Token indicator */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-sm"
          style={{ backgroundColor: color }}
        >
          {getTokenEmoji(player.token)}
        </div>

        {/* Name */}
        <div className="flex-1 min-w-0">
          <p className="text-white font-bold truncate">{player.name}</p>
          {player.isBot && (
            <p className="text-xs text-purple-400 capitalize">{player.personality}</p>
          )}
        </div>

        {/* Current turn indicator */}
        {isCurrentTurn && (
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className="w-2 h-2 rounded-full bg-green-500"
          />
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="text-center">
          <p className="text-green-400 font-bold">${formatMoney(player.money)}</p>
          <p className="text-white/40">Cash</p>
        </div>
        <div className="text-center">
          <p className="text-blue-400 font-bold">{ownedProperties.length}</p>
          <p className="text-white/40">Props</p>
        </div>
        <div className="text-center">
          <p className="text-yellow-400 font-bold">
            {hotels > 0 ? `${hotels}H` : totalHouses}
          </p>
          <p className="text-white/40">{hotels > 0 ? 'Hotels' : 'Houses'}</p>
        </div>
      </div>

      {/* Jail indicator */}
      {player.inJail && (
        <div className="mt-2 text-center">
          <span className="px-2 py-0.5 text-xs bg-orange-500/30 text-orange-300 rounded">
            IN JAIL ({player.jailTurns}/3)
          </span>
        </div>
      )}

      {/* Bankrupt indicator */}
      {player.isBankrupt && (
        <div className="mt-2 text-center">
          <span className="px-2 py-0.5 text-xs bg-red-500/30 text-red-300 rounded">
            BANKRUPT
          </span>
        </div>
      )}
    </motion.div>
  );
}

function formatMoney(amount: number): string {
  if (amount >= 1000000) {
    return `${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `${(amount / 1000).toFixed(1)}K`;
  }
  return amount.toString();
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
