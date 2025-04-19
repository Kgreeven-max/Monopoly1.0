import { io } from 'socket.io-client';

// Create socket instance
export const socket = io({
  path: '/ws',
  autoConnect: false,
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
});

// Socket connection management
export const connectSocket = (token) => {
  socket.auth = { token };
  socket.connect();
};

export const disconnectSocket = () => {
  socket.disconnect();
};

// Socket event handlers
socket.on('connect', () => {
  console.log('Socket connected');
});

socket.on('disconnect', () => {
  console.log('Socket disconnected');
});

socket.on('connect_error', (error) => {
  console.error('Socket connection error:', error);
});

// Game-specific event handlers
socket.on('game_error', (error) => {
  console.error('Game error:', error);
});

// Property action helpers
const mortgageProperty = (playerId, propertyId, gameId = 1, pin = null) => {
  socket.emit('mortgage_property', { playerId, propertyId, gameId, pin });
};

const unmortgageProperty = (playerId, propertyId, gameId = 1, pin = null) => {
  socket.emit('unmortgage_property', { playerId, propertyId, gameId, pin });
};

const improveProperty = (playerId, propertyId, gameId = 1, improvementType = 'house') => {
  socket.emit('improve_property', { playerId, propertyId, gameId, improvementType });
};

const sellImprovement = (playerId, propertyId, gameId = 1, improvementType = 'house') => {
  socket.emit('sell_improvement', { playerId, propertyId, gameId, improvementType });
};

// Market fluctuation handling
const handleMarketFluctuation = (playerId, gameId = 1) => {
  socket.emit('handle_market_fluctuation', { playerId, gameId });
};

// Export socket instance and helper functions
export default {
  socket,
  connectSocket,
  disconnectSocket,
  emit: (...args) => socket.emit(...args),
  on: (event, callback) => socket.on(event, callback),
  off: (event, callback) => socket.off(event, callback),
  // Property Actions
  mortgageProperty,
  unmortgageProperty,
  improveProperty,
  sellImprovement,
  // Special Space Actions
  handleMarketFluctuation
}; 