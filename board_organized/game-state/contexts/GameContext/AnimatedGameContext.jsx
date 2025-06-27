import React, { createContext, useContext, useState, useReducer, useEffect, useCallback } from 'react';
import { useSocket } from '../SocketContext';
import { useAuth } from '../AuthContext';
import { useAnimation } from '../AnimationContext';

const AnimatedGameContext = createContext();

export const useAnimatedGame = () => useContext(AnimatedGameContext);

// Enhanced initial state with animation tracking
const initialGameState = {
  gameId: null,
  status: 'Initializing',
  players: [],
  properties: [],
  currentPlayerId: null,
  current_player_id: null,
  currentTurn: 0,
  current_turn: 0,
  lastDiceRoll: null,
  notifications: [],
  loading: true,
  error: null,
  // Animation-specific state
  animationMode: true, // Enable animations by default
  lastMovementData: null,
  pendingMovements: new Map(),
};

// Enhanced reducer with animation handling
function animatedGameReducer(state, action) {
  switch (action.type) {
    case 'SET_INITIAL_STATE':
      console.log("[AnimatedGameContext] Setting initial state:", action.payload);
      return {
        ...initialGameState,
        ...action.payload,
        currentPlayerId: action.payload.current_player_id || action.payload.currentPlayerId || null,
        current_player_id: action.payload.current_player_id || action.payload.currentPlayerId || null,
        currentTurn: action.payload.current_turn || action.payload.currentTurn || 0,
        current_turn: action.payload.current_turn || action.payload.currentTurn || 0,
        players: action.payload.players || [],
        properties: action.payload.properties || [],
        loading: false,
        error: null,
      };

    case 'UPDATE_GAME_STATE':
      console.log("[AnimatedGameContext] Updating game state:", action.payload);
      return {
        ...state,
        ...action.payload,
        currentPlayerId: action.payload.current_player_id || state.currentPlayerId,
        currentTurn: action.payload.current_turn || state.currentTurn,
        loading: false,
        error: null,
      };

    case 'DICE_ROLLED':
      console.log("[AnimatedGameContext] Dice rolled:", action.payload);
      const { dice_values, player_id: rollingPlayerId } = action.payload;
      return {
        ...state,
        lastDiceRoll: dice_values,
        notifications: [
          { 
            message: `${state.players.find(p => p.id === rollingPlayerId)?.username || `Player ${rollingPlayerId}`} rolled ${dice_values[0]} and ${dice_values[1]}`,
            type: 'dice_roll',
            playerId: rollingPlayerId,
            diceValues: dice_values
          },
          ...state.notifications.slice(0, 19)
        ]
      };

    case 'PLAYER_MOVE_INITIATED':
      console.log("[AnimatedGameContext] Player move initiated:", action.payload);
      const { player_id, old_position, new_position, dice_total } = action.payload;
      
      // Store movement data for animation
      const movementData = {
        playerId: player_id,
        fromPosition: old_position,
        toPosition: new_position,
        steps: dice_total || calculateSteps(old_position, new_position),
        timestamp: Date.now()
      };

      return {
        ...state,
        lastMovementData: movementData,
        pendingMovements: new Map(state.pendingMovements).set(player_id, movementData),
        notifications: [
          { 
            message: `${state.players.find(p => p.id === player_id)?.username || `Player ${player_id}`} is moving from ${old_position} to ${new_position}`,
            type: 'movement_start',
            playerId: player_id
          },
          ...state.notifications.slice(0, 19)
        ]
      };

    case 'PLAYER_MOVE_COMPLETED':
      console.log("[AnimatedGameContext] Player move completed:", action.payload);
      const { player_id: movedPlayerId, final_position } = action.payload;
      
      // Update player position after animation completes
      const updatedPendingMovements = new Map(state.pendingMovements);
      updatedPendingMovements.delete(movedPlayerId);

      return {
        ...state,
        players: state.players.map(player => 
          player.id === movedPlayerId 
            ? { ...player, position: final_position } 
            : player
        ),
        pendingMovements: updatedPendingMovements,
        notifications: [
          { 
            message: `${state.players.find(p => p.id === movedPlayerId)?.username || `Player ${movedPlayerId}`} arrived at position ${final_position}`,
            type: 'movement_complete',
            playerId: movedPlayerId
          },
          ...state.notifications.slice(0, 19)
        ]
      };

    case 'PLAYER_MOVED':
      console.log("[AnimatedGameContext] Player moved (legacy):", action.payload);
      // For backwards compatibility, but prefer PLAYER_MOVE_INITIATED/COMPLETED
      const { player_id: legacyPlayerId, new_position: legacyNewPosition } = action.payload;
      return {
        ...state,
        players: state.players.map(player => 
          player.id === legacyPlayerId 
            ? { ...player, position: legacyNewPosition } 
            : player
        ),
        notifications: [
          { 
            message: `${state.players.find(p => p.id === legacyPlayerId)?.username || `Player ${legacyPlayerId}`} moved to position ${legacyNewPosition}` 
          },
          ...state.notifications.slice(0, 19)
        ]
      };

    case 'TURN_CHANGED':
      console.log("[AnimatedGameContext] Turn changed:", action.payload);
      return {
        ...state,
        currentPlayerId: action.payload.player_id,
        current_player_id: action.payload.player_id,
        currentTurn: action.payload.turn_number || state.currentTurn + 1,
        current_turn: action.payload.turn_number || state.current_turn + 1,
        notifications: [
          { 
            message: `Turn changed to ${state.players.find(p => p.id === action.payload.player_id)?.username || `Player ${action.payload.player_id}`}`,
            type: 'turn_change',
            playerId: action.payload.player_id
          },
          ...state.notifications.slice(0, 19)
        ]
      };

    case 'TOGGLE_ANIMATION_MODE':
      console.log("[AnimatedGameContext] Toggling animation mode:", !state.animationMode);
      return {
        ...state,
        animationMode: !state.animationMode
      };

    // ... other cases remain the same as original GameContext
    case 'PROPERTY_UPDATED':
    case 'PLAYER_UPDATED':
    case 'GAME_CREATED':
    case 'PLAYER_ADDED':
    case 'PLAYER_REMOVED':
    case 'GAME_STARTED':
    case 'ADD_NOTIFICATION':
    case 'SET_ERROR':
    case 'SET_LOADING':
    case 'CARD_DRAWN':
      // Delegate to original logic (would need to import original reducer)
      return state;

    default:
      return state;
  }
}

