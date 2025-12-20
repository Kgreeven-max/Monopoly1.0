import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

/**
 * Animation Context - Handles UI animations SEPARATELY from game state
 *
 * Key Principle: Animation events trigger visual effects only.
 * They do NOT update game state. GAME_STATE is the single source of truth.
 */

interface AnimationState {
  // Dice animation
  diceRolling: boolean;
  diceValues: [number, number] | null;

  // Player movement animation
  playerMoving: string | null;
  moveFrom: number | null;
  moveTo: number | null;
  moveSpaces: number | null;

  // Card animation
  cardRevealing: boolean;
  cardId: string | null;
  cardDeck: 'chance' | 'community_chest' | null;
}

interface AnimationContextType extends AnimationState {
  // Dice animations
  startDiceRoll: () => void;
  showDiceResult: (dice: [number, number]) => void;
  clearDiceAnimation: () => void;

  // Movement animations
  startPlayerMove: (playerId: string, from: number, to: number, spaces: number) => void;
  clearMoveAnimation: () => void;

  // Card animations
  startCardReveal: (cardId: string, deck: 'chance' | 'community_chest') => void;
  clearCardAnimation: () => void;

  // Clear all
  clearAllAnimations: () => void;
}

const initialState: AnimationState = {
  diceRolling: false,
  diceValues: null,
  playerMoving: null,
  moveFrom: null,
  moveTo: null,
  moveSpaces: null,
  cardRevealing: false,
  cardId: null,
  cardDeck: null,
};

const AnimationContext = createContext<AnimationContextType | null>(null);

export function AnimationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AnimationState>(initialState);

  // Dice animations
  const startDiceRoll = useCallback(() => {
    setState(prev => ({ ...prev, diceRolling: true, diceValues: null }));
  }, []);

  const showDiceResult = useCallback((dice: [number, number]) => {
    setState(prev => ({ ...prev, diceRolling: false, diceValues: dice }));

    // Auto-clear after animation completes
    setTimeout(() => {
      setState(prev => ({ ...prev, diceValues: null }));
    }, 2000);
  }, []);

  const clearDiceAnimation = useCallback(() => {
    setState(prev => ({ ...prev, diceRolling: false, diceValues: null }));
  }, []);

  // Movement animations
  const startPlayerMove = useCallback((playerId: string, from: number, to: number, spaces: number) => {
    setState(prev => ({
      ...prev,
      playerMoving: playerId,
      moveFrom: from,
      moveTo: to,
      moveSpaces: spaces,
    }));

    // Auto-clear after animation completes (adjust timing as needed)
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        playerMoving: null,
        moveFrom: null,
        moveTo: null,
        moveSpaces: null,
      }));
    }, 1500 + (spaces * 200)); // Base time + per-space time
  }, []);

  const clearMoveAnimation = useCallback(() => {
    setState(prev => ({
      ...prev,
      playerMoving: null,
      moveFrom: null,
      moveTo: null,
      moveSpaces: null,
    }));
  }, []);

  // Card animations
  const startCardReveal = useCallback((cardId: string, deck: 'chance' | 'community_chest') => {
    setState(prev => ({
      ...prev,
      cardRevealing: true,
      cardId,
      cardDeck: deck,
    }));

    // Auto-clear after animation
    setTimeout(() => {
      setState(prev => ({
        ...prev,
        cardRevealing: false,
        cardId: null,
        cardDeck: null,
      }));
    }, 3000);
  }, []);

  const clearCardAnimation = useCallback(() => {
    setState(prev => ({
      ...prev,
      cardRevealing: false,
      cardId: null,
      cardDeck: null,
    }));
  }, []);

  // Clear all
  const clearAllAnimations = useCallback(() => {
    setState(initialState);
  }, []);

  return (
    <AnimationContext.Provider
      value={{
        ...state,
        startDiceRoll,
        showDiceResult,
        clearDiceAnimation,
        startPlayerMove,
        clearMoveAnimation,
        startCardReveal,
        clearCardAnimation,
        clearAllAnimations,
      }}
    >
      {children}
    </AnimationContext.Provider>
  );
}

export function useAnimation() {
  const context = useContext(AnimationContext);
  if (!context) {
    throw new Error('useAnimation must be used within AnimationProvider');
  }
  return context;
}

// Export type for external use
export type { AnimationContextType, AnimationState };
