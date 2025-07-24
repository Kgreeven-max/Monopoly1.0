import { useState, useRef, useCallback, useEffect } from 'react';
import { boardPositionCache } from '../utils/BoardPositionCache';

/**
 * Hook to manage player positions with animation support
 * Provides both logical positions (0-39) and visual positions (x, y)
 */
export const usePlayerPositions = () => {
  // Logical positions (space indices)
  const [logicalPositions, setLogicalPositions] = useState(new Map());
  
  // Visual positions (x, y coordinates)
  const [visualPositions, setVisualPositions] = useState(new Map());
  
  // Animation states for each player
  const animationStates = useRef(new Map());
  
  // Track players on each space for offset calculations
  const spaceOccupancy = useRef(new Map());

  /**
   * Initialize player position
   */
  const initializePlayer = useCallback((playerId, position = 0) => {
    setLogicalPositions(prev => new Map(prev).set(playerId, position));
    
    // Calculate visual position
    const playersOnSpace = Array.from(spaceOccupancy.current.get(position) || []);
    if (!playersOnSpace.includes(playerId)) {
      playersOnSpace.push(playerId);
      spaceOccupancy.current.set(position, playersOnSpace);
    }
    
    const playerIndex = playersOnSpace.indexOf(playerId);
    const visualPos = boardPositionCache.getPlayerPosition(
      position, 
      playerIndex, 
      playersOnSpace.length
    );
    
    setVisualPositions(prev => new Map(prev).set(playerId, visualPos));
  }, []);

  /**
   * Update player's logical position (instant update)
   */
  const updateLogicalPosition = useCallback((playerId, newPosition) => {
    setLogicalPositions(prev => {
      const updated = new Map(prev);
      const oldPosition = updated.get(playerId);
      updated.set(playerId, newPosition);
      
      // Update space occupancy
      if (oldPosition !== undefined) {
        const oldSpacePlayers = spaceOccupancy.current.get(oldPosition) || [];
        const index = oldSpacePlayers.indexOf(playerId);
        if (index !== -1) {
          oldSpacePlayers.splice(index, 1);
          if (oldSpacePlayers.length === 0) {
            spaceOccupancy.current.delete(oldPosition);
          } else {
            spaceOccupancy.current.set(oldPosition, oldSpacePlayers);
          }
        }
      }
      
      const newSpacePlayers = spaceOccupancy.current.get(newPosition) || [];
      if (!newSpacePlayers.includes(playerId)) {
        newSpacePlayers.push(playerId);
        spaceOccupancy.current.set(newPosition, newSpacePlayers);
      }
      
      return updated;
    });
  }, []);

  /**
   * Update player's visual position (for animations)
   */
  const updateVisualPosition = useCallback((playerId, position) => {
    setVisualPositions(prev => new Map(prev).set(playerId, position));
  }, []);

  /**
   * Get current animation state for a player
   */
  const getAnimationState = useCallback((playerId) => {
    return animationStates.current.get(playerId) || null;
  }, []);

  /**
   * Set animation state for a player
   */
  const setAnimationState = useCallback((playerId, state) => {
    if (state) {
      animationStates.current.set(playerId, state);
    } else {
      animationStates.current.delete(playerId);
    }
  }, []);

  /**
   * Check if player is currently animating
   */
  const isAnimating = useCallback((playerId) => {
    return animationStates.current.has(playerId);
  }, []);

  /**
   * Get all players on a specific space
   */
  const getPlayersOnSpace = useCallback((spaceId) => {
    return spaceOccupancy.current.get(spaceId) || [];
  }, []);

  /**
   * Remove a player from tracking
   */
  const removePlayer = useCallback((playerId) => {
    const position = logicalPositions.get(playerId);
    
    setLogicalPositions(prev => {
      const updated = new Map(prev);
      updated.delete(playerId);
      return updated;
    });
    
    setVisualPositions(prev => {
      const updated = new Map(prev);
      updated.delete(playerId);
      return updated;
    });
    
    // Clean up space occupancy
    if (position !== undefined) {
      const spacePlayers = spaceOccupancy.current.get(position) || [];
      const index = spacePlayers.indexOf(playerId);
      if (index !== -1) {
        spacePlayers.splice(index, 1);
        if (spacePlayers.length === 0) {
          spaceOccupancy.current.delete(position);
        } else {
          spaceOccupancy.current.set(position, spacePlayers);
        }
      }
    }
    
    animationStates.current.delete(playerId);
  }, [logicalPositions]);

  /**
   * Batch update multiple players
   */
  const batchUpdatePlayers = useCallback((updates) => {
    updates.forEach(({ playerId, position }) => {
      initializePlayer(playerId, position);
    });
  }, [initializePlayer]);

  /**
   * Get movement path for a player
   */
  const getMovementPath = useCallback((playerId, toPosition, steps) => {
    const fromPosition = logicalPositions.get(playerId) || 0;
    return boardPositionCache.getMovementPath(fromPosition, toPosition, steps);
  }, [logicalPositions]);

  /**
   * Clear all player positions
   */
  const clearAllPositions = useCallback(() => {
    setLogicalPositions(new Map());
    setVisualPositions(new Map());
    animationStates.current.clear();
    spaceOccupancy.current.clear();
  }, []);

  return {
    // Position getters
    logicalPositions,
    visualPositions,
    
    // Position management
    initializePlayer,
    updateLogicalPosition,
    updateVisualPosition,
    removePlayer,
    batchUpdatePlayers,
    clearAllPositions,
    
    // Animation state
    getAnimationState,
    setAnimationState,
    isAnimating,
    
    // Utility functions
    getPlayersOnSpace,
    getMovementPath
  };
};