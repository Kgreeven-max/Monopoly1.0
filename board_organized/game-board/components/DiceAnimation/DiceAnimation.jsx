import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';
import './DiceAnimation.css';

const DiceAnimation = ({ diceRoll, onComplete }) => {
  const [isRolling, setIsRolling] = useState(true);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    if (diceRoll) {
      setIsRolling(true);
      setShowResult(false);

      // Show rolling animation
      setTimeout(() => {
        setIsRolling(false);
        setShowResult(true);
      }, 1000);

      // Hide dice after showing result
      setTimeout(() => {
        if (onComplete) onComplete();
      }, 2500);
    }
  }, [diceRoll, onComplete]);

  if (!diceRoll || diceRoll.length !== 2) return null;

  const renderDiceFace = (value) => {
    const dots = [];
    const dotPositions = {
      1: [[50, 50]],
      2: [[30, 30], [70, 70]],
      3: [[30, 30], [50, 50], [70, 70]],
      4: [[30, 30], [70, 30], [30, 70], [70, 70]],
      5: [[30, 30], [70, 30], [50, 50], [30, 70], [70, 70]],
      6: [[30, 30], [70, 30], [30, 50], [70, 50], [30, 70], [70, 70]]
    };

    const positions = dotPositions[value] || [];
    
    positions.forEach((pos, index) => {
      dots.push(
        <div
          key={index}
          className="dice-dot"
          style={{
            left: `${pos[0]}%`,
            top: `${pos[1]}%`
          }}
        />
      );
    });

    return dots;
  };

  return (
    <Box className="dice-animation-container">
      <div className={`dice ${isRolling ? 'rolling' : ''} ${showResult ? 'show-result' : ''}`}>
        <div className="dice-face">
          {!isRolling && renderDiceFace(diceRoll[0])}
        </div>
      </div>
      <div className={`dice ${isRolling ? 'rolling' : ''} ${showResult ? 'show-result' : ''}`}>
        <div className="dice-face">
          {!isRolling && renderDiceFace(diceRoll[1])}
        </div>
      </div>
      {showResult && (
        <div className="dice-total">
          {diceRoll[0] + diceRoll[1]}
        </div>
      )}
    </Box>
  );
};

export default DiceAnimation;