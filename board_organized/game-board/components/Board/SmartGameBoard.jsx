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

export default function SmartGameBoard() {
  const { state } = useGame();
  const boardRef = useRef(null);
  const [diceRoll, setDiceRoll] = useState(null);
  const [showDiceAnimation, setShowDiceAnimation] = useState(false);
  const [isRollingDice, setIsRollingDice] = useState(false);
  
  // Single source of truth for player positions
  // This tracks the actual displayed position during animations
  const [displayPositions, setDisplayPositions] = useState(new Map());
  
  // Track game state positions to detect changes
  const prevGamePositions = useRef(new Map());

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

      positions.push({ x: x + spaceSize/2, y: y + spaceSize/2 }); // Center of space
    }

    return positions;
  }, []);

  // Initialize display positions from game state
  useEffect(() => {
    if (state.players && state.players.length > 0) {
      const newDisplayPositions = new Map();
      state.players.forEach(player => {
        const position = player.position || 0;
        newDisplayPositions.set(player.id, position);
        prevGamePositions.current.set(player.id, position);
      });
      setDisplayPositions(newDisplayPositions);
    }
  }, []); // Only run once on mount

  // Listen for dice roll events from GameContext state
  useEffect(() => {
    if (state.lastDiceRoll && state.lastDiceRoll.roll && state.lastDiceRoll.roll.length === 2) {
      console.log('[SmartGameBoard] Dice roll detected:', state.lastDiceRoll);
      
      // Show dice animation for the roll
      setDiceRoll(state.lastDiceRoll.roll);
      setShowDiceAnimation(true);
      setIsRollingDice(true);
    }
  }, [state.lastDiceRoll]);

  // Listen for player position changes and animate movement
  useEffect(() => {
    if (!state.players || state.players.length === 0 || isAnimating) return;
    
    state.players.forEach(player => {
      const currentGamePos = player.position || 0;
      const prevPos = prevGamePositions.current.get(player.id);
      const currentDisplayPos = displayPositions.get(player.id) || 0;
      
      // Detect if position changed in game state
      if (prevPos !== undefined && currentGamePos !== prevPos) {
        console.log(`[SmartGameBoard] Position change detected for player ${player.id}: ${prevPos} → ${currentGamePos}`);
        
        // Calculate steps (handle wrap-around)
        let steps;
        if (currentGamePos > prevPos) {
          steps = currentGamePos - prevPos;
        } else if (currentGamePos < prevPos) {
          // Wrapped around the board (passed GO)
          steps = (40 - prevPos) + currentGamePos;
        } else {
          steps = 0;
        }
        
        // Handle special cases (like Go to Jail)
        if (steps > 20) {
          // This is likely a "Go to Jail" or similar teleport
          console.log(`[SmartGameBoard] Teleporting player ${player.id} to position ${currentGamePos}`);
          setDisplayPositions(prev => new Map(prev).set(player.id, currentGamePos));
          prevGamePositions.current.set(player.id, currentGamePos);
        } else if (steps > 0 && steps <= 12) {
          // Normal dice roll movement - animate it
          console.log(`[SmartGameBoard] Animating player ${player.id} movement: ${steps} steps`);
          
          animatePlayerMovement(
            player.id,
            currentDisplayPos,
            currentGamePos,
            steps,
            (finalPosition) => {
              // Animation complete - ensure we're at the correct position
              console.log(`[SmartGameBoard] Animation complete for player ${player.id}`);
              setDisplayPositions(prev => new Map(prev).set(player.id, finalPosition));
              prevGamePositions.current.set(player.id, finalPosition);
            },
            (intermediatePosition, stepNumber) => {
              // Update position for each step
              setDisplayPositions(prev => new Map(prev).set(player.id, intermediatePosition));
            }
          ).catch(error => {
            // Animation failed - just update to final position
            console.error(`[SmartGameBoard] Animation failed:`, error);
            setDisplayPositions(prev => new Map(prev).set(player.id, currentGamePos));
            prevGamePositions.current.set(player.id, currentGamePos);
          });
        } else {
          // No movement needed
          prevGamePositions.current.set(player.id, currentGamePos);
        }
      }
    });
  }, [state.players, isAnimating, animatePlayerMovement, displayPositions]);

  // Handle dice animation completion
  const handleDiceAnimationComplete = useCallback(() => {
    console.log('[SmartGameBoard] Dice animation completed');
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

  // Render player tokens
  const renderPlayers = useCallback(() => {
    const positions = calculateSpacePositions();
    
    return state.players?.map((player) => {
      // Use display position (animated position)
      const currentPosition = displayPositions.get(player.id) || player.position || 0;
      const spacePosition = positions[currentPosition];
      
      if (!spacePosition) {
        console.error(`No position found for space ${currentPosition}`);
        return null;
      }
      
      // Calculate offset to prevent token overlap
      const playerIndex = state.players.findIndex(p => p.id === player.id);
      const totalPlayers = state.players.length;
      const angle = (playerIndex / totalPlayers) * 2 * Math.PI;
      const offsetRadius = 15;
      const offsetX = Math.cos(angle) * offsetRadius;
      const offsetY = Math.sin(angle) * offsetRadius;
      
      return (
        <div
          key={player.id}
          data-player-id={player.id}
          className="player-token"
          style={{
            position: 'absolute',
            left: `${spacePosition.x + offsetX}px`,
            top: `${spacePosition.y + offsetY}px`,
            transform: 'translate(-50%, -50%)',
            transition: isAnimating && animatingPlayer === player.id ? 'none' : 'all 300ms ease-out',
            zIndex: animatingPlayer === player.id ? 100 : 10
          }}
        >
          <PlayerToken
            player={player}
            position={spacePosition}
          />
        </div>
      );
    });
  }, [state.players, displayPositions, calculateSpacePositions, isAnimating, animatingPlayer]);

  // Debug functions for testing
  const testPlayerMovement = useCallback(() => {
    if (state.players && state.players.length > 0) {
      const testPlayer = state.players[0];
      const currentPos = displayPositions.get(testPlayer.id) || 0;
      const steps = Math.floor(Math.random() * 6) + 1; // 1-6 steps
      const newPos = (currentPos + steps) % 40;
      
      console.log(`[Test] Moving player ${testPlayer.id}: ${currentPos} → ${newPos} (${steps} steps)`);
      
      // Simulate a position change
      prevGamePositions.current.set(testPlayer.id, currentPos);
      
      animatePlayerMovement(
        testPlayer.id,
        currentPos,
        newPos,
        steps,
        (finalPosition) => {
          console.log(`[Test] Animation completed at position ${finalPosition}`);
          setDisplayPositions(prev => new Map(prev).set(testPlayer.id, finalPosition));
        },
        (intermediatePosition) => {
          setDisplayPositions(prev => new Map(prev).set(testPlayer.id, intermediatePosition));
        }
      );
    }
  }, [state.players, displayPositions, animatePlayerMovement]);

  const testDiceRoll = useCallback(() => {
    const roll = [Math.floor(Math.random() * 6) + 1, Math.floor(Math.random() * 6) + 1];
    console.log(`[Test] Dice roll:`, roll);
    
    setDiceRoll(roll);
    setShowDiceAnimation(true);
    setIsRollingDice(true);
    
    // Test player movement after dice animation
    setTimeout(() => {
      testPlayerMovement();
    }, 2500);
  }, [testPlayerMovement]);

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
          </div>
          
          {/* Debug buttons */}
          <div className="debug-controls" style={{ marginTop: '20px' }}>
            <button onClick={testDiceRoll} style={{ marginRight: '10px' }}>
              Test Dice & Movement
            </button>
            <button onClick={testPlayerMovement}>
              Test Movement Only
            </button>
          </div>
        </div>

        {/* Render board spaces */}
        {renderSpaces()}
        
        {/* Render player tokens */}
        {renderPlayers()}
        
        {/* Dice animation overlay */}
        {showDiceAnimation && diceRoll && (
          <DiceAnimation
            dice={diceRoll}
            isRolling={isRollingDice}
            onComplete={handleDiceAnimationComplete}
          />
        )}
      </div>
    </div>
  );
}