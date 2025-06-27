import React, { useEffect, useRef, useState } from 'react';
import { useGame } from '../../../game-state/contexts/GameContext';
import './PlayerToken.css';

export default function AnimatedPlayerToken({ player, boardSize = 600, onAnimationComplete }) {
  const { state } = useGame();
  const tokenRef = useRef(null);
  const [currentPosition, setCurrentPosition] = useState(player.position || 0);
  const [isAnimating, setIsAnimating] = useState(false);
  
  const isCurrentPlayer = state.currentPlayer?.id === player.id;
  const isInJail = player.jailTurns > 0;

  // Calculate position coordinates based on board space
  const calculatePositionCoords = (position) => {
    const spaceSize = boardSize / 10; // 10 spaces per side
    let x, y;
    const side = Math.floor(position / 10);
    const offset = position % 10;

    switch (side) {
      case 0: // Bottom row (right to left)
        x = boardSize - (offset + 1) * spaceSize;
        y = boardSize - spaceSize;
        break;
      case 1: // Left column (bottom to top)
        x = 0;
        y = boardSize - (offset + 1) * spaceSize;
        break;
      case 2: // Top row (left to right)
        x = offset * spaceSize;
        y = 0;
        break;
      case 3: // Right column (top to bottom)
        x = boardSize - spaceSize;
        y = offset * spaceSize;
        break;
      default:
        x = 0;
        y = 0;
    }

    // Center the token within the space
    return { 
      x: x + spaceSize / 2, 
      y: y + spaceSize / 2 
    };
  };

  // Animate movement from current position to new position
  const animateMovement = (fromPos, toPos, steps) => {
    return new Promise((resolve) => {
      console.log(`[AnimatedPlayerToken] Animating player ${player.id} from ${fromPos} to ${toPos} (${steps} steps)`);
      
      setIsAnimating(true);
      
      // Calculate the path
      const path = [];
      let current = fromPos;
      
      for (let i = 0; i < steps; i++) {
        current = (current + 1) % 40;
        path.push(current);
      }

      let stepIndex = 0;
      
      const moveToNextStep = () => {
        if (stepIndex >= path.length) {
          // Animation complete
          setCurrentPosition(toPos);
          setIsAnimating(false);
          
          if (onAnimationComplete) {
            onAnimationComplete(player.id, toPos);
          }
          
          resolve();
          return;
        }

        const nextPosition = path[stepIndex];
        setCurrentPosition(nextPosition);
        stepIndex++;
        
        // Continue to next step after delay
        setTimeout(moveToNextStep, 300); // 300ms per step
      };

      // Start the animation
      moveToNextStep();
    });
  };

  // Handle position changes from game state
  useEffect(() => {
    const newPosition = player.position || 0;
    
    if (newPosition !== currentPosition && !isAnimating) {
      // Calculate steps moved
      let steps;
      if (newPosition > currentPosition) {
        steps = newPosition - currentPosition;
      } else {
        // Wrapped around the board
        steps = (40 - currentPosition) + newPosition;
      }
      
      // Only animate if steps > 0 and reasonable (not initial positioning)
      if (steps > 0 && steps <= 12) { // Max normal roll is 12
        animateMovement(currentPosition, newPosition, steps);
      } else {
        // Just update position immediately (for initial setup, etc.)
        setCurrentPosition(newPosition);
      }
    }
  }, [player.position, currentPosition, isAnimating]);

  // Calculate current display position
  const coords = calculatePositionCoords(currentPosition);

  // Player status indicators
  const getStatusIndicators = () => {
    const indicators = [];

    if (player.cash < 0) {
      indicators.push({
        icon: '💸',
        tooltip: 'In debt',
        class: 'status-debt'
      });
    }

    if (isInJail) {
      indicators.push({
        icon: '🔒',
        tooltip: `In jail for ${player.jailTurns} more turns`,
        class: 'status-jail'
      });
    }

    if (player.suspicionLevel > 50) {
      indicators.push({
        icon: '👮',
        tooltip: 'High suspicion level',
        class: 'status-suspicious'
      });
    }

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
      ref={tokenRef}
      className={`player-token ${isCurrentPlayer ? 'current' : ''} ${isAnimating ? 'animating' : ''}`}
      style={{
        position: 'absolute',
        transform: `translate(${coords.x}px, ${coords.y}px)`,
        transition: isAnimating ? 'transform 0.3s ease-in-out' : 'none',
        backgroundColor: player.color,
        zIndex: isAnimating ? 1000 : 100,
      }}
      data-player-id={player.id}
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
          {isAnimating && <div>Moving... ({currentPosition})</div>}
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

      {/* Animation indicator */}
      {isAnimating && (
        <div className="animation-indicator">
          ⚡
        </div>
      )}
    </div>
  );
}