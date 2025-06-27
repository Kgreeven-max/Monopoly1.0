import { useEffect, useState } from 'react';
import { useGame } from '../../game-state/contexts/GameContext';

/**
 * Debug hook to monitor all game events and help identify when movements occur
 */
export const useGameEventDebugger = () => {
  const { state } = useGame();
  const [eventLog, setEventLog] = useState([]);
  const [playerMovements, setPlayerMovements] = useState([]);

  // Log all state changes
  useEffect(() => {
    const timestamp = new Date().toLocaleTimeString();
    const newLogEntry = {
      timestamp,
      type: 'state_update',
      players: state.players?.map(p => ({ id: p.id, name: p.name || p.username, position: p.position })),
      notifications: state.notifications?.slice(0, 3),
      currentPlayer: state.currentPlayerId,
      lastDiceRoll: state.lastDiceRoll
    };
    
    setEventLog(prev => [newLogEntry, ...prev.slice(0, 9)]); // Keep last 10 entries
  }, [state.players, state.notifications, state.currentPlayerId, state.lastDiceRoll]);

  // Track player movements specifically
  useEffect(() => {
    if (state.players && state.players.length > 0) {
      state.players.forEach(player => {
        const timestamp = new Date().toLocaleTimeString();
        const movementEntry = {
          timestamp,
          playerId: player.id,
          playerName: player.name || player.username || `Player ${player.id}`,
          position: player.position || 0,
          isBot: player.is_bot
        };
        
        setPlayerMovements(prev => {
          // Check if this is a new position for this player
          const lastEntry = prev.find(entry => entry.playerId === player.id);
          if (!lastEntry || lastEntry.position !== movementEntry.position) {
            const newEntry = {
              ...movementEntry,
              previousPosition: lastEntry?.position,
              isMovement: lastEntry !== undefined
            };
            
            // Keep last 20 movements
            return [newEntry, ...prev.filter(entry => entry.playerId !== player.id).slice(0, 19)];
          }
          return prev;
        });
      });
    }
  }, [state.players]);

  // Get recent movements for a specific player
  const getPlayerMovements = (playerId) => {
    return playerMovements.filter(movement => movement.playerId === playerId && movement.isMovement);
  };

  // Get the latest movement
  const getLatestMovement = () => {
    return playerMovements.find(movement => movement.isMovement);
  };

  // Check if any player moved recently (within last 5 seconds)
  const hasRecentMovement = () => {
    const fiveSecondsAgo = Date.now() - 5000;
    return playerMovements.some(movement => {
      if (!movement.isMovement) return false;
      const movementTime = new Date();
      const [time, period] = movement.timestamp.split(' ');
      const [hours, minutes, seconds] = time.split(':');
      movementTime.setHours(
        period === 'PM' && hours !== '12' ? parseInt(hours) + 12 : parseInt(hours),
        parseInt(minutes),
        parseInt(seconds)
      );
      return movementTime.getTime() > fiveSecondsAgo;
    });
  };

  return {
    eventLog,
    playerMovements,
    getPlayerMovements,
    getLatestMovement,
    hasRecentMovement,
    currentState: {
      playersCount: state.players?.length || 0,
      notificationsCount: state.notifications?.length || 0,
      currentPlayer: state.currentPlayerId,
      lastDiceRoll: state.lastDiceRoll
    }
  };
};

export default useGameEventDebugger;