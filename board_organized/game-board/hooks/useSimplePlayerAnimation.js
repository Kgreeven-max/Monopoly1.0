import { useState, useRef, useCallback } from 'react';

/**
 * Simplified animation hook that integrates with existing GameContext
 * No complex queue system - just smooth CSS-based transitions
 */
export const useSimplePlayerAnimation = () => {
  const [isAnimating, setIsAnimating] = useState(false);
  const [animatingPlayer, setAnimatingPlayer] = useState(null);
  const animationTimeouts = useRef(new Set());

  // Clear all animation timeouts
  const clearAnimationTimeouts = useCallback(() => {
    animationTimeouts.current.forEach(timeout => clearTimeout(timeout));
    animationTimeouts.current.clear();
  }, []);

  // Simple step-by-step animation using CSS transitions
  const animatePlayerMovement = useCallback((playerId, fromPosition, toPosition, steps, onComplete) => {
    return new Promise((resolve, reject) => {
      console.log(`[SimpleAnimation] Starting movement for player ${playerId} from ${fromPosition} to ${toPosition} (${steps} steps)`);
      
      // Prevent concurrent animations for the same player
      if (isAnimating && animatingPlayer === playerId) {
        console.warn(`Player ${playerId} is already animating, skipping`);
        return reject(new Error('Player already animating'));
      }

      // Find the player element
      const playerElement = document.querySelector(`[data-player-id="${playerId}"]`);
      
      if (!playerElement) {
        console.error(`No element found for player ${playerId}`);
        return reject(new Error('Player element not found'));
      }

      // Calculate the path the player should take
      const path = [];
      let currentPos = fromPosition;
      
      for (let i = 0; i < steps; i++) {
        currentPos = (currentPos + 1) % 40; // Wrap around the board
        path.push(currentPos);
      }

      console.log(`[SimpleAnimation] Movement path: ${path.join(' → ')}`);

      setIsAnimating(true);
      setAnimatingPlayer(playerId);

      // Add animation class for visual feedback
      playerElement.classList.add('animating');

      // Animate each step with a delay
      let stepIndex = 0;
      const animateStep = () => {
        if (stepIndex >= path.length) {
          // Animation complete
          console.log(`[SimpleAnimation] Movement complete for player ${playerId}`);
          
          // Remove animation class
          playerElement.classList.remove('animating');
          
          setIsAnimating(false);
          setAnimatingPlayer(null);
          
          if (onComplete) {
            onComplete(toPosition);
          }
          
          resolve(toPosition);
          return;
        }

        const targetPosition = path[stepIndex];
        
        console.log(`[SimpleAnimation] Step ${stepIndex + 1}/${path.length}: Moving to position ${targetPosition}`);

        // Update the data attribute so the position calculation updates
        playerElement.dataset.currentPosition = targetPosition.toString();
        
        // Trigger a re-render by dispatching a custom event
        const event = new CustomEvent('playerPositionUpdate', {
          detail: { playerId, position: targetPosition }
        });
        document.dispatchEvent(event);

        stepIndex++;
        
        // Schedule next step
        const timeout = setTimeout(animateStep, 300); // 300ms between steps
        animationTimeouts.current.add(timeout);
      };

      // Start the animation
      animateStep();

      // Safety timeout to prevent infinite animation
      const safetyTimeout = setTimeout(() => {
        console.warn(`[SimpleAnimation] Safety timeout reached for player ${playerId}`);
        clearAnimationTimeouts();
        playerElement.classList.remove('animating');
        setIsAnimating(false);
        setAnimatingPlayer(null);
        reject(new Error('Animation timeout'));
      }, steps * 500 + 5000); // Allow 500ms per step plus 5s buffer
      
      animationTimeouts.current.add(safetyTimeout);
    });
  }, [isAnimating, animatingPlayer, clearAnimationTimeouts]);

  // Stop animation for a specific player
  const stopPlayerAnimation = useCallback((playerId) => {
    if (animatingPlayer === playerId) {
      console.log(`[SimpleAnimation] Stopping animation for player ${playerId}`);
      clearAnimationTimeouts();
      
      // Remove animation class
      const playerElement = document.querySelector(`[data-player-id="${playerId}"]`);
      if (playerElement) {
        playerElement.classList.remove('animating');
      }
      
      setIsAnimating(false);
      setAnimatingPlayer(null);
    }
  }, [animatingPlayer, clearAnimationTimeouts]);

  // Stop all animations
  const stopAllAnimations = useCallback(() => {
    console.log('[SimpleAnimation] Stopping all animations');
    clearAnimationTimeouts();
    
    // Remove animation class from all players
    const playerElements = document.querySelectorAll('[data-player-id]');
    playerElements.forEach(el => el.classList.remove('animating'));
    
    setIsAnimating(false);
    setAnimatingPlayer(null);
  }, [clearAnimationTimeouts]);

  return {
    isAnimating,
    animatingPlayer,
    animatePlayerMovement,
    stopPlayerAnimation,
    stopAllAnimations
  };
};

export default useSimplePlayerAnimation;