// Helper function to calculate steps between positions
function calculateSteps(fromPosition, toPosition) {
  if (toPosition >= fromPosition) {
    return toPosition - fromPosition;
  } else {
    // Wrapped around the board
    return (40 - fromPosition) + toPosition;
  }
}

export const AnimatedGameProvider = ({ children }) => {
  const [gameState, dispatch] = useReducer(animatedGameReducer, initialGameState);
  const { socket, emit } = useSocket();
  const { playerInfo, adminKey, user } = useAuth();
  const { 
    animateTurnSequence, 
    queuePlayerMovement, 
    queueDiceRoll,
    isAnimating,
    getAnimationStatus 
  } = useAnimation();

  // Enhanced handler for coordinated dice roll and movement
  const handleCombinedTurnEvent = useCallback(async (diceData, movementData) => {
    console.log('[AnimatedGameContext] Handling combined turn event:', { diceData, movementData });
    
    if (!gameState.animationMode) {
      // Skip animation, update immediately
      dispatch({ type: 'DICE_ROLLED', payload: diceData });
      dispatch({ type: 'PLAYER_MOVED', payload: movementData });
      return;
    }

    try {
      // Initiate the animated sequence
      dispatch({ type: 'DICE_ROLLED', payload: diceData });
      dispatch({ 
        type: 'PLAYER_MOVE_INITIATED', 
        payload: {
          player_id: movementData.player_id || diceData.player_id,
          old_position: movementData.old_position || 0,
          new_position: movementData.new_position,
          dice_total: diceData.dice_values[0] + diceData.dice_values[1]
        }
      });

      // Trigger animation sequence
      await animateTurnSequence(
        movementData.player_id || diceData.player_id,
        diceData.dice_values,
        movementData.old_position || 0,
        movementData.new_position
      );

      // Mark movement as completed
      dispatch({ 
        type: 'PLAYER_MOVE_COMPLETED', 
        payload: {
          player_id: movementData.player_id || diceData.player_id,
          final_position: movementData.new_position
        }
      });

    } catch (error) {
      console.error('[AnimatedGameContext] Animation sequence failed:', error);
      // Fallback to immediate update
      dispatch({ type: 'PLAYER_MOVED', payload: movementData });
    }
  }, [gameState.animationMode, animateTurnSequence]);

  // Socket event handlers with animation integration
  useEffect(() => {
    if (socket) {
      const handleGameStateUpdate = (data) => {
        console.log('[AnimatedGameContext] Received game_state_update:', data);
        
        // Track previous positions for movement detection
        const previousPositions = {};
        if (gameState.players && gameState.players.length) {
          gameState.players.forEach(player => {
            if (player && player.id) {
              previousPositions[player.id] = player.position;
            }
          });
        }
        
        // Update game state
        dispatch({ type: 'SET_INITIAL_STATE', payload: data });
        
        // Check for position changes and queue animations
        if (data.players && data.players.length && gameState.animationMode) {
          data.players.forEach(player => {
            if (player && player.id && previousPositions[player.id] !== undefined) {
              const oldPosition = previousPositions[player.id];
              const newPosition = player.position;
              
              if (oldPosition !== newPosition) {
                console.log(`[AnimatedGameContext] Detected position change for player ${player.id}: ${oldPosition} → ${newPosition}`);
                
                const steps = calculateSteps(oldPosition, newPosition);
                
                // Queue the movement animation
                queuePlayerMovement(player.id, oldPosition, newPosition, steps);
              }
            }
          });
        }
      };

      const handleDiceRolled = (data) => {
        console.log('[AnimatedGameContext] Received dice_rolled:', data);
        
        if (gameState.animationMode) {
          // Queue dice animation
          queueDiceRoll(data.dice_values || data.roll, 1500);
        }
        
        dispatch({ type: 'DICE_ROLLED', payload: data });
      };

      const handlePlayerMoved = (data) => {
        console.log('[AnimatedGameContext] Received player_moved:', data);
        
        if (gameState.animationMode) {
          // Calculate movement parameters
          const steps = data.steps || calculateSteps(data.old_position || 0, data.new_position);
          
          // Queue movement animation
          queuePlayerMovement(
            data.player_id, 
            data.old_position || 0, 
            data.new_position, 
            steps
          );
        } else {
          // Immediate update
          dispatch({ type: 'PLAYER_MOVED', payload: data });
        }
      };

      const handleTurnChanged = (data) => {
        console.log('[AnimatedGameContext] Received turn_changed:', data);
        dispatch({ type: 'TURN_CHANGED', payload: data });
      };

      // Register enhanced event listeners
      socket.on('game_state_update', handleGameStateUpdate);
      socket.on('dice_rolled', handleDiceRolled);
      socket.on('player_moved', handlePlayerMoved);
      socket.on('turn_changed', handleTurnChanged);

      // Request initial game state
      if ((playerInfo || user?.role === 'display') && gameState.loading) {
        console.log('[AnimatedGameContext] Requesting initial game state...');
        socket.emit('request_game_state');
      }

      return () => {
        console.log('[AnimatedGameContext] Cleaning up enhanced listeners...');
        socket.off('game_state_update', handleGameStateUpdate);
        socket.off('dice_rolled', handleDiceRolled);
        socket.off('player_moved', handlePlayerMoved);
        socket.off('turn_changed', handleTurnChanged);
      };
    }
  }, [socket, playerInfo, user, gameState.loading, gameState.animationMode, queuePlayerMovement, queueDiceRoll]);

  // Enhanced game management functions
  const toggleAnimationMode = useCallback(() => {
    dispatch({ type: 'TOGGLE_ANIMATION_MODE' });
  }, []);

  const getEnhancedGameStatus = useCallback(() => {
    const animationStatus = getAnimationStatus();
    return {
      ...gameState,
      animation: animationStatus,
      pendingMovementsCount: gameState.pendingMovements.size
    };
  }, [gameState, getAnimationStatus]);

  // Original game functions (would need to be imported from original context)
  const createGame = useCallback((config) => {
    if (!socket || !adminKey) return;
    dispatch({ type: 'SET_LOADING', payload: true });
    emit('create_game', { 
      admin_key: adminKey,
      ...config
    });
  }, [socket, emit, adminKey]);

  const rollDice = useCallback(() => {
    if (!socket || !playerInfo || !gameState.gameId) return;
    
    emit('roll_dice', {
      player_id: playerInfo.id,
      game_id: gameState.gameId
    });
  }, [socket, emit, playerInfo, gameState.gameId]);

  return (
    <AnimatedGameContext.Provider value={{ 
      gameState, 
      dispatch,
      
      // Enhanced functions
      toggleAnimationMode,
      getEnhancedGameStatus,
      handleCombinedTurnEvent,
      
      // Original functions
      createGame,
      rollDice,
      
      // Animation state
      isAnimating,
      animationMode: gameState.animationMode
    }}>
      {children}
    </AnimatedGameContext.Provider>
  );
};