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

// Export socket instance and helper functions
export default {
  socket,
  connectSocket,
  disconnectSocket,
  emit: (...args) => socket.emit(...args),
  on: (event, callback) => socket.on(event, callback),
  off: (event, callback) => socket.off(event, callback),
}; 