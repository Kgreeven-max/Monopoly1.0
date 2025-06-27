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
  const [playerPositions, setPlayerPositions] = useState(new Map());
  const [lastNotificationId, setLastNotificationId] = useState(null);

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

  // Listen for dice roll events from GameContext notifications
  useEffect(() => {
    if (state.notifications && state.notifications.length > 0) {
      const latestNotification = state.notifications[0];
      
      // Avoid processing the same notification twice
      if (latestNotification !== lastNotificationId) {
        setLastNotificationId(latestNotification);
        
        // Check if it's a dice roll notification
        if (latestNotification.message && latestNotification.message.includes('rolled')) {
          console.log('[SmartGameBoard] Dice roll detected from notification:', latestNotification.message);
          
          // Try to extract dice values from the message
          const diceMatch = latestNotification.message.match(/rolled (\d+) and (\d+)/);
          if (diceMatch) {
            const roll = [parseInt(diceMatch[1]), parseInt(diceMatch[2])];
            console.log('[SmartGameBoard] Extracted dice values:', roll);
            
            setDiceRoll(roll);
            setShowDiceAnimation(true);
            setIsRollingDice(true);
          }
        }
        
        // Check if it's a movement notification
        if (latestNotification.message && latestNotification.message.includes('moved to position')) {
          console.log('[SmartGameBoard] Movement detected from notification:', latestNotification.message);
          
          // Extract player info and position from the message
          const moveMatch = latestNotification.message.match(/(.+) moved to position (\d+)/);
          if (moveMatch) {
            const playerName = moveMatch[1];
            const newPosition = parseInt(moveMatch[2]);
            
            // Find the player by name
            const player = state.players?.find(p => 
              p.name === playerName || 
              p.username === playerName || 
              `Player ${p.id}` === playerName
            );
            
            if (player) {
              const currentPos = playerPositions.get(player.id) ?? player.position ?? 0;
              
              if (currentPos !== newPosition && !isAnimating) {
                // Calculate movement steps
                let steps;
                if (newPosition > currentPos) {
                  steps = newPosition - currentPos;
                } else if (newPosition < currentPos) {
                  // Wrapped around the board
                  steps = (40 - currentPos) + newPosition;
                } else {
                  steps = 0;
                }

                // Only animate reasonable movements
                if (steps > 0 && steps <= 12) {
                  console.log(`[SmartGameBoard] Animating real game movement: Player ${player.id} from ${currentPos} to ${newPosition} (${steps} steps)`);
                  
                  animatePlayerMovement(
                    player.id,
                    currentPos,
                    newPosition,
                    steps,
                    (finalPosition) => {
                      console.log(`[SmartGameBoard] Real game animation completed for player ${player.id} at position ${finalPosition}`);
                      setPlayerPositions(prev => new Map(prev).set(player.id, finalPosition));
                    }
                  ).catch(error => {
                    console.error(`[SmartGameBoard] Real game animation failed for player ${player.id}:`, error);
                    setPlayerPositions(prev => new Map(prev).set(player.id, newPosition));
                  });
                } else {
                  // Update position without animation
                  setPlayerPositions(prev => new Map(prev).set(player.id, newPosition));
                }
              }
            }
          }
        }
      }
    }
  }, [state.notifications, lastNotificationId, playerPositions, animatePlayerMovement, isAnimating, state.players]);

  // Also listen directly to player position changes (backup method)
  useEffect(() => {
    if (state.players && state.players.length > 0) {
      state.players.forEach(player => {
        const currentGamePos = player.position || 0;
        const lastKnownPos = playerPositions.get(player.id);

        // Only update if we haven't seen this player before
        if (lastKnownPos === undefined) {
          setPlayerPositions(prev => new Map(prev).set(player.id, currentGamePos));
        }
      });
    }
  }, [state.players, playerPositions]);

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
      
      console.log(`[SmartGameBoard] Testing movement for player ${testPlayer.id}: ${currentPos} → ${newPos}`);
      
      animatePlayerMovement(
        testPlayer.id,
        currentPos,
        newPos,
        steps,
        (finalPosition) => {
          console.log(`[SmartGameBoard] Test animation completed at position ${finalPosition}`);
          setPlayerPositions(prev => new Map(prev).set(testPlayer.id, finalPosition));
        }
      ).catch(error => {
        console.error('[SmartGameBoard] Test animation failed:', error);
      });
    }
  }, [state.players, playerPositions, animatePlayerMovement]);

  const testDiceRoll = useCallback(() => {
    const roll = [Math.floor(Math.random() * 6) + 1, Math.floor(Math.random() * 6) + 1];
    console.log(`[SmartGameBoard] Testing dice roll:`, roll);
    
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

            {/* Real-time debug info */}
            <div style={{ fontSize: '10px', marginTop: '8px', opacity: 0.7 }}>
              <div>Notifications: {state.notifications?.length || 0}</div>
              <div>Animated Positions: {playerPositions.size}</div>
              {state.notifications && state.notifications.length > 0 && (
                <div style={{ marginTop: '4px', maxWidth: '200px', wordWrap: 'break-word' }}>
                  Latest: {state.notifications[0]?.message?.substring(0, 50)}...
                </div>
              )}
            </div>
          </div>

          {/* Debug Controls */}
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