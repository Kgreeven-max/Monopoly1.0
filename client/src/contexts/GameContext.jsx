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
  currentTurn: 0,
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
      return {
        ...initialGameState, // Reset to initial structure
        ...action.payload, // Apply received state
        loading: false,
        error: null,
      };
    case 'UPDATE_GAME_STATE':
      console.log("[GameContext] Updating game state:", action.payload);
      return {
        ...state,
        ...action.payload, // Merge updates
        loading: false, // Assume update means loading is done for now
        error: null,
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
        isBot: action.payload.is_bot || false,
      };
      return {
        ...state,
        players: [...state.players, newPlayer],
        loading: false,
        error: null,
      };
    case 'PLAYER_REMOVED':
      console.log("[GameContext] Player removed:", action.payload);
      return {
        ...state,
        players: state.players.filter(player => player.id !== action.payload.player_id),
        loading: false,
        error: null,
      };
    case 'GAME_STARTED':
      console.log("[GameContext] Game started:", action.payload);
      return {
        ...state,
        status: 'active',
        currentPlayerId: action.payload.first_player?.id || state.currentPlayerId,
        loading: false,
        error: null,
      };
    case 'ADD_NOTIFICATION':
      console.log("[GameContext] Adding notification:", action.payload);
      return {
        ...state,
        notifications: [action.payload, ...state.notifications.slice(0, 19)], // Keep last 20
      };
    case 'SET_ERROR':
      console.error("[GameContext] Setting error:", action.payload);
      return { ...state, error: action.payload, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    default:
      return state;
  }
}

export const GameProvider = ({ children }) => {
  const [gameState, dispatch] = useReducer(gameReducer, initialGameState);
  const { socket, emit } = useSocket(); // Get socket instance and emit function
  const { playerInfo, adminKey } = useAuth(); // Get playerInfo and adminKey

  // Effect for handling game state updates from the server
  useEffect(() => {
    if (socket) {
      const handleGameStateUpdate = (newState) => {
        console.log('[GameContext] Received game_state_update:', newState);
        dispatch({ type: 'SET_INITIAL_STATE', payload: newState });
      };

      const handleGameNotification = (notification) => {
        console.log('[GameContext] Received game_notification:', notification);
        dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
        // Optionally show a toast or alert here too
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

      socket.on('game_state_update', handleGameStateUpdate);
      socket.on('game_notification', handleGameNotification);
      socket.on('auth_socket_response', handleAuthSuccess);
      
      // Setup wizard events
      socket.on('game_created', handleGameCreated);
      socket.on('player_added', handlePlayerAdded);
      socket.on('player_removed', handlePlayerRemoved);
      socket.on('game_started', handleGameStarted);
      socket.on('game_error', handleGameError);

      // Cleanup function
      return () => {
        console.log('[GameContext] Cleaning up game listeners...');
        socket.off('game_state_update', handleGameStateUpdate);
        socket.off('game_notification', handleGameNotification);
        socket.off('auth_socket_response', handleAuthSuccess);
        
        // Remove setup wizard events
        socket.off('game_created', handleGameCreated);
        socket.off('player_added', handlePlayerAdded);
        socket.off('player_removed', handlePlayerRemoved);
        socket.off('game_started', handleGameStarted);
        socket.off('game_error', handleGameError);
      };
    }
  }, [socket, playerInfo?.id]);

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
      updateGameState
    }}>
      {children}
    </GameContext.Provider>
  );
}; 