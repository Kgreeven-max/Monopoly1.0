import { motion, AnimatePresence } from 'framer-motion';
import { useGameStore } from '../store/gameStore';
import type { GameEvent } from '@pinopoly/game-engine';

export function EventLog() {
  const { recentEvents } = useGameStore();

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-white/10">
        <h2 className="text-lg font-display text-white/70">Event Log</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence initial={false}>
          {recentEvents.length === 0 ? (
            <p className="text-white/40 text-center">No events yet</p>
          ) : (
            recentEvents.map((event, index) => (
              <motion.div
                key={`${event.type}-${event.timestamp}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.05 }}
                className="mb-3"
              >
                <EventItem event={event} />
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

interface EventItemProps {
  event: GameEvent;
}

function EventItem({ event }: EventItemProps) {
  const { icon, message, color } = getEventDisplay(event);

  return (
    <div className="flex items-start gap-3">
      <span className="text-xl">{icon}</span>
      <div className="flex-1">
        <p className={`text-sm ${color}`}>{message}</p>
        <p className="text-xs text-white/30">
          {formatTime(event.timestamp)}
        </p>
      </div>
    </div>
  );
}

function getEventDisplay(event: GameEvent): { icon: string; message: string; color: string } {
  switch (event.type) {
    case 'PLAYER_JOINED':
      return {
        icon: '👋',
        message: `${event.data?.playerName || 'Player'} joined the game`,
        color: 'text-green-400',
      };

    case 'DICE_ROLLED':
      return {
        icon: '🎲',
        message: `Rolled ${event.data?.dice?.[0]} + ${event.data?.dice?.[1]} = ${(event.data?.dice?.[0] || 0) + (event.data?.dice?.[1] || 0)}`,
        color: 'text-blue-400',
      };

    case 'PLAYER_MOVED':
      return {
        icon: '🚶',
        message: `Moved to ${event.data?.spaceName || `space ${event.data?.position}`}`,
        color: 'text-white/70',
      };

    case 'PROPERTY_PURCHASED':
      return {
        icon: '🏠',
        message: `Bought ${event.data?.propertyName} for $${event.data?.price}`,
        color: 'text-yellow-400',
      };

    case 'RENT_PAID':
      return {
        icon: '💰',
        message: `Paid $${event.data?.amount} rent`,
        color: 'text-red-400',
      };

    case 'PASSED_GO':
      return {
        icon: '✅',
        message: `Collected $${event.data?.amount || 200} passing GO`,
        color: 'text-green-400',
      };

    case 'WENT_TO_JAIL':
      return {
        icon: '🚔',
        message: 'Sent to jail!',
        color: 'text-orange-400',
      };

    case 'LEFT_JAIL':
      return {
        icon: '🔓',
        message: 'Got out of jail',
        color: 'text-green-400',
      };

    case 'HOUSE_BUILT':
      return {
        icon: '🏗️',
        message: `Built house on ${event.data?.propertyName}`,
        color: 'text-yellow-400',
      };

    case 'HOTEL_BUILT':
      return {
        icon: '🏨',
        message: `Built hotel on ${event.data?.propertyName}`,
        color: 'text-purple-400',
      };

    case 'PLAYER_BANKRUPT':
      return {
        icon: '💸',
        message: `${event.data?.playerName || 'Player'} went bankrupt!`,
        color: 'text-red-500',
      };

    case 'GAME_WON':
      return {
        icon: '🏆',
        message: `${event.data?.winnerName || 'Player'} wins the game!`,
        color: 'text-yellow-500',
      };

    case 'ECONOMY_CHANGED':
      return {
        icon: '📈',
        message: `Economy shifted to ${event.data?.phase}`,
        color: 'text-blue-400',
      };

    case 'FREE_PARKING':
      return {
        icon: '🅿️',
        message: `Collected $${event.data?.amount} from Free Parking`,
        color: 'text-green-400',
      };

    default:
      return {
        icon: '📝',
        message: event.type.replace(/_/g, ' ').toLowerCase(),
        color: 'text-white/50',
      };
  }
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
