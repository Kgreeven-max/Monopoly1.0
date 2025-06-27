import { useState, useRef, useCallback } from 'react';

/**
 * Custom hook for animating player movement around the board
 * Provides smooth step-by-step movement animation using CSS transitions
 */
export const usePlayerAnimation = () => {
  const [isAnimating, setIsAnimating] = useState(false);
  const [animatingPlayer, setAnimatingPlayer] = useState(null);
  const animationTimeouts = useRef(new Set());
  const playerPositions = useRef(new Map());

  // Clear all animation timeouts
  const clearAnimationTimeouts = useCallback(() => {
    animationTimeouts.current.forEach(timeout => clearTimeout(timeout));
    animationTimeouts.current.clear();
  }, []);

  // Calculate board positions for each space (0-39)
  const calculateBoardPositions = useCallback(() => {
    const positions = [];
    const boardSize = 600; // Standard board size
    const spaceSize = boardSize / 10; // 10 spaces per side
    
    for (let i = 0; i < 40; i++) {
      let x, y;
      const side = Math.floor(i / 10);
      const offset = i % 10;

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
      positions.push({ 
        x: x + spaceSize / 2, 
        y: y + spaceSize / 2 
      });
    }

    return positions;
  }, []);

  // Animate player movement from one position to another
  const animatePlayerMovement = useCallback((playerId, fromPosition, toPosition, steps, onComplete) => {
    return new Promise((resolve, reject) => {
      console.log(`[Animation] Starting movement for player ${playerId} from ${fromPosition} to ${toPosition} (${steps} steps)`);
      
      // Prevent concurrent animations for the same player
      if (isAnimating && animatingPlayer === playerId) {
        console.warn(`Player ${playerId} is already animating, skipping`);
        return reject(new Error('Player already animating'));
      }

      // Clear any existing timeouts
      clearAnimationTimeouts();

      setIsAnimating(true);
      setAnimatingPlayer(playerId);

      const boardPositions = calculateBoardPositions();
      const playerElement = document.querySelector(`[data-player-id="${playerId}"]`);
      
      if (!playerElement) {
        console.error(`No element found for player ${playerId}`);
        setIsAnimating(false);
        setAnimatingPlayer(null);
        return reject(new Error('Player element not found'));
      }

      // Calculate the path the player should take
      const path = [];
      let currentPos = fromPosition;
      
      for (let i = 0; i < steps; i++) {
        currentPos = (currentPos + 1) % 40; // Wrap around the board
        path.push(currentPos);
      }

      console.log(`[Animation] Movement path: ${path.join(' → ')}`);

      // Store initial position
      playerPositions.set(playerId, fromPosition);

      // Animate each step with a delay
      let stepIndex = 0;
      const animateStep = () => {
        if (stepIndex >= path.length) {
          // Animation complete
          console.log(`[Animation] Movement complete for player ${playerId}`);
          setIsAnimating(false);
          setAnimatingPlayer(null);
          playerPositions.set(playerId, toPosition);
          
          if (onComplete) {
            onComplete(toPosition);
          }
          
          resolve(toPosition);
          return;
        }

        const targetPosition = path[stepIndex];
        const targetCoords = boardPositions[targetPosition];
        
        console.log(`[Animation] Step ${stepIndex + 1}/${path.length}: Moving to position ${targetPosition} (${targetCoords.x}, ${targetCoords.y})`);

        // Update the player element position with smooth transition
        playerElement.style.transition = 'transform 0.3s ease-in-out';
        playerElement.style.transform = `translate(${targetCoords.x}px, ${targetCoords.y}px)`;

        // Store current position
        playerPositions.set(playerId, targetPosition);

        stepIndex++;
        
        // Schedule next step
        const timeout = setTimeout(animateStep, 350); // 350ms between steps
        animationTimeouts.current.add(timeout);
      };

      // Start the animation
      animateStep();

      // Safety timeout to prevent infinite animation
      const safetyTimeout = setTimeout(() => {
        console.warn(`[Animation] Safety timeout reached for player ${playerId}`);
        clearAnimationTimeouts();
        setIsAnimating(false);
        setAnimatingPlayer(null);
        playerPositions.set(playerId, toPosition);
        reject(new Error('Animation timeout'));
      }, steps * 500 + 5000); // Allow 500ms per step plus 5s buffer
      
      animationTimeouts.current.add(safetyTimeout);
    });
  }, [isAnimating, animatingPlayer, calculateBoardPositions, clearAnimationTimeouts]);

  // Get current animated position for a player
  const getPlayerPosition = useCallback((playerId) => {
    return playerPositions.get(playerId);
  }, []);

  // Stop animation for a specific player
  const stopPlayerAnimation = useCallback((playerId) => {
    if (animatingPlayer === playerId) {
      console.log(`[Animation] Stopping animation for player ${playerId}`);
      clearAnimationTimeouts();
      setIsAnimating(false);
      setAnimatingPlayer(null);
    }
  }, [animatingPlayer, clearAnimationTimeouts]);

  // Stop all animations
  const stopAllAnimations = useCallback(() => {
    console.log('[Animation] Stopping all animations');
    clearAnimationTimeouts();
    setIsAnimating(false);
    setAnimatingPlayer(null);
  }, [clearAnimationTimeouts]);

  return {
    isAnimating,
    animatingPlayer,
    animatePlayerMovement,
    getPlayerPosition,
    stopPlayerAnimation,
    stopAllAnimations,
    calculateBoardPositions
  };
};

export default usePlayerAnimation;