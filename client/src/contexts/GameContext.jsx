import React, { createContext, useContext, useState, useReducer, useEffect } from 'react';
import { useSocket } from './SocketContext';
import { useAuth } from './AuthContext';

const GameContext = createContext();

export const useGame = () => useContext(GameContext);

// Define the initial state for the game
const initialGameState = {
  gameId: null,
  status: 'Initializing', // e.g., Waiting, InProgress, Finished
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
  const { socket } = useSocket(); // Get socket instance
  const { playerInfo } = useAuth(); // Get playerInfo to know who we are

  // Effect for handling game state updates from the server
  useEffect(() => {
    if (socket) {
      const handleGameStateUpdate = (newState) => {
        console.log('[GameContext] Received game_state_update:', newState);
        dispatch({ type: 'SET_GAME_STATE', payload: newState });
      };

      const handleGameNotification = (notification) => {
        console.log('[GameContext] Received game_notification:', notification);
        dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
        // Optionally show a toast or alert here too
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
      socket.on('auth_socket_response', handleAuthSuccess); // Listen for auth confirmation

      // Cleanup function
      return () => {
        console.log('[GameContext] Cleaning up game listeners...');
        socket.off('game_state_update', handleGameStateUpdate);
        socket.off('game_notification', handleGameNotification);
        socket.off('auth_socket_response', handleAuthSuccess); // Clean up listener
      };
    } else {
      // console.log('[GameContext] Socket not connected, listeners not registered.');
    }
  }, [socket, playerInfo?.id]); // Add playerInfo.id dependency

  // TODO: Add functions to emit game actions (rollDice, buyProperty, etc.)
  // Example:
  // const rollDice = useCallback(() => {
  //   emit('roll_dice', { playerId: authState.user.id }); // Need access to AuthContext
  // }, [emit, authState]);

  return (
    <GameContext.Provider value={{ gameState, dispatch /*, rollDice */ }}>
      {children}
    </GameContext.Provider>
  );
}; 