import React, { useState, useEffect, useRef } from 'react';
import { Box, Tooltip, Typography } from '@mui/material';
import './AnimatedPlayerToken.css';

// Constants for board layout
const BOARD_SPACES = 40;
const SPACES_PER_SIDE = 10;

// Player colors matching the main board
const PLAYER_COLORS = ['#E53935', '#1E88E5', '#43A047', '#FDD835', '#8E24AA', '#FB8C00', '#26A69A', '#EC407A'];

/**
 * Calculates the absolute X,Y position for a given board space
 * @param {number} spaceIndex - The board space index (0-39)
 * @param {number} boardSize - The size of the board in pixels
 * @returns {{x: number, y: number}} The x,y coordinates for the token
 */
const calculateBoardPosition = (spaceIndex, boardSize = 900) => {
  const cornerSize = boardSize / 11; // Corner spaces are larger
  const edgeSize = (boardSize - 2 * cornerSize) / 9; // 9 edge spaces per side
  
  // Helper to get position along an edge
  const getEdgePosition = (index, total) => {
    return cornerSize + (index * edgeSize) + (edgeSize / 2);
  };
  
  if (spaceIndex === 0) {
    // GO corner (bottom-right)
    return { x: boardSize - cornerSize / 2, y: boardSize - cornerSize / 2 };
  } else if (spaceIndex <= 9) {
    // Bottom edge (moving left)
    const pos = 9 - spaceIndex; // Reverse for left movement
    return { x: getEdgePosition(pos, 9), y: boardSize - cornerSize / 2 };
  } else if (spaceIndex === 10) {
    // Jail corner (bottom-left) - handle "Just Visiting" vs "In Jail"
    return { x: cornerSize / 2, y: boardSize - cornerSize / 2 };
  } else if (spaceIndex <= 19) {
    // Left edge (moving up)
    const pos = 19 - spaceIndex;
    return { x: cornerSize / 2, y: getEdgePosition(pos, 9) };
  } else if (spaceIndex === 20) {
    // Free Parking corner (top-left)
    return { x: cornerSize / 2, y: cornerSize / 2 };
  } else if (spaceIndex <= 29) {
    // Top edge (moving right)
    const pos = spaceIndex - 21;
    return { x: getEdgePosition(pos, 9), y: cornerSize / 2 };
  } else if (spaceIndex === 30) {
    // Go to Jail corner (top-right)
    return { x: boardSize - cornerSize / 2, y: cornerSize / 2 };
  } else if (spaceIndex <= 39) {
    // Right edge (moving down)
    const pos = spaceIndex - 31;
    return { x: boardSize - cornerSize / 2, y: getEdgePosition(pos, 9) };
  }
  
  // Fallback (should never happen)
  return { x: boardSize / 2, y: boardSize / 2 };
};

/**
 * Calculates the path from one position to another
 * @param {number} fromPos - Starting position
 * @param {number} toPos - Ending position
 * @returns {number[]} Array of positions to animate through
 */
const calculateMovementPath = (fromPos, toPos) => {
  const path = [];
  let currentPos = fromPos;
  
  // Handle forward movement (including passing GO)
  while (currentPos !== toPos) {
    currentPos = (currentPos + 1) % BOARD_SPACES;
    path.push(currentPos);
  }
  
  return path;
};

/**
 * AnimatedPlayerToken Component
 * Handles smooth animation of player tokens around the board
 */
