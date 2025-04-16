import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';

// Create context
const SocketContext = createContext();

// Custom hook to use the socket context
export const useSocket = () => useContext(SocketContext);

// Ensure the WebSocket URL is configurable, fallback to default
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:5000'; 
// Note: Standard Socket.IO connects to the path specified on the server 
// (often /socket.io/), but we configured Flask-SocketIO path to '/ws'
// We might need to adjust connection options if '/ws' isn't handled automatically.

// Socket provider component
export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Explicit connect function 
  const connectSocket = useCallback(() => {
    // Prevent multiple connections
    if (socket?.connected) return;

    console.log('[SocketContext] Attempting to connect...');
    // Use the WebSocket URL and specify the path if needed
    const newSocket = io(WS_URL, {
      path: '/ws/socket.io', // Path configured in Flask-SocketIO (check app.py)
      transports: ['websocket'], // Prefer WebSocket
      reconnectionAttempts: 5,
      timeout: 10000,
      // Add authentication if needed (e.g., sending token)
      // auth: {
      //   token: localStorage.getItem('token') 
      // }
    });

    newSocket.on('connect', () => {
      console.log('[SocketContext] Connected successfully! SID:', newSocket.id);
      setIsConnected(true);
    });

    newSocket.on('disconnect', (reason) => {
      console.warn('[SocketContext] Disconnected:', reason);
      setIsConnected(false);
      // Handle potential cleanup or reconnection logic here if needed
    });

    newSocket.on('connect_error', (error) => {
      console.error('[SocketContext] Connection Error:', error);
      setIsConnected(false);
      // Maybe retry connection or notify user
    });

    setSocket(newSocket);

  }, []); // Dependency array is now empty

  // Explicit disconnect function
  const disconnectSocket = useCallback(() => {
    if (socket) {
      console.log('[SocketContext] Disconnecting socket...');
      socket.disconnect();
      setSocket(null);
      setIsConnected(false);
    }
  }, []); // Dependency array is now empty

  // Function to emit events safely
  const emitEvent = useCallback((eventName, data, ack) => {
    if (socket && isConnected) {
      console.debug(`[SocketContext] Emitting event '${eventName}':`, data);
      socket.emit(eventName, data, ack);
    } else {
      console.error(`[SocketContext] Cannot emit event '${eventName}'. Socket not connected.`);
    }
  }, [socket, isConnected]);

  // Function to register listeners safely
  const registerListener = useCallback((eventName, callback) => {
    if (socket) {
        console.debug(`[SocketContext] Registering listener for '${eventName}'`);
        socket.on(eventName, callback);
        // Return an unsubscribe function
        return () => {
             console.debug(`[SocketContext] Unregistering listener for '${eventName}'`);
             socket.off(eventName, callback);
        };
    } else {
        console.warn(`[SocketContext] Cannot register listener for '${eventName}'. Socket not initialized.`);
        return () => {}; // Return no-op unsubscribe
    }
  }, [socket]);

  // Cleanup on unmount
  useEffect(() => {
    // Store the current socket instance
    const currentSocket = socket;
    return () => {
      // Use the stored instance in the cleanup
      if (currentSocket) {
          console.log('[SocketContext] Cleaning up socket connection on unmount...');
          currentSocket.disconnect();
      }
    };
    // Ensure cleanup runs only once on unmount
  }, []); // Dependency array is now empty

  const value = {
    socket,
    isConnected,
    connectSocket,
    disconnectSocket,
    emit: emitEvent,
    on: registerListener,
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
}; 