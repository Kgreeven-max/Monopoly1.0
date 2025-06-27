import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useGame } from '../../../game-state/contexts/GameContext';
import PropertySpace from '../Spaces/PropertySpace';
import SpecialSpace from '../Spaces/SpecialSpace';
import PlayerToken from '../PlayerToken/PlayerToken';
import DiceAnimation from '../DiceAnimation/DiceAnimation';
import useSimplePlayerAnimation from '../../hooks/useSimplePlayerAnimation';
import './GameBoard.css';

const BOARD_SPACES = 40;
const BOARD_SIZE = 600;

export default function EnhancedGameBoard() {
  const { state } = useGame();
  const boardRef = useRef(null);
  const [diceRoll, setDiceRoll] = useState(null);
  const [showDiceAnimation, setShowDiceAnimation] = useState(false);
  const [isRollingDice, setIsRollingDice] = useState(false);
  const [playerPositions, setPlayerPositions] = useState(new Map());

  // Use our simple animation hook
  const {
    isAnimating,
    animatingPlayer,
    animatePlayerMovement,
    stopAllAnimations
  } = useSimplePlayerAnimation();

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

  // Track player positions and detect changes for animation
  useEffect(() => {
    if (state.players && state.players.length > 0) {
      state.players.forEach(player => {
        const currentPos = player.position || 0;
        const lastKnownPos = playerPositions.get(player.id);

        if (lastKnownPos !== undefined && lastKnownPos !== currentPos && !isAnimating) {
          // Calculate movement steps
          let steps;
          if (currentPos > lastKnownPos) {
            steps = currentPos - lastKnownPos;
          } else if (currentPos < lastKnownPos) {
            // Wrapped around the board
            steps = (40 - lastKnownPos) + currentPos;
          } else {
            steps = 0;
          }

          // Only animate reasonable movements (typical dice rolls)
          if (steps > 0 && steps <= 12) {
            console.log(`[EnhancedGameBoard] Animating player ${player.id}: ${lastKnownPos} → ${currentPos} (${steps} steps)`);
            
            animatePlayerMovement(
              player.id,
              lastKnownPos,
              currentPos,
              steps,
              (finalPosition) => {
                console.log(`[EnhancedGameBoard] Animation completed for player ${player.id} at position ${finalPosition}`);
                setPlayerPositions(prev => new Map(prev).set(player.id, finalPosition));
              }
            ).catch(error => {
              console.error(`[EnhancedGameBoard] Animation failed for player ${player.id}:`, error);
              // Fallback: just update position
              setPlayerPositions(prev => new Map(prev).set(player.id, currentPos));
            });
          } else {
            // Update position without animation (for initial setup, etc.)
            setPlayerPositions(prev => new Map(prev).set(player.id, currentPos));
          }
        } else if (lastKnownPos === undefined) {
          // First time seeing this player, just set position
          setPlayerPositions(prev => new Map(prev).set(player.id, currentPos));
        }
      });
    }
  }, [state.players, playerPositions, animatePlayerMovement, isAnimating]);

  // Handle dice roll events from the game context
  useEffect(() => {
    if (state.lastDiceRoll && state.lastDiceRoll.length === 2) {
      console.log('[EnhancedGameBoard] Dice roll detected:', state.lastDiceRoll);
      
      // Show dice animation
      setDiceRoll(state.lastDiceRoll);
      setShowDiceAnimation(true);
      setIsRollingDice(true);
    }
  }, [state.lastDiceRoll]);

  // Handle dice animation completion
  const handleDiceAnimationComplete = useCallback(() => {
    console.log('[EnhancedGameBoard] Dice animation completed');
    setShowDiceAnimation(false);
    setIsRollingDice(false);
    setDiceRoll(null);
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

  // Render player tokens with enhanced positioning
  const renderPlayers = useCallback(() => {
    const positions = calculateSpacePositions();
    
    return state.players?.map((player) => {
      // Use animated position if available, otherwise use game state position
      const displayPosition = playerPositions.get(player.id) ?? player.position ?? 0;
      const position = positions[displayPosition];
      
      return (
        <div
          key={player.id}
          data-player-id={player.id}
          data-current-position={displayPosition}
          style={{
            position: 'absolute',
            transform: `translate(${position.x}px, ${position.y}px)`,
            transition: isAnimating && animatingPlayer === player.id ? 'transform 0.3s ease-in-out' : 'none'
          }}
        >
          <PlayerToken
            player={player}
            position={position}
          />
        </div>
      );
    });
  }, [state.players, calculateSpacePositions, playerPositions, isAnimating, animatingPlayer]);

  // Debug functions for testing
  const testPlayerMovement = useCallback(() => {
    if (state.players && state.players.length > 0) {
      const testPlayer = state.players[0];
      const currentPos = playerPositions.get(testPlayer.id) ?? testPlayer.position ?? 0;
      const steps = Math.floor(Math.random() * 8) + 1; // 1-8 steps
      const newPos = (currentPos + steps) % 40;
      
      console.log(`[EnhancedGameBoard] Testing movement for player ${testPlayer.id}: ${currentPos} → ${newPos}`);
      
      animatePlayerMovement(
        testPlayer.id,
        currentPos,
        newPos,
        steps,
        (finalPosition) => {
          console.log(`[EnhancedGameBoard] Test animation completed at position ${finalPosition}`);
          setPlayerPositions(prev => new Map(prev).set(testPlayer.id, finalPosition));
        }
      ).catch(error => {
        console.error('[EnhancedGameBoard] Test animation failed:', error);
      });
    }
  }, [state.players, playerPositions, animatePlayerMovement]);

  const testDiceRoll = useCallback(() => {
    const roll = [Math.floor(Math.random() * 6) + 1, Math.floor(Math.random() * 6) + 1];
    console.log(`[EnhancedGameBoard] Testing dice roll:`, roll);
    
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

          {/* Simple Debug Controls */}
          <div className="debug-controls" style={{ 
            position: 'absolute', 
            bottom: '10px', 
            left: '50%', 
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '8px'
          }}>
            <button 
              onClick={testPlayerMovement}
              disabled={isAnimating || state.players?.length === 0}
              style={{
                padding: '6px 10px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              Test Move
            </button>
            <button 
              onClick={testDiceRoll}
              disabled={isRollingDice}
              style={{
                padding: '6px 10px',
                backgroundColor: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              Test Dice
            </button>
            <button 
              onClick={stopAllAnimations}
              style={{
                padding: '6px 10px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              Stop
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