const AnimatedPlayerToken = ({ 
  player, 
  boardSize = 900,
  isCurrentPlayer = false,
  playerIndex = 0,
  otherPlayersOnSpace = [],
  enableSound = true
}) => {
  const [currentPosition, setCurrentPosition] = useState(player.position);
  const [isAnimating, setIsAnimating] = useState(false);
  const [bouncing, setBouncing] = useState(false);
  const [coordinates, setCoordinates] = useState(() => 
    calculateBoardPosition(player.position, boardSize)
  );
  const animationQueueRef = useRef([]);
  const previousPositionRef = useRef(player.position);
  const isAnimatingRef = useRef(false);

  // Handle position changes with animation
  useEffect(() => {
    if (player.position !== previousPositionRef.current && !isAnimatingRef.current) {
      console.log(`[AnimatedPlayerToken] Player ${player.id} moving from ${previousPositionRef.current} to ${player.position}`);
      
      // Calculate the path
      const path = calculateMovementPath(previousPositionRef.current, player.position);
      console.log(`[AnimatedPlayerToken] Movement path:`, path);
      
      // Queue the animation
      animationQueueRef.current = path;
      previousPositionRef.current = player.position;
      
      // Start animation
      animateMovement();
    }
  }, [player.position]);

  // Animate through each space in the path
  const animateMovement = async () => {
    if (animationQueueRef.current.length === 0) {
      return;
    }
    
    console.log(`[AnimatedPlayerToken] Starting animation for ${animationQueueRef.current.length} moves`);
    setIsAnimating(true);
    isAnimatingRef.current = true;
    
    // Process each position in the queue with bounce effect
    for (let i = 0; i < animationQueueRef.current.length; i++) {
      const nextPos = animationQueueRef.current[i];
      const coords = calculateBoardPosition(nextPos, boardSize);
      const isLastMove = i === animationQueueRef.current.length - 1;
      
      console.log(`[AnimatedPlayerToken] Moving to position ${nextPos} (${i + 1}/${animationQueueRef.current.length})`);
      
      setCurrentPosition(nextPos);
      setCoordinates(coords);
      
      // Trigger bounce animation for each move
      setBouncing(true);
      
      // Wait for bounce animation (increased time for visibility)
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Stop bouncing before next move
      setBouncing(false);
      
      // Pause between hops (increased for visibility)
      if (!isLastMove) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
    }
    
    // Clear the queue after animation
    animationQueueRef.current = [];
    setIsAnimating(false);
    isAnimatingRef.current = false;
    console.log(`[AnimatedPlayerToken] Animation complete`);
  };

  // Handle board resize
  useEffect(() => {
    const coords = calculateBoardPosition(currentPosition, boardSize);
    setCoordinates(coords);
  }, [boardSize, currentPosition]);

  // Calculate stacking offset for multiple players on same space
  const stackingOffset = otherPlayersOnSpace.indexOf(player.id);
  const offsetX = stackingOffset * 10; // Horizontal offset for visibility
  const offsetY = stackingOffset * -10; // Vertical offset for visibility

  const tokenStyle = {
    left: `${coordinates.x + offsetX}px`,
    top: `${coordinates.y + offsetY}px`,
    transform: 'translate(-50%, -50%)', // Center the token on the coordinates
    backgroundColor: PLAYER_COLORS[playerIndex % PLAYER_COLORS.length],
    zIndex: 100 + playerIndex + (isCurrentPlayer ? 50 : 0) + (isAnimating ? 100 : 0),
  };

  return (
    <Tooltip 
      title={
        <Box>
          <Typography variant="caption">
            {player.username || `Player ${player.id}`}
            {player.is_bot && ' (Bot)'}
          </Typography>
          <Typography variant="caption" display="block">
            Money: ${player.money || 0}
          </Typography>
          {player.in_jail && (
            <Typography variant="caption" display="block" color="error">
              In Jail
            </Typography>
          )}
        </Box>
      }
      arrow
    >
      <Box
        className={`animated-player-token ${isCurrentPlayer ? 'current-player' : ''} ${isAnimating ? 'animating' : ''} ${bouncing ? 'bouncing' : ''}`}
        style={tokenStyle}
        data-player-id={player.id}
        data-position={currentPosition}
      >
        <Typography className="token-label">
          {player.id}
        </Typography>
        {player.in_jail && (
          <Box className="jail-indicator" />
        )}
        {player.has_outstanding_loans && (
          <Box className="debt-indicator" />
        )}
      </Box>
    </Tooltip>
  );
};

export default AnimatedPlayerToken;