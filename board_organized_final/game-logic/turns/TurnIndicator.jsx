import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { useAuth } from '../contexts/AuthContext';
import './TurnIndicator.css';

const TurnIndicator = ({ turnTimeLimit = 60 }) => {
  const { state } = useGame();
  const { user } = useAuth();
  const { currentPlayer, gamePhase, turn } = state;
  const [timeLeft, setTimeLeft] = useState(turnTimeLimit);
  const [timerActive, setTimerActive] = useState(false);

  // Reset and start timer when turn changes
  useEffect(() => {
    if (gamePhase === 'playing' && currentPlayer) {
      setTimeLeft(turnTimeLimit);
      setTimerActive(true);
    } else {
      setTimerActive(false);
    }
  }, [currentPlayer, gamePhase, turn, turnTimeLimit]);

  // Timer countdown
  useEffect(() => {
    let timer;
    
    if (timerActive && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prevTime => prevTime - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setTimerActive(false);
    }
    
    return () => clearInterval(timer);
  }, [timerActive, timeLeft]);

  // Calculate timer percentage for progress bar
  const timerPercentage = (timeLeft / turnTimeLimit) * 100;
  
  // Determine warning class based on time left
  const getTimerClass = () => {
    if (timeLeft <= 10) return 'timer-critical';
    if (timeLeft <= 20) return 'timer-warning';
    return '';
  };

  // Check if it's the current user's turn
  const isMyTurn = user && currentPlayer && user.id === currentPlayer.id;

  if (gamePhase !== 'playing') {
    return (
      <div className="turn-indicator game-not-playing">
        <div className="turn-status">Game not in progress</div>
      </div>
    );
  }

  if (!currentPlayer) {
    return (
      <div className="turn-indicator">
        <div className="turn-status">Waiting for next turn...</div>
      </div>
    );
  }

  return (
    <div className={`turn-indicator ${isMyTurn ? 'my-turn' : ''}`}>
      <div className="turn-info">
        <div className="current-player">
          <div 
            className="player-token" 
            style={{ backgroundColor: currentPlayer.color }}
          ></div>
          <div className="player-name">
            {isMyTurn ? "Your Turn" : `${currentPlayer.name}'s Turn`}
          </div>
        </div>
        
        <div className="turn-number">Turn {turn}</div>
      </div>
      
      {turnTimeLimit > 0 && (
        <div className="timer-container">
          <div className="timer-label">
            Time left: <span className={getTimerClass()}>{timeLeft}s</span>
          </div>
          <div className="timer-bar-container">
            <div 
              className={`timer-bar ${getTimerClass()}`} 
              style={{ width: `${timerPercentage}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TurnIndicator; 