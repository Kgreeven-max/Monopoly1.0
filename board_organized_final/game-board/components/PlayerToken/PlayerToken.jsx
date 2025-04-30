import React from 'react';
import { useGame } from '../../contexts/GameContext';
import './PlayerToken.css';

export default function PlayerToken({ player, position }) {
  const { state } = useGame();
  const isCurrentPlayer = state.currentPlayer?.id === player.id;
  const isInJail = player.jailTurns > 0;

  // Calculate player status indicators
  const getStatusIndicators = () => {
    const indicators = [];

    // Bankruptcy warning
    if (player.cash < 0) {
      indicators.push({
        icon: '💸',
        tooltip: 'In debt',
        class: 'status-debt'
      });
    }

    // Jail status
    if (isInJail) {
      indicators.push({
        icon: '🔒',
        tooltip: `In jail for ${player.jailTurns} more turns`,
        class: 'status-jail'
      });
    }

    // Crime suspicion
    if (player.suspicionLevel > 50) {
      indicators.push({
        icon: '👮',
        tooltip: 'High suspicion level',
        class: 'status-suspicious'
      });
    }

    // Active loans
    if (player.loans?.length > 0) {
      indicators.push({
        icon: '💰',
        tooltip: `${player.loans.length} active loans`,
        class: 'status-loans'
      });
    }

    return indicators;
  };

  return (
    <div
      className={`player-token ${isCurrentPlayer ? 'current' : ''}`}
      style={{
        transform: `translate(${position.x}px, ${position.y}px)`,
        backgroundColor: player.color,
      }}
      data-in-jail={isInJail}
    >
      {/* Player emoji or initial */}
      <div className="token-symbol">
        {player.emoji || player.name[0]}
      </div>

      {/* Player name tooltip */}
      <div className="token-tooltip">
        <strong>{player.name}</strong>
        <div className="tooltip-details">
          <div>Cash: ${player.cash}</div>
          <div>Properties: {player.properties?.length || 0}</div>
          <div>Net Worth: ${player.netWorth}</div>
        </div>
      </div>

      {/* Status indicators */}
      <div className="status-indicators">
        {getStatusIndicators().map((indicator, index) => (
          <div
            key={index}
            className={`status-indicator ${indicator.class}`}
            title={indicator.tooltip}
          >
            {indicator.icon}
          </div>
        ))}
      </div>

      {/* Current player indicator */}
      {isCurrentPlayer && (
        <div className="current-player-indicator" />
      )}
    </div>
  );
} 