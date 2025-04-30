import React, { createContext, useContext, useState, useReducer, useEffect, useCallback } from 'react';
import { useSocket } from './SocketContext';
import { useAuth } from './AuthContext';

const GameContext = createContext();

export const useGame = () => useContext(GameContext);

// Define the initial state for the game
const initialGameState = {
  gameId: null,
  status: 'Initializing', // Possible values: Initializing, Waiting, setup, active, Paused, Ended
  players: [], // List of player objects { id, username, money, position, ... }
  properties: [], // List of property objects { id, name, owner_id, ... }
  currentPlayerId: null,
  current_player_id: null, // Keeping both for compatibility
  currentTurn: 0,
  current_turn: 0, // Keeping both for compatibility
  lastDiceRoll: null, // [dice1, dice2]
  notifications: [], // Game log or specific notifications
  // Add other relevant state fields: auction_info, event_info, etc.
  loading: true, // Start in loading state
  error: null,
};

// Reducer to manage game state updates
function gameReducer(state, action) {
  switch (action.type) {
    case 'SET_INITIAL_STATE':
      console.log("[GameContext] Setting initial state:", action.payload);
      // Make sure we're keeping all data from the payload
      return {
        ...initialGameState,
        ...action.payload,
        // Ensure we have both camelCase and snake_case for compatibility
        currentPlayerId: action.payload.current_player_id || action.payload.currentPlayerId || null,
        current_player_id: action.payload.current_player_id || action.payload.currentPlayerId || null,
        currentTurn: action.payload.current_turn || action.payload.currentTurn || 0,
        current_turn: action.payload.current_turn || action.payload.currentTurn || 0,
        // Make sure players array is properly set
        players: action.payload.players || [],
        // Make sure properties array is properly set
        properties: action.payload.properties || [],
        loading: false,
        error: null,
      };
    case 'UPDATE_GAME_STATE':
      console.log("[GameContext] Updating game state:", action.payload);
      return {
        ...state,
        ...action.payload, // Merge updates
        // Ensure we have both camelCase and snake_case for compatibility
        currentPlayerId: action.payload.current_player_id || state.currentPlayerId,
        currentTurn: action.payload.current_turn || state.currentTurn,
        loading: false, // Assume update means loading is done for now
        error: null,
      };
    case 'PLAYER_MOVED':
      console.log("[GameContext] Player moved:", action.payload);
      const { player_id, new_position } = action.payload;
      return {
        ...state,
        players: state.players.map(player => 
          player.id === player_id 
            ? { ...player, position: new_position } 
            : player
        ),
        notifications: [
          { 
            message: `${state.players.find(p => p.id === player_id)?.username || `Player ${player_id}`} moved to position ${new_position}` 
          },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'DICE_ROLLED':
      console.log("[GameContext] Dice rolled:", action.payload);
      const { dice_values, player_id: rollingPlayerId } = action.payload;
      return {
        ...state,
        lastDiceRoll: dice_values,
        notifications: [
          { 
            message: `${state.players.find(p => p.id === rollingPlayerId)?.username || `Player ${rollingPlayerId}`} rolled ${dice_values[0]} and ${dice_values[1]}` 
          },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'TURN_CHANGED':
      console.log("[GameContext] Turn changed:", action.payload);
      return {
        ...state,
        currentPlayerId: action.payload.player_id,
        current_player_id: action.payload.player_id,
        currentTurn: action.payload.turn_number || state.currentTurn + 1,
        current_turn: action.payload.turn_number || state.current_turn + 1,
        notifications: [
          { 
            message: `Turn changed to ${state.players.find(p => p.id === action.payload.player_id)?.username || `Player ${action.payload.player_id}`}` 
          },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'PROPERTY_UPDATED':
      console.log("[GameContext] Property updated:", action.payload);
      const { property_id, updates } = action.payload;
      return {
        ...state,
        properties: state.properties.map(property => 
          property.id === property_id 
            ? { ...property, ...updates } 
            : property
        ),
        notifications: [
          { 
            message: `Property ${state.properties.find(p => p.id === property_id)?.name || property_id} updated` 
          },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'PLAYER_UPDATED':
      console.log("[GameContext] Player updated:", action.payload);
      const { player_id: updatedPlayerId, updates: playerUpdates } = action.payload;
      return {
        ...state,
        players: state.players.map(player => 
          player.id === updatedPlayerId 
            ? { ...player, ...playerUpdates } 
            : player
        ),
        notifications: playerUpdates.money !== undefined 
          ? [
              { 
                message: `${state.players.find(p => p.id === updatedPlayerId)?.username || `Player ${updatedPlayerId}`}'s money changed to $${playerUpdates.money}` 
              },
              ...state.notifications.slice(0, 19)
            ]
          : state.notifications
      };
    case 'GAME_CREATED':
      console.log("[GameContext] Game created:", action.payload);
      return {
        ...state,
        gameId: action.payload.game_id,
        status: 'setup',
        loading: false,
        error: null,
      };
    case 'PLAYER_ADDED':
      console.log("[GameContext] Player added:", action.payload);
      const newPlayer = {
        id: action.payload.player_id,
        name: action.payload.player_name,
        username: action.payload.player_name,
        is_bot: action.payload.is_bot || false,
        money: action.payload.money || 1500,
        position: action.payload.position || 0,
      };
      
      // Check if player already exists to avoid duplicates
      const playerExists = state.players.some(p => p.id === newPlayer.id);
      
      return {
        ...state,
        players: playerExists 
          ? state.players 
          : [...state.players, newPlayer],
        loading: false,
        error: null,
        notifications: [
          { message: `${newPlayer.name}${newPlayer.is_bot ? ' (Bot)' : ''} added to the game` },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'PLAYER_REMOVED':
      console.log("[GameContext] Player removed:", action.payload);
      const removedPlayer = state.players.find(p => p.id === action.payload.player_id);
      return {
        ...state,
        players: state.players.filter(player => player.id !== action.payload.player_id),
        loading: false,
        error: null,
        notifications: [
          { message: `${removedPlayer?.name || `Player ${action.payload.player_id}`} removed from the game` },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'GAME_STARTED':
      console.log("[GameContext] Game started:", action.payload);
      return {
        ...state,
        status: 'active',
        currentPlayerId: action.payload.first_player?.id || action.payload.current_player_id || state.currentPlayerId,
        current_player_id: action.payload.first_player?.id || action.payload.current_player_id || state.current_player_id,
        loading: false,
        error: null,
        notifications: [
          { message: 'Game started!' },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'ADD_NOTIFICATION':
      console.log("[GameContext] Adding notification:", action.payload);
      return {
        ...state,
        notifications: [action.payload, ...state.notifications.slice(0, 19)], // Keep last 20
      };
    case 'SET_ERROR':
      console.error("[GameContext] Setting error:", action.payload);
      return { 
        ...state, 
        error: action.payload, 
        loading: false,
        notifications: [
          { message: `Error: ${action.payload.message || action.payload}`, type: 'error' },
          ...state.notifications.slice(0, 19)
        ]
      };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'CARD_DRAWN':
      console.log("[GameContext] Card drawn:", action.payload);
      return {
        ...state,
        lastCardDrawn: action.payload,
        notifications: [
          { 
            message: `${state.players.find(p => p.id === action.payload.player_id)?.username || `Player ${action.payload.player_id}`} drew a ${action.payload.cardType || ''} card: ${action.payload.card?.title || action.payload.card?.description || 'Unknown Card'}` 
          },
          ...state.notifications.slice(0, 19)
        ]
      };
    default:
      return state;
  }
}

export const GameProvider = ({ children }) => {
  const [gameState, dispatch] = useReducer(gameReducer, initialGameState);
  const { socket, emit } = useSocket(); // Get socket instance and emit function
  const { playerInfo, adminKey, user } = useAuth(); // Get playerInfo, adminKey, and user

  // Effect for handling game state updates from the server
  useEffect(() => {
    if (socket) {
      const handleGameStateUpdate = (data) => {
        console.log('[GameContext] Received game_state_update:', data);
        
        // Store previous player positions to detect changes
        const previousPositions = {};
        if (gameState.players && gameState.players.length) {
          gameState.players.forEach(player => {
            if (player && player.id) {
              previousPositions[player.id] = player.position;
            }
          });
        }
        
        // Update game state first
        dispatch({ type: 'SET_INITIAL_STATE', payload: data });
        
        // Check if player positions changed and dispatch explicit move events
        if (data.players && data.players.length) {
          data.players.forEach(player => {
            if (player && player.id && previousPositions[player.id] !== undefined) {
              const oldPosition = previousPositions[player.id];
              const newPosition = player.position;
              
              if (oldPosition !== newPosition) {
                console.log(`[GameContext] Detected player ${player.id} moved from ${oldPosition} to ${newPosition}`);
                // Dispatch a separate player moved event for animation
                dispatch({ 
                  type: 'PLAYER_MOVED', 
                  payload: { 
                    player_id: player.id, 
                    old_position: oldPosition,
                    new_position: newPosition 
                  } 
                });
              }
            }
          });
        }
      };

      const handleGameNotification = (notification) => {
        console.log('[GameContext] Received game_notification:', notification);
        dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
        // Optionally show a toast or alert here too
      };
      
      // Player movement events
      const handlePlayerMoved = (data) => {
        console.log('[GameContext] Player moved:', data);
        dispatch({ type: 'PLAYER_MOVED', payload: data });
      };
      
      // Card draw events
      const handleCardDrawn = (data) => {
        console.log('[GameContext] Card drawn:', data);
        dispatch({ type: 'CARD_DRAWN', payload: data });
      };
      
      // Community chest card events
      const handleCommunityChestCardDrawn = (data) => {
        console.log('[GameContext] Community Chest card drawn:', data);
        dispatch({ type: 'CARD_DRAWN', payload: {
          ...data,
          cardType: 'community_chest'
        }});
      };
      
      // Chance card events
      const handleChanceCardDrawn = (data) => {
        console.log('[GameContext] Chance card drawn:', data);
        dispatch({ type: 'CARD_DRAWN', payload: {
          ...data,
          cardType: 'chance'
        }});
      };
      
      // Dice roll events
      const handleDiceRolled = (data) => {
        console.log('[GameContext] Dice rolled:', data);
        dispatch({ type: 'DICE_ROLLED', payload: data });
      };
      
      // Turn change events
      const handleTurnChanged = (data) => {
        console.log('[GameContext] Turn changed:', data);
        dispatch({ type: 'TURN_CHANGED', payload: data });
      };
      
      // Property update events
      const handlePropertyUpdated = (data) => {
        console.log('[GameContext] Property updated:', data);
        dispatch({ type: 'PROPERTY_UPDATED', payload: data });
      };
      
      // Player update events (money, etc.)
      const handlePlayerUpdated = (data) => {
        console.log('[GameContext] Player updated:', data);
        dispatch({ type: 'PLAYER_UPDATED', payload: data });
      };
      
      // Game setup event handlers
      const handleGameCreated = (data) => {
        console.log('[GameContext] Game created:', data);
        dispatch({ type: 'GAME_CREATED', payload: data });
      };
      
      const handlePlayerAdded = (data) => {
        console.log('[GameContext] Player added:', data);
        dispatch({ type: 'PLAYER_ADDED', payload: data });
      };
      
      const handlePlayerRemoved = (data) => {
        console.log('[GameContext] Player removed:', data);
        dispatch({ type: 'PLAYER_REMOVED', payload: data });
      };
      
      const handleGameStarted = (data) => {
        console.log('[GameContext] Game started:', data);
        dispatch({ type: 'GAME_STARTED', payload: data });
      };
      
      const handleGameError = (data) => {
        console.error('[GameContext] Game error:', data);
        dispatch({ type: 'SET_ERROR', payload: data.error });
      };
      
      // Listener for successful socket authentication confirmation
      const handleAuthSuccess = (data) => {
        if(data.success && data.player_id === playerInfo?.id) {
          console.log(`[GameContext] Socket authenticated for player ${data.player_id}. Requesting initial game state...`);
          socket.emit('request_game_state');
        }
      };

      // Register all event listeners
      socket.on('game_state_update', handleGameStateUpdate);
      socket.on('game_notification', handleGameNotification);
      socket.on('auth_socket_response', handleAuthSuccess);
      
      // Game play events
      socket.on('player_moved', handlePlayerMoved);
      socket.on('dice_rolled', handleDiceRolled);
      socket.on('turn_changed', handleTurnChanged);
      socket.on('property_updated', handlePropertyUpdated);
      socket.on('player_updated', handlePlayerUpdated);
      socket.on('card_drawn', handleCardDrawn);
      socket.on('community_chest_card_drawn', handleCommunityChestCardDrawn);
      socket.on('chance_card_drawn', handleChanceCardDrawn);
      
      // Setup wizard events
      socket.on('game_created', handleGameCreated);
      socket.on('player_added', handlePlayerAdded);
      socket.on('player_removed', handlePlayerRemoved);
      socket.on('game_started', handleGameStarted);
      socket.on('game_error', handleGameError);

      // If we have playerInfo or we're in display mode, request game state
      if ((playerInfo || user?.role === 'display') && gameState.loading) {
        console.log('[GameContext] Player info or display mode available, requesting game state...');
        socket.emit('request_game_state');
      }

      // Cleanup function
      return () => {
        console.log('[GameContext] Cleaning up game listeners...');
        socket.off('game_state_update', handleGameStateUpdate);
        socket.off('game_notification', handleGameNotification);
        socket.off('auth_socket_response', handleAuthSuccess);
        
        // Remove game play events
        socket.off('player_moved', handlePlayerMoved);
        socket.off('dice_rolled', handleDiceRolled);
        socket.off('turn_changed', handleTurnChanged);
        socket.off('property_updated', handlePropertyUpdated);
        socket.off('player_updated', handlePlayerUpdated);
        socket.off('card_drawn', handleCardDrawn);
        socket.off('community_chest_card_drawn', handleCommunityChestCardDrawn);
        socket.off('chance_card_drawn', handleChanceCardDrawn);
        
        // Remove setup wizard events
        socket.off('game_created', handleGameCreated);
        socket.off('player_added', handlePlayerAdded);
        socket.off('player_removed', handlePlayerRemoved);
        socket.off('game_started', handleGameStarted);
        socket.off('game_error', handleGameError);
      };
    }
  }, [socket, playerInfo, user, gameState.loading]);

  // Game management functions
  const createGame = useCallback((config) => {
    if (!socket || !adminKey) return;
    
    dispatch({ type: 'SET_LOADING', payload: true });
    emit('create_game', { 
      admin_key: adminKey,
      ...config
    });
  }, [socket, emit, adminKey]);
  
  const addPlayer = useCallback((username, isBot = false) => {
    if (!socket || !adminKey || !gameState.gameId) return;
    
    dispatch({ type: 'SET_LOADING', payload: true });
    
    if (isBot) {
      emit('add_bot', {
        admin_key: adminKey,
        game_id: gameState.gameId,
        name: username || undefined,  // Undefined will trigger server to generate a name
        type: 'random'  // Or specify a type
      });
    } else {
      emit('add_player', {
        admin_key: adminKey,
        game_id: gameState.gameId,
        username: username
      });
    }
  }, [socket, emit, adminKey, gameState.gameId]);
  
  const removePlayer = useCallback((playerId) => {
    if (!socket || !adminKey || !gameState.gameId) return;
    
    dispatch({ type: 'SET_LOADING', payload: true });
    emit('remove_player', {
      admin_key: adminKey,
      game_id: gameState.gameId,
      player_id: playerId
    });
  }, [socket, emit, adminKey, gameState.gameId]);
  
  const startGame = useCallback(() => {
    if (!socket || !adminKey || !gameState.gameId) return;
    
    dispatch({ type: 'SET_LOADING', payload: true });
    emit('start_game', { 
      admin_key: adminKey,
      game_id: gameState.gameId 
    });
  }, [socket, emit, adminKey, gameState.gameId]);

  // Player action methods
  const rollDice = useCallback(() => {
    if (!socket || !playerInfo || !gameState.gameId) return;
    
    emit('roll_dice', {
      player_id: playerInfo.id,
      game_id: gameState.gameId
    });
  }, [socket, emit, playerInfo, gameState.gameId]);
  
  const buyProperty = useCallback((propertyId) => {
    if (!socket || !playerInfo || !gameState.gameId) return;
    
    emit('buy_property', {
      player_id: playerInfo.id,
      game_id: gameState.gameId,
      property_id: propertyId
    });
  }, [socket, emit, playerInfo, gameState.gameId]);
  
  const endTurn = useCallback(() => {
    if (!socket || !playerInfo || !gameState.gameId) return;
    
    emit('end_turn', {
      player_id: playerInfo.id,
      game_id: gameState.gameId
    });
  }, [socket, emit, playerInfo, gameState.gameId]);

  // Method to explicitly update game state (used by the Admin Dashboard)
  const updateGameState = useCallback((newState) => {
    dispatch({ type: 'UPDATE_GAME_STATE', payload: newState });
  }, []);

  return (
    <GameContext.Provider value={{ 
      gameState, 
      dispatch,
      createGame,
      addPlayer,
      removePlayer,
      startGame,
      updateGameState,
      rollDice,
      buyProperty,
      endTurn
    }}>
      {children}
    </GameContext.Provider>
  );
}; 