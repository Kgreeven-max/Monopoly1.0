import React from 'react';
import { useGame } from '../../contexts/GameContext';
import { useAuth } from '../../contexts/AuthContext';
import './PlayerControls.css';

export default function PlayerControls() {
  const { state, rollDice, endTurn, purchaseProperty } = useGame();
  const { user } = useAuth();

  const isCurrentPlayer = state.currentPlayer?.id === user?.id;
  const canRoll = isCurrentPlayer && !state.dice.roll1 && !state.dice.roll2;
  const canEndTurn = isCurrentPlayer && (state.dice.roll1 || state.dice.roll2);
  const canBuyProperty = isCurrentPlayer && state.currentSpace?.type === 'property' && !state.currentSpace.ownerId;

  // Handle dice roll
  const handleRollDice = async () => {
    if (!canRoll) return;
    try {
      await rollDice();
    } catch (error) {
      console.error('Error rolling dice:', error);
    }
  };

  // Handle end turn
  const handleEndTurn = async () => {
    if (!canEndTurn) return;
    try {
      await endTurn();
    } catch (error) {
      console.error('Error ending turn:', error);
    }
  };

  // Handle property purchase
  const handlePurchaseProperty = async () => {
    if (!canBuyProperty) return;
    try {
      await purchaseProperty(state.currentSpace.id);
    } catch (error) {
      console.error('Error purchasing property:', error);
    }
  };

  // Render dice
  const renderDice = () => {
    if (!state.dice.roll1 && !state.dice.roll2) {
      return null;
    }

    return (
      <div className="dice-container">
        <div className="dice">{state.dice.roll1}</div>
        <div className="dice">{state.dice.roll2}</div>
        {state.dice.roll1 === state.dice.roll2 && (
          <div className="doubles-indicator">Doubles!</div>
        )}
      </div>
    );
  };

  return (
    <div className="player-controls">
      {/* Game info */}
      <div className="game-info">
        <h3>Turn {state.turn}</h3>
        <p className="current-player">
          Current Player: {state.currentPlayer?.name || 'Waiting...'}
        </p>
        <p className="economic-state">
          Economy: <span className={state.economicState}>{state.economicState}</span>
        </p>
      </div>

      {/* Dice section */}
      <div className="dice-section">
        {renderDice()}
        <button
          className="roll-button"
          onClick={handleRollDice}
          disabled={!canRoll}
        >
          Roll Dice
        </button>
      </div>

      {/* Action buttons */}
      <div className="action-buttons">
        <button
          className="purchase-button"
          onClick={handlePurchaseProperty}
          disabled={!canBuyProperty}
        >
          Buy Property (${state.currentSpace?.price || 0})
        </button>

        <button
          className="end-turn-button"
          onClick={handleEndTurn}
          disabled={!canEndTurn}
        >
          End Turn
        </button>
      </div>

      {/* Player status */}
      {user && (
        <div className="player-status">
          <div className="status-item">
            <span>Cash</span>
            <strong>${state.players.find(p => p.id === user.id)?.cash || 0}</strong>
          </div>
          <div className="status-item">
            <span>Properties</span>
            <strong>{state.players.find(p => p.id === user.id)?.properties?.length || 0}</strong>
          </div>
          <div className="status-item">
            <span>Net Worth</span>
            <strong>${state.players.find(p => p.id === user.id)?.netWorth || 0}</strong>
          </div>
        </div>
      )}
    </div>
  );
} 