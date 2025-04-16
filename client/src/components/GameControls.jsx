import React, { useState } from 'react';
import { useGame } from '../contexts/GameContext';
import { useAuth } from '../contexts/AuthContext';
import './GameControls.css';

const GameControls = () => {
  const { state, endTurn, rollDice } = useGame();
  const { user } = useAuth();
  const { gamePhase, currentPlayer, dice } = state;
  const [confirmingEnd, setConfirmingEnd] = useState(false);
  
  // Check if it's the current user's turn
  const isMyTurn = user && currentPlayer && user.id === currentPlayer.id;
  
  // Check if dice have been rolled this turn
  const hasRolled = dice.roll1 !== 0 && dice.roll2 !== 0;
  
  // Check if the game is active
  const isGameActive = gamePhase === 'playing';

  // Handle roll dice
  const handleRollDice = () => {
    if (isMyTurn && !hasRolled) {
      rollDice();
    }
  };

  // Handle end turn with confirmation
  const handleEndTurn = () => {
    if (!confirmingEnd) {
      setConfirmingEnd(true);
      setTimeout(() => setConfirmingEnd(false), 3000); // Reset after 3 seconds
      return;
    }
    
    endTurn();
    setConfirmingEnd(false);
  };

  if (!isGameActive) {
    return (
      <div className="game-controls disabled">
        <div className="controls-status">Game not in progress</div>
      </div>
    );
  }

  if (!isMyTurn) {
    return (
      <div className="game-controls disabled">
        <div className="controls-status">Waiting for {currentPlayer?.name}'s turn</div>
      </div>
    );
  }

  return (
    <div className="game-controls">
      <button 
        className={`control-button roll-button ${!hasRolled ? 'primary' : 'disabled'}`}
        onClick={handleRollDice}
        disabled={hasRolled}
      >
        Roll Dice
      </button>
      
      <button 
        className={`control-button end-turn-button ${hasRolled ? (confirmingEnd ? 'warning' : 'primary') : 'disabled'}`}
        onClick={handleEndTurn}
        disabled={!hasRolled}
      >
        {confirmingEnd ? 'Confirm End Turn' : 'End Turn'}
      </button>
      
      <div className="action-buttons">
        <button 
          className="action-button"
          onClick={() => {/* Trade action */}}
        >
          Trade
        </button>
        
        <button 
          className="action-button"
          onClick={() => {/* Manage Properties action */}}
        >
          Properties
        </button>
        
        <button 
          className="action-button"
          onClick={() => {/* View Cards action */}}
        >
          My Cards
        </button>
      </div>
    </div>
  );
};

export default GameControls; 