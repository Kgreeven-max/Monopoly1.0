import type { PlayerState } from '@pinopoly/game-engine';

interface PlayerCardProps {
  player: PlayerState;
  color: string;
  isHost?: boolean;
}

export function PlayerCard({ player, color, isHost }: PlayerCardProps) {
  return (
    <div
      className="p-4 rounded-xl bg-white/10 backdrop-blur border-2 transition-all"
      style={{ borderColor: color }}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center text-white text-xl"
          style={{ backgroundColor: color }}
        >
          {getTokenEmoji(player.token)}
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-white font-bold text-lg">{player.name}</span>
            {isHost && (
              <span className="px-2 py-0.5 text-xs bg-yellow-500/30 text-yellow-300 rounded">
                HOST
              </span>
            )}
            {player.isBot && (
              <span className="px-2 py-0.5 text-xs bg-purple-500/30 text-purple-300 rounded">
                BOT
              </span>
            )}
          </div>
          <span className="text-white/60 text-sm capitalize">{player.token}</span>
        </div>

        <div className="text-right">
          <span className="text-green-400 font-bold">
            ${player.money.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
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
