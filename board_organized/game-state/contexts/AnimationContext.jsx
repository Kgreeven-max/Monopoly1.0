import React, { createContext, useContext, useRef, useCallback, useState } from 'react';
import usePlayerAnimation from '../../game-board/hooks/usePlayerAnimation';

const AnimationContext = createContext();

export const useAnimation = () => {
  const context = useContext(AnimationContext);
  if (!context) {
    throw new Error('useAnimation must be used within an AnimationProvider');
  }
  return context;
};

export const AnimationProvider = ({ children }) => {
  const [pendingAnimations, setPendingAnimations] = useState(new Map());
  const [animationQueue, setAnimationQueue] = useState([]);
  const [isProcessingQueue, setIsProcessingQueue] = useState(false);
  
  const {
    isAnimating,
    animatingPlayer,
    animatePlayerMovement,
    getPlayerPosition,
    stopPlayerAnimation,
    stopAllAnimations,
    calculateBoardPositions
  } = usePlayerAnimation();

  // Queue an animation to be processed
  const queueAnimation = useCallback((animationType, data) => {
    const animationId = `${animationType}-${Date.now()}-${Math.random()}`;
    
    const animation = {
      id: animationId,
      type: animationType,
      data,
      timestamp: Date.now()
    };

    console.log(`[AnimationContext] Queuing animation:`, animation);
    
    setAnimationQueue(prev => [...prev, animation]);
    
    return animationId;
  }, []);

  // Process the animation queue
  const processAnimationQueue = useCallback(async () => {
    if (isProcessingQueue || animationQueue.length === 0) {
      return;
    }

    setIsProcessingQueue(true);
    
    while (animationQueue.length > 0) {
      const animation = animationQueue[0];
      
      try {
        console.log(`[AnimationContext] Processing animation:`, animation);
        
        switch (animation.type) {
          case 'player_movement':
            const { playerId, fromPosition, toPosition, steps } = animation.data;
            
            await animatePlayerMovement(
              playerId,
              fromPosition,
              toPosition,
              steps,
              (finalPosition) => {
                console.log(`[AnimationContext] Player ${playerId} movement completed at position ${finalPosition}`);
              }
            );
            break;
            
          case 'dice_roll':
            const { diceValues, duration = 2000 } = animation.data;
            
            // Simulate dice roll animation delay
            await new Promise(resolve => setTimeout(resolve, duration));
            break;
            
          default:
            console.warn(`[AnimationContext] Unknown animation type: ${animation.type}`);
        }
        
        // Remove completed animation from queue
        setAnimationQueue(prev => prev.slice(1));
        
      } catch (error) {
        console.error(`[AnimationContext] Animation failed:`, error);
        // Remove failed animation from queue and continue
        setAnimationQueue(prev => prev.slice(1));
      }
    }
    
    setIsProcessingQueue(false);
  }, [animationQueue, isProcessingQueue, animatePlayerMovement]);

  // Start processing queue when animations are added
  React.useEffect(() => {
    if (animationQueue.length > 0 && !isProcessingQueue) {
      processAnimationQueue();
    }
  }, [animationQueue, isProcessingQueue, processAnimationQueue]);

  // Queue a player movement animation
  const queuePlayerMovement = useCallback((playerId, fromPosition, toPosition, steps) => {
    return queueAnimation('player_movement', {
      playerId,
      fromPosition,
      toPosition,
      steps
    });
  }, [queueAnimation]);

  // Queue a dice roll animation
  const queueDiceRoll = useCallback((diceValues, duration) => {
    return queueAnimation('dice_roll', {
      diceValues,
      duration
    });
  }, [queueAnimation]);

  // Handle coordinated dice roll + movement sequence
  const animateTurnSequence = useCallback(async (playerId, diceValues, fromPosition, toPosition) => {
    try {
      console.log(`[AnimationContext] Starting turn sequence for player ${playerId}`);
      
      // Calculate steps based on dice total
      const steps = diceValues[0] + diceValues[1];
      
      // First, queue and wait for dice animation
      const diceAnimationId = queueDiceRoll(diceValues, 1500);
      
      // Then queue player movement
      const movementAnimationId = queuePlayerMovement(playerId, fromPosition, toPosition, steps);
      
      console.log(`[AnimationContext] Queued turn sequence: dice=${diceAnimationId}, movement=${movementAnimationId}`);
      
      return { diceAnimationId, movementAnimationId };
      
    } catch (error) {
      console.error(`[AnimationContext] Turn sequence failed:`, error);
      throw error;
    }
  }, [queueDiceRoll, queuePlayerMovement]);

  // Get current animation status
  const getAnimationStatus = useCallback(() => {
    return {
      isAnimating,
      animatingPlayer,
      queueLength: animationQueue.length,
      isProcessingQueue,
      pendingAnimationsCount: pendingAnimations.size
    };
  }, [isAnimating, animatingPlayer, animationQueue.length, isProcessingQueue, pendingAnimations.size]);

  // Clear all animations and queues
  const clearAllAnimations = useCallback(() => {
    console.log('[AnimationContext] Clearing all animations');
    stopAllAnimations();
    setAnimationQueue([]);
    setPendingAnimations(new Map());
    setIsProcessingQueue(false);
  }, [stopAllAnimations]);

  const value = {
    // Animation state
    isAnimating,
    animatingPlayer,
    animationQueue,
    isProcessingQueue,
    
    // Core animation functions
    animatePlayerMovement,
    queuePlayerMovement,
    queueDiceRoll,
    animateTurnSequence,
    
    // Utility functions
    getPlayerPosition,
    getAnimationStatus,
    calculateBoardPositions,
    
    // Control functions
    stopPlayerAnimation,
    stopAllAnimations,
    clearAllAnimations
  };

  return (
    <AnimationContext.Provider value={value}>
      {children}
    </AnimationContext.Provider>
  );
};