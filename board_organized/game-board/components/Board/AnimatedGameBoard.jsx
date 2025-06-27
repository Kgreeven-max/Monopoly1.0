import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useGame } from '../../../game-state/contexts/GameContext';
import PropertySpace from '../Spaces/PropertySpace';
import SpecialSpace from '../Spaces/SpecialSpace';
import AnimatedPlayerToken from '../PlayerToken/AnimatedPlayerToken';
import DiceAnimation from '../DiceAnimation/DiceAnimation';
import usePlayerAnimation from '../../hooks/usePlayerAnimation';
import './GameBoard.css';

const BOARD_SPACES = 40;
const BOARD_SIZE = 600;

export default function AnimatedGameBoard() {
  const { state } = useGame();
  const boardRef = useRef(null);
  const [diceRoll, setDiceRoll] = useState(null);
  const [showDiceAnimation, setShowDiceAnimation] = useState(false);
  const [isRollingDice, setIsRollingDice] = useState(false);

  // Use our animation hook
  const {
    isAnimating,
    animatingPlayer,
    animatePlayerMovement,
    stopAllAnimations
  } = usePlayerAnimation();

  // Calculate positions for each space on the board
  const calculateSpacePositions = useCallback(() => {
    const positions = [];
    const spaceSize = BOARD_SIZE / 10; // 10 spaces per side

    for (let i = 0; i < BOARD_SPACES; i++) {
      let x, y;
      const side = Math.floor(i / 10);
      const offset = i % 10;

      switch (side) {
        case 0: // Bottom row
          x = BOARD_SIZE - (offset + 1) * spaceSize;
          y = BOARD_SIZE - spaceSize;
          break;
        case 1: // Left column
          x = 0;
          y = BOARD_SIZE - (offset + 1) * spaceSize;
          break;
        case 2: // Top row
          x = offset * spaceSize;
          y = 0;
          break;
        case 3: // Right column
          x = BOARD_SIZE - spaceSize;
          y = offset * spaceSize;
          break;
        default:
          x = 0;
          y = 0;
      }

      positions.push({ x, y });
    }

    return positions;
  }, []);

  // Handle dice roll events from the game context
  useEffect(() => {
    if (state.lastDiceRoll && state.lastDiceRoll.length === 2) {
      console.log('[AnimatedGameBoard] Dice roll detected:', state.lastDiceRoll);
      
      // Show dice animation
      setDiceRoll(state.lastDiceRoll);
      setShowDiceAnimation(true);
      setIsRollingDice(true);
    }
  }, [state.lastDiceRoll]);

  // Handle player movement events from the game context
  useEffect(() => {
    // Listen for player position changes and trigger animations
    const checkForMovement = () => {
      state.players.forEach(player => {
        const playerElement = document.querySelector(`[data-player-id="${player.id}"]`);
        if (playerElement) {
          const currentDisplayPosition = parseInt(playerElement.dataset.currentPosition || '0');
          const newPosition = player.position || 0;
          
          if (currentDisplayPosition !== newPosition && !isAnimating) {
            // Calculate movement steps
            let steps;
            if (newPosition > currentDisplayPosition) {
              steps = newPosition - currentDisplayPosition;
            } else if (newPosition < currentDisplayPosition) {
              // Wrapped around the board
              steps = (40 - currentDisplayPosition) + newPosition;
            } else {
              steps = 0;
            }

            // Animate if reasonable movement
            if (steps > 0 && steps <= 12) {
              console.log(`[AnimatedGameBoard] Animating player ${player.id} movement: ${currentDisplayPosition} → ${newPosition} (${steps} steps)`);
              
              animatePlayerMovement(
                player.id,
                currentDisplayPosition,
                newPosition,
                steps,
                (finalPosition) => {
                  console.log(`[AnimatedGameBoard] Animation completed for player ${player.id} at position ${finalPosition}`);
                  // Update the data attribute
                  if (playerElement) {
                    playerElement.dataset.currentPosition = finalPosition.toString();
                  }
                }
              ).catch(error => {
                console.error(`[AnimatedGameBoard] Animation failed for player ${player.id}:`, error);
              });
            }
          }
        }
      });
    };

    // Check for movements on every state update
    checkForMovement();
  }, [state.players, animatePlayerMovement, isAnimating]);

  // Handle dice animation completion
  const handleDiceAnimationComplete = useCallback(() => {
    console.log('[AnimatedGameBoard] Dice animation completed');
    setShowDiceAnimation(false);
    setIsRollingDice(false);
    setDiceRoll(null);
  }, []);

  // Handle player animation completion
  const handlePlayerAnimationComplete = useCallback((playerId, finalPosition) => {
    console.log(`[AnimatedGameBoard] Player ${playerId} animation completed at position ${finalPosition}`);
  }, []);

  // Render board spaces
  const renderSpaces = useCallback(() => {
    const positions = calculateSpacePositions();
    return state.properties?.map((property, index) => (
      property.type === 'property' ? (
        <PropertySpace
          key={property.id}
          property={property}
          position={positions[index]}
        />
      ) : (
        <SpecialSpace
          key={property.id}
          space={property}
          position={positions[index]}
        />
      )
    ));
  }, [state.properties, calculateSpacePositions]);

  // Render player tokens with animation
  const renderPlayers = useCallback(() => {
    return state.players?.map((player) => (
      <AnimatedPlayerToken
        key={player.id}
        player={player}
        boardSize={BOARD_SIZE}
        onAnimationComplete={handlePlayerAnimationComplete}
      />
    ));
  }, [state.players, handlePlayerAnimationComplete]);

  // Debug functions for testing
  const testPlayerMovement = useCallback(() => {
    if (state.players && state.players.length > 0) {
      const testPlayer = state.players[0];
      const currentPos = testPlayer.position || 0;
      const newPos = (currentPos + 7) % 40; // Move 7 spaces
      
      console.log(`[AnimatedGameBoard] Testing movement for player ${testPlayer.id}: ${currentPos} → ${newPos}`);
      
      animatePlayerMovement(
        testPlayer.id,
        currentPos,
        newPos,
        7,
        (finalPosition) => {
          console.log(`[AnimatedGameBoard] Test animation completed at position ${finalPosition}`);
        }
      ).catch(error => {
        console.error('[AnimatedGameBoard] Test animation failed:', error);
      });
    }
  }, [state.players, animatePlayerMovement]);

  const testDiceRoll = useCallback(() => {
    const roll = [Math.floor(Math.random() * 6) + 1, Math.floor(Math.random() * 6) + 1];
    console.log(`[AnimatedGameBoard] Testing dice roll:`, roll);
    
    setDiceRoll(roll);
    setShowDiceAnimation(true);
    setIsRollingDice(true);
  }, []);

  return (
    <div className="game-board-container">
      <div className="game-board" ref={boardRef} style={{ width: BOARD_SIZE, height: BOARD_SIZE, position: 'relative' }}>
        {/* Center area with logo and game info */}
        <div className="board-center">
          <h2>Pi-nopoly</h2>
          <div className="game-info">
            <p>Mode: {state.gameMode}</p>
            <p>Turn: {state.turn}</p>
            <p>Community Fund: ${state.communityFund}</p>
            
            {/* Animation status */}
            {isAnimating && (
              <p style={{ color: 'orange', fontWeight: 'bold' }}>
                🎬 Player {animatingPlayer} moving...
              </p>
            )}
            
            {isRollingDice && (
              <p style={{ color: 'blue', fontWeight: 'bold' }}>
                🎲 Rolling dice...
              </p>
            )}
          </div>

          {/* Debug Controls */}
          <div className="debug-controls" style={{ 
            position: 'absolute', 
            bottom: '10px', 
            left: '50%', 
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '10px'
          }}>
            <button 
              onClick={testPlayerMovement}
              disabled={isAnimating || state.players?.length === 0}
              style={{
                padding: '8px 12px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              Test Move
            </button>
            <button 
              onClick={testDiceRoll}
              disabled={isRollingDice}
              style={{
                padding: '8px 12px',
                backgroundColor: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              Test Dice
            </button>
            <button 
              onClick={stopAllAnimations}
              style={{
                padding: '8px 12px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              Stop All
            </button>
          </div>
        </div>

        {/* Board spaces */}
        <div className="board-spaces">
          {renderSpaces()}
        </div>

        {/* Player tokens with animation */}
        <div className="player-tokens">
          {renderPlayers()}
        </div>

        {/* Dice animation overlay */}
        {showDiceAnimation && diceRoll && (
          <div className="dice-overlay" style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 2000
          }}>
            <DiceAnimation 
              diceRoll={diceRoll} 
              onComplete={handleDiceAnimationComplete}
            />
          </div>
        )}
      </div>
    </div>
  );
}