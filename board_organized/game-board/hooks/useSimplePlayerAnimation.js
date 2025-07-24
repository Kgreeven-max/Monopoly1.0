import { useState, useRef, useCallback } from 'react';

/**
 * Simple animation hook that handles timing for step-by-step player movement
 * Follows the WARS game pattern: 300ms per space with bounce animation
 */
export const useSimplePlayerAnimation = () => {
  const [isAnimating, setIsAnimating] = useState(false);
  const [animatingPlayer, setAnimatingPlayer] = useState(null);
  const animationInterval = useRef(null);
  const animationTimeouts = useRef(new Set());

  // Clear all animation timeouts and intervals
  const clearAllTimers = useCallback(() => {
    if (animationInterval.current) {
      clearInterval(animationInterval.current);
      animationInterval.current = null;
    }
    animationTimeouts.current.forEach(timeout => clearTimeout(timeout));
    animationTimeouts.current.clear();
  }, []);

  // Animate player movement step by step
  const animatePlayerMovement = useCallback((playerId, fromPosition, toPosition, steps, onComplete, onStep) => {
    return new Promise((resolve, reject) => {
      console.log(`[Animation] Starting movement for player ${playerId} from ${fromPosition} to ${toPosition} (${steps} steps)`);
      
      // Prevent concurrent animations
      if (isAnimating) {
        console.warn(`Animation already in progress, skipping player ${playerId}`);
        return reject(new Error('Animation already in progress'));
      }

      // Validate inputs
      if (steps <= 0 || steps > 40) {
        console.error(`Invalid steps: ${steps}`);
        return reject(new Error('Invalid number of steps'));
      }

      setIsAnimating(true);
      setAnimatingPlayer(playerId);

      let currentPos = fromPosition;
      let moveCount = 0;

      // Move one space at a time with 300ms interval
      animationInterval.current = setInterval(() => {
        if (moveCount < steps) {
          // Calculate next position (wrap around board)
          currentPos = (currentPos + 1) % 40;
          moveCount++;

          console.log(`[Animation] Step ${moveCount}/${steps}: Player ${playerId} at position ${currentPos}`);

          // Call the step callback to update position
          if (onStep) {
            onStep(currentPos, moveCount);
          }

          // Find and animate the player token element
          const tokenElement = document.querySelector(`[data-player-id="${playerId}"]`);
          if (tokenElement) {
            // Add bounce class
            tokenElement.classList.add('bouncing');
            
            // Remove bounce class after 250ms (before next step)
            const bounceTimeout = setTimeout(() => {
              tokenElement.classList.remove('bouncing');
            }, 250);
            animationTimeouts.current.add(bounceTimeout);
          }
        } else {
          // Animation complete
          clearAllTimers();
          
          console.log(`[Animation] Movement complete for player ${playerId} at position ${toPosition}`);
          
          setIsAnimating(false);
          setAnimatingPlayer(null);
          
          if (onComplete) {
            onComplete(toPosition);
          }
          
          resolve(toPosition);
        }
      }, 300); // 300ms per space (matching WARS game)

      // Safety timeout to prevent infinite animation
      const safetyTimeout = setTimeout(() => {
        console.error(`[Animation] Safety timeout reached for player ${playerId}`);
        clearAllTimers();
        setIsAnimating(false);
        setAnimatingPlayer(null);
        reject(new Error('Animation timeout'));
      }, (steps * 300) + 2000); // Allow time for all steps plus 2s buffer
      
      animationTimeouts.current.add(safetyTimeout);
    });
  }, [isAnimating, clearAllTimers]);

  // Stop all animations
  const stopAllAnimations = useCallback(() => {
    console.log('[Animation] Stopping all animations');
    clearAllTimers();
    
    // Remove bounce class from any player that might have it
    document.querySelectorAll('.player-token.bouncing').forEach(el => {
      el.classList.remove('bouncing');
    });
    
    setIsAnimating(false);
    setAnimatingPlayer(null);
  }, [clearAllTimers]);

  return {
    isAnimating,
    animatingPlayer,
    animatePlayerMovement,
    stopAllAnimations
  };
};

export default useSimplePlayerAnimation;