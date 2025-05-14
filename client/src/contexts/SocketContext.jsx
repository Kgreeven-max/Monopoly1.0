import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';

// Create context with default values
const SocketContext = createContext({
  socket: null,
  isConnected: false,
  connectionError: null,
  reconnectAttempts: 0,
  connectSocket: () => {},
  disconnectSocket: () => {},
  emit: () => false,
  on: () => () => {}
});

// Custom hook to use the socket context
export const useSocket = () => useContext(SocketContext);

// Default socket URL - will be determined at runtime based on tests
let WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:5001';

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
      path: '/ws/socket.io', // Match the path in app.py
      transports: ['websocket', 'polling'], // Try websocket first, fallback to polling
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000, // Increase timeout
      autoConnect: true,
      debug: true, // Enable debug mode
      withCredentials: true, // Send cookies
      query: {
        token: 'display-mode', // Pass a token for display mode
      },
      // Override with any user-provided options
      ...options
    };

    console.log(`[SocketContext] Attempting to connect to websocket server at ${WS_URL} with options:`, finalOptions);
    
    try {
      // Create a new socket connection
      console.log(`[SocketContext] Creating new socket connection to: ${WS_URL}${finalOptions.path}`);
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

  // Automatically connect when the component mounts
  useEffect(() => {
    console.log('[SocketContext] Automatically connecting to socket on mount...');
    
    // Try different connection methods
    const testConnection = async () => {
      // First try the default port 5001
      await testPort('http://localhost:5001');
      
      // Then try port 8080 which is mentioned in app.py and run_server.py
      await testPort('http://localhost:8080');
    };
    
    // Test connections with various paths on a specific port
    const testPort = async (url) => {
      console.log(`[SocketContext] Testing connection to ${url}...`);
      
      // Try with default path
      console.log(`[SocketContext] Testing connection to ${url} with default path /socket.io...`);
      try {
        const testSocket1 = io(url, {
          path: '/socket.io',
          transports: ['websocket', 'polling'],
          timeout: 5000,
          autoConnect: true,
          withCredentials: true
        });
        
        testSocket1.on('connect', () => {
          console.log(`[SocketContext] Test CONNECTED SUCCESSFULLY to ${url} with path /socket.io`);
        });
        
        testSocket1.on('connect_error', (err) => {
          console.error(`[SocketContext] Connection error to ${url} with path /socket.io:`, err.message);
          testSocket1.disconnect();
        });
        
        // Try with /ws path
        console.log(`[SocketContext] Testing connection to ${url} with /ws path...`);
        const testSocket2 = io(url, {
          path: '/ws',
          transports: ['websocket', 'polling'],
          timeout: 5000,
          autoConnect: true,
          withCredentials: true
        });
        
        testSocket2.on('connect', () => {
          console.log(`[SocketContext] Test CONNECTED SUCCESSFULLY to ${url} with path /ws`);
        });
        
        testSocket2.on('connect_error', (err) => {
          console.error(`[SocketContext] Connection error to ${url} with path /ws:`, err.message);
          testSocket2.disconnect();
        });
        
        // Try with /ws/socket.io path
        console.log(`[SocketContext] Testing connection to ${url} with /ws/socket.io path...`);
        const testSocket3 = io(url, {
          path: '/ws/socket.io',
          transports: ['websocket', 'polling'],
          timeout: 5000,
          autoConnect: true,
          withCredentials: true
        });
        
        testSocket3.on('connect', () => {
          console.log(`[SocketContext] Test CONNECTED SUCCESSFULLY to ${url} with path /ws/socket.io`);
        });
        
        testSocket3.on('connect_error', (err) => {
          console.error(`[SocketContext] Connection error to ${url} with path /ws/socket.io:`, err.message);
          testSocket3.disconnect();
        });
      } catch (err) {
        console.error(`[SocketContext] Test socket creation error for ${url}:`, err);
      }
    };
    
    // Run the test
    testConnection();
    
    // Also try normal connection
    connectSocket();
  }, [connectSocket]);

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