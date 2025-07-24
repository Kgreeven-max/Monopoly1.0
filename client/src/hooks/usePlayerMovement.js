import { useRef, useCallback } from 'react';
import { boardPositionCache } from '../utils/BoardPositionCache';

/**
 * Hook for smooth player movement animations using requestAnimationFrame
 */
export const usePlayerMovement = ({
  updateVisualPosition,
  updateLogicalPosition,
  getAnimationState,
  setAnimationState,
  onMovementComplete
}) => {
  const animationFrameIds = useRef(new Map());

  /**
   * Easing function for smooth movement
   */
  const easeInOutQuad = (t) => {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  };

  /**
   * Cancel any ongoing animation for a player
   */
  const cancelAnimation = useCallback((playerId) => {
    const frameId = animationFrameIds.current.get(playerId);
    if (frameId) {
      cancelAnimationFrame(frameId);
      animationFrameIds.current.delete(playerId);
    }
    setAnimationState(playerId, null);
  }, [setAnimationState]);

  /**
   * Animate player movement along a path
   */
  const animateMovement = useCallback((playerId, fromPosition, toPosition, steps, options = {}) => {
    const {
      duration = 300 * steps, // 300ms per space
      bounceHeight = 15,
      onStepComplete,
      onComplete
    } = options;

    console.log(`[Animation] Starting movement for player ${playerId}: ${fromPosition} → ${toPosition} (${steps} steps)`);

    // Cancel any existing animation
    cancelAnimation(playerId);

    // Get the movement path
    const path = boardPositionCache.getMovementPath(fromPosition, toPosition, steps);
    
    // Animation state
    const animState = {
      playerId,
      startTime: performance.now(),
      duration,
      currentStep: 0,
      path,
      fromPosition,
      toPosition,
      totalSteps: steps
    };

    setAnimationState(playerId, animState);

    // Animation loop
    const animate = (currentTime) => {
      const state = getAnimationState(playerId);
      if (!state) return;

      const elapsed = currentTime - state.startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Calculate which step we're on
      const stepProgress = progress * steps;
      const currentStep = Math.floor(stepProgress);
      const stepFraction = stepProgress - currentStep;

      // Handle step completion callbacks
      if (currentStep > state.currentStep) {
        state.currentStep = currentStep;
        if (onStepComplete) {
          onStepComplete(currentStep);
        }
      }

      // Calculate position between current and next step
      if (currentStep < path.length - 1) {
        const currentPos = path[currentStep];
        const nextPos = path[currentStep + 1];
        
        // Interpolate position with easing
        const easedFraction = easeInOutQuad(stepFraction);
        const x = currentPos.x + (nextPos.x - currentPos.x) * easedFraction;
        const y = currentPos.y + (nextPos.y - currentPos.y) * easedFraction;
        
        // Add bounce effect
        const bounceProgress = Math.sin(stepFraction * Math.PI);
        const bounceOffset = bounceHeight * bounceProgress;
        
        updateVisualPosition(playerId, { 
          x, 
          y: y - bounceOffset // Subtract to move up
        });
      }

      // Continue or complete animation
      if (progress < 1) {
        const frameId = requestAnimationFrame(animate);
        animationFrameIds.current.set(playerId, frameId);
      } else {
        // Animation complete
        console.log(`[Animation] Completed movement for player ${playerId}`);
        
        // Ensure final position is exact
        const finalPos = path[path.length - 1];
        updateVisualPosition(playerId, finalPos);
        updateLogicalPosition(playerId, toPosition);
        
        // Clean up
        animationFrameIds.current.delete(playerId);
        setAnimationState(playerId, null);
        
        // Callbacks
        if (onComplete) {
          onComplete();
        }
        if (onMovementComplete) {
          onMovementComplete(playerId, toPosition);
        }
      }
    };

    // Start animation
    const frameId = requestAnimationFrame(animate);
    animationFrameIds.current.set(playerId, frameId);

    // Return a promise that resolves when animation completes
    return new Promise((resolve) => {
      const checkComplete = () => {
        if (!getAnimationState(playerId)) {
          resolve();
        } else {
          setTimeout(checkComplete, 50);
        }
      };
      checkComplete();
    });
  }, [
    cancelAnimation,
    getAnimationState,
    setAnimationState,
    updateVisualPosition,
    updateLogicalPosition,
    onMovementComplete
  ]);

  /**
   * Move a player instantly without animation
   */
  const moveInstantly = useCallback((playerId, toPosition) => {
    cancelAnimation(playerId);
    
    const visualPos = boardPositionCache.getSpacePosition(toPosition);
    updateVisualPosition(playerId, visualPos);
    updateLogicalPosition(playerId, toPosition);
    
    if (onMovementComplete) {
      onMovementComplete(playerId, toPosition);
    }
  }, [
    cancelAnimation,
    updateVisualPosition,
    updateLogicalPosition,
    onMovementComplete
  ]);

  /**
   * Check if any player is currently animating
   */
  const isAnyPlayerAnimating = useCallback(() => {
    return animationFrameIds.current.size > 0;
  }, []);

  /**
   * Cancel all ongoing animations
   */
  const cancelAllAnimations = useCallback(() => {
    animationFrameIds.current.forEach((frameId, playerId) => {
      cancelAnimationFrame(frameId);
      setAnimationState(playerId, null);
    });
    animationFrameIds.current.clear();
  }, [setAnimationState]);

  return {
    animateMovement,
    moveInstantly,
    cancelAnimation,
    cancelAllAnimations,
    isAnyPlayerAnimating
  };
};