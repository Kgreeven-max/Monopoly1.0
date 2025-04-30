import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import { useNotifications } from '../contexts/NotificationContext';
import './DiceRoller.css';

const DiceRoller = ({ disabled = false }) => {
  const { state, rollDice } = useGame();
  const { addNotification } = useNotifications();
  const [rolling, setRolling] = useState(false);
  const { dice } = state;

  useEffect(() => {
    // When dice values change and are not 0, show animation
    if (dice.roll1 !== 0 && dice.roll2 !== 0 && rolling) {
      // End the animation after a delay
      const timer = setTimeout(() => {
        setRolling(false);
        
        // Notify the user of the roll
        addNotification({
          type: 'info',
          title: 'Dice Rolled',
          message: `You rolled ${dice.roll1 + dice.roll2} (${dice.roll1} + ${dice.roll2})`,
          duration: 3000,
        });
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [dice, rolling, addNotification]);

  const handleRollDice = () => {
    if (disabled || rolling) return;
    
    setRolling(true);
    rollDice();
  };

  const getDiceFace = (value) => {
    if (rolling) {
      return Math.floor(Math.random() * 6) + 1;
    }
    return value;
  };

  return (
    <div className="dice-roller">
      <div className="dice-container">
        <div className={`dice ${rolling ? 'rolling' : ''}`} data-face={getDiceFace(dice.roll1)}>
          <div className="face face-1">⚀</div>
          <div className="face face-2">⚁</div>
          <div className="face face-3">⚂</div>
          <div className="face face-4">⚃</div>
          <div className="face face-5">⚄</div>
          <div className="face face-6">⚅</div>
        </div>
        <div className={`dice ${rolling ? 'rolling' : ''}`} data-face={getDiceFace(dice.roll2)}>
          <div className="face face-1">⚀</div>
          <div className="face face-2">⚁</div>
          <div className="face face-3">⚂</div>
          <div className="face face-4">⚃</div>
          <div className="face face-5">⚄</div>
          <div className="face face-6">⚅</div>
        </div>
      </div>
      
      <button 
        className="roll-button" 
        onClick={handleRollDice} 
        disabled={disabled || rolling}
      >
        {rolling ? 'Rolling...' : 'Roll Dice'}
      </button>
      
      {!rolling && dice.roll1 !== 0 && dice.roll2 !== 0 && (
        <div className="dice-result">
          You rolled {dice.roll1 + dice.roll2} ({dice.roll1} + {dice.roll2})
        </div>
      )}
    </div>
  );
};

export default DiceRoller; 