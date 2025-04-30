import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';

// Create context
const SocketContext = createContext();

// Custom hook to use the socket context
export const useSocket = () => useContext(SocketContext);

// Use port 8080 for WebSocket connection
const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8080';

// Socket provider component
export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  
  // Use refs to keep track of the current socket instance
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const maxReconnectAttempts = 10;

  // Explicit connect function with configurable options
  const connectSocket = useCallback((options = {}) => {
    // Prevent multiple connections or if already connected
    if (socketRef.current?.connected) {
      console.log('[SocketContext] Already connected, skipping connection request');
      return socketRef.current;
    }
    
    // Clear any previous reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Allow direct override of connection options
    const finalOptions = {
      // Default options
      path: '/ws/socket.io', // Path configured in Flask-SocketIO
      transports: ['websocket', 'polling'], // Try websocket first, fallback to polling
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000, // Increase timeout
      // Override with any user-provided options
      ...options
    };

    console.log(`[SocketContext] Attempting to connect to websocket server at ${WS_URL} with options:`, finalOptions);
    
    try {
      // Create a new socket connection
      const newSocket = io(WS_URL, finalOptions);
      socketRef.current = newSocket;

      // Setup event handlers
      newSocket.on('connect', () => {
        console.log('[SocketContext] Connected successfully! SID:', newSocket.id);
        setIsConnected(true);
        setConnectionError(null);
        setReconnectAttempts(0);
      });

      newSocket.on('disconnect', (reason) => {
        console.warn('[SocketContext] Disconnected:', reason);
        setIsConnected(false);
        
        // Handle reconnection for specific disconnect reasons
        if (reason === 'io server disconnect' || reason === 'io client disconnect') {
          // Server/client explicitly closed the connection, don't reconnect automatically
          console.log('[SocketContext] Server or client explicitly closed the connection');
        }
      });

      newSocket.on('connect_error', (error) => {
        console.error('[SocketContext] Connection Error:', error);
        setIsConnected(false);
        setConnectionError(error.message || 'Connection failed');
        
        // Track reconnection attempts
        setReconnectAttempts(prev => {
          const newAttempts = prev + 1;
          console.log(`[SocketContext] Reconnect attempt ${newAttempts}/${maxReconnectAttempts}`);
          
          // If we've exceeded max attempts, stop trying
          if (newAttempts >= maxReconnectAttempts) {
            console.error('[SocketContext] Max reconnect attempts reached');
            newSocket.disconnect();
          }
          
          return newAttempts;
        });
      });

      // Handle reconnecting events
      newSocket.on('reconnecting', (attemptNumber) => {
        console.log(`[SocketContext] Attempting to reconnect. Attempt: ${attemptNumber}`);
      });

      newSocket.on('reconnect', (attemptNumber) => {
        console.log(`[SocketContext] Reconnected successfully after ${attemptNumber} attempts`);
        setIsConnected(true);
        setConnectionError(null);
        setReconnectAttempts(0);
      });

      newSocket.on('reconnect_error', (error) => {
        console.error('[SocketContext] Reconnection error:', error);
        setConnectionError(`Reconnection error: ${error.message || 'Connection failed'}`);
      });

      newSocket.on('reconnect_failed', () => {
        console.error('[SocketContext] Failed to reconnect after all attempts');
        setConnectionError('Failed to reconnect after multiple attempts. Please try again later.');
      });

      setSocket(newSocket);
      return newSocket;
    } catch (error) {
      console.error('[SocketContext] Error creating socket connection:', error);
      setConnectionError(`Failed to create socket: ${error.message}`);
      return null;
    }
  }, []); 

  // Explicit disconnect function
  const disconnectSocket = useCallback(() => {
    if (socketRef.current) {
      console.log('[SocketContext] Disconnecting socket...');
      socketRef.current.disconnect();
      socketRef.current = null;
      setSocket(null);
      setIsConnected(false);
      
      // Clear any pending reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    }
  }, []); 

  // Function to emit events safely
  const emitEvent = useCallback((eventName, data, ack) => {
    if (socketRef.current && isConnected) {
      console.debug(`[SocketContext] Emitting event '${eventName}':`, data);
      socketRef.current.emit(eventName, data, ack);
      return true;
    } else {
      console.warn(`[SocketContext] Cannot emit event '${eventName}'. Socket not connected.`);
      // Attempt to reconnect if not connected
      if (!isConnected && !reconnectTimeoutRef.current) {
        console.log('[SocketContext] Attempting to reconnect before emitting...');
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectTimeoutRef.current = null;
          if (!isConnected) {
            connectSocket();
          }
        }, 500);
      }
      return false;
    }
  }, [isConnected, connectSocket]);

  // Function to register listeners safely
  const registerListener = useCallback((eventName, callback) => {
    if (socketRef.current) {
      console.debug(`[SocketContext] Registering listener for '${eventName}'`);
      socketRef.current.on(eventName, callback);
      // Return an unsubscribe function
      return () => {
        console.debug(`[SocketContext] Unregistering listener for '${eventName}'`);
        if (socketRef.current) {
          socketRef.current.off(eventName, callback);
        }
      };
    } else {
      console.warn(`[SocketContext] Cannot register listener for '${eventName}'. Socket not initialized.`);
      return () => {}; // Return no-op unsubscribe
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Use the stored instance in the cleanup
      if (socketRef.current) {
        console.log('[SocketContext] Cleaning up socket connection on unmount...');
        socketRef.current.disconnect();
        socketRef.current = null;
      }
      
      // Clear any pending reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, []);

  // Expose socket context values
  const value = {
    socket: socketRef.current, // Use the ref for the current socket
    isConnected,
    connectionError,
    reconnectAttempts,
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