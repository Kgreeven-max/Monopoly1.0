import React from 'react';
import { useGame } from '../contexts/GameContext';
import './PlayerList.css';

const getPlayerStatusClass = (player, currentPlayer) => {
  if (player.id === currentPlayer?.id) return 'player-active';
  if (player.inJail) return 'player-jailed';
  if (player.bankrupt) return 'player-bankrupt';
  if (player.connected === false) return 'player-disconnected';
  return '';
};

const PlayerList = () => {
  const { state } = useGame();
  const { players, currentPlayer } = state;

  if (!players || players.length === 0) {
    return <div className="player-list-empty">No players in the game</div>;
  }

  return (
    <div className="player-list">
      <h3>Players</h3>
      <div className="player-list-container">
        {players.map((player) => (
          <div 
            key={player.id} 
            className={`player-item ${getPlayerStatusClass(player, currentPlayer)}`}
          >
            <div className="player-token" style={{ backgroundColor: player.color }}></div>
            <div className="player-info">
              <div className="player-name">{player.name}</div>
              <div className="player-cash">${player.cash}</div>
              <div className="player-status">
                {player.id === currentPlayer?.id && <span className="status-indicator">Turn</span>}
                {player.inJail && <span className="status-indicator">In Jail</span>}
                {player.bankrupt && <span className="status-indicator">Bankrupt</span>}
                {player.connected === false && <span className="status-indicator">Disconnected</span>}
              </div>
            </div>
            <div className="player-properties">
              <div className="property-count">
                Properties: {player.properties ? player.properties.length : 0}
              </div>
              <div className="net-worth">
                Net Worth: ${player.netWorth || 0}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PlayerList; 