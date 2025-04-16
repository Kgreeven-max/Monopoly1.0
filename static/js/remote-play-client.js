/**
 * Remote Play Client Module
 * 
 * Manages the connection between remote players and the Pi-nopoly game server.
 * Handles reconnection, ping, and player state management.
 */
const RemotePlayClient = (function() {
    // Configuration
    const PING_INTERVAL = 30000; // Ping every 30 seconds
    const RECONNECT_TIMEOUT = 60; // Default reconnect timeout
    
    // State variables
    let socket = null;
    let playerPin = null;
    let playerName = null;
    let isConnected = false;
    let pingTimer = null;
    let reconnectTimer = null;
    let reconnectTimeRemaining = 0;
    let reconnectInterval = null;
    
    /**
     * Initialize the remote play client
     */
    function init() {
        setupEventListeners();
        
        // Attempt to auto-connect if we have saved credentials and were previously connected
        if (localStorage.getItem('pinopolyAutoConnect') === 'true' && 
            localStorage.getItem('pinopolyPin')) {
            connectToGame(
                localStorage.getItem('pinopolyPin'),
                localStorage.getItem('pinopolyName') || ''
            );
        }
    }
    
    /**
     * Set up all event listeners for the connection page
     */
    function setupEventListeners() {
        // Connect button
        const connectBtn = document.getElementById('connect-btn');
        if (connectBtn) {
            connectBtn.addEventListener('click', function() {
                const pin = document.getElementById('pin-input').value.trim();
                const name = document.getElementById('name-input').value.trim();
                
                if (pin.length === 0) {
                    showError('Please enter your PIN to connect.');
                    return;
                }
                
                connectToGame(pin, name);
            });
        }
        
        // Disconnect button
        const disconnectBtn = document.getElementById('disconnect-btn');
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', function() {
                disconnectFromGame();
            });
        }
        
        // Ping button
        const pingBtn = document.getElementById('ping-btn');
        if (pingBtn) {
            pingBtn.addEventListener('click', function() {
                pingServer();
            });
        }
        
        // PIN input - allow enter key
        const pinInput = document.getElementById('pin-input');
        if (pinInput) {
            pinInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    connectBtn.click();
                }
            });
            
            // Only allow numbers in PIN input
            pinInput.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9]/g, '');
            });
        }
        
        // Save connection checkbox
        const saveConnection = document.getElementById('save-connection');
        if (saveConnection) {
            saveConnection.addEventListener('change', function() {
                localStorage.setItem('pinopolySaveConnection', this.checked);
                
                // If unchecked, remove stored credentials
                if (!this.checked) {
                    localStorage.removeItem('pinopolyPin');
                    localStorage.removeItem('pinopolyName');
                    localStorage.removeItem('pinopolyAutoConnect');
                }
            });
        }
    }
    
    /**
     * Connect to the game server
     * @param {string} pin Player's PIN
     * @param {string} name Player's name (optional)
     */
    function connectToGame(pin, name = '') {
        // Show loading state
        document.getElementById('connect-btn').disabled = true;
        document.getElementById('connect-btn').textContent = 'Connecting...';
        hideError();
        
        // Save credentials if requested
        const saveConnection = document.getElementById('save-connection').checked;
        if (saveConnection) {
            localStorage.setItem('pinopolyPin', pin);
            localStorage.setItem('pinopolyName', name);
            localStorage.setItem('pinopolySaveConnection', 'true');
        }
        
        // Store connection info
        playerPin = pin;
        playerName = name || 'Player ' + pin;
        
        // Create socket connection
        if (!socket) {
            socket = io({
                query: {
                    pin: pin,
                    name: name,
                    client: 'remote'
                }
            });
            
            // Set up socket event handlers
            setupSocketHandlers();
        } else {
            // Re-establish connection with new credentials
            socket.io.opts.query = {
                pin: pin,
                name: name,
                client: 'remote'
            };
            socket.connect();
        }
    }
    
    /**
     * Set up all socket event handlers
     */
    function setupSocketHandlers() {
        // Connection successful
        socket.on('connect', function() {
            console.log('Connected to server');
            isConnected = true;
            updateConnectionStatus('connected');
            
            // Switch to player view
            switchToPlayerView();
            
            // Start periodic ping
            startPingTimer();
            
            // Reset reconnect timer if it was running
            clearReconnectTimer();
            hideReconnectingView();
            
            // Set auto-connect flag
            localStorage.setItem('pinopolyAutoConnect', 'true');
        });
        
        // Disconnection
        socket.on('disconnect', function() {
            console.log('Disconnected from server');
            isConnected = false;
            updateConnectionStatus('disconnected');
            
            // Stop ping timer
            clearTimeout(pingTimer);
            
            // Show reconnecting view with timer
            startReconnectTimer();
        });
        
        // Connection error
        socket.on('connect_error', function(error) {
            console.error('Connection error:', error);
            showError('Unable to connect: ' + (error.message || 'Unknown error'));
            
            // Reset button state
            document.getElementById('connect-btn').disabled = false;
            document.getElementById('connect-btn').textContent = 'Connect to Game';
        });
        
        // Authentication error
        socket.on('auth_error', function(msg) {
            console.error('Authentication error:', msg);
            showError(msg);
            disconnectFromGame();
            
            // Reset auto-connect flag
            localStorage.removeItem('pinopolyAutoConnect');
        });
        
        // Ping response
        socket.on('pong', function(data) {
            const latency = Date.now() - data.ts;
            displayPingResult(latency);
        });
        
        // Game state updates
        socket.on('game_state', function(data) {
            console.log('Game state update:', data);
            // Handle game state updates here
        });
        
        // Player status updates
        socket.on('player_status', function(data) {
            console.log('Player status update:', data);
            
            if (data && data.pin === playerPin) {
                updatePlayerStatus(data);
            }
        });
        
        // Reconnect timeout updates
        socket.on('reconnect_settings', function(data) {
            if (data && data.timeout) {
                reconnectTimeRemaining = data.timeout;
            }
        });
    }
    
    /**
     * Disconnect from the game server
     */
    function disconnectFromGame() {
        if (socket) {
            socket.disconnect();
        }
        
        isConnected = false;
        updateConnectionStatus('disconnected');
        
        // Reset UI
        document.getElementById('connect-form').style.display = 'block';
        document.getElementById('player-view').style.display = 'none';
        document.getElementById('connect-btn').disabled = false;
        document.getElementById('connect-btn').textContent = 'Connect to Game';
        
        // Clear timers
        clearTimeout(pingTimer);
        clearReconnectTimer();
        
        // Reset auto-connect flag
        localStorage.removeItem('pinopolyAutoConnect');
    }
    
    /**
     * Ping the server to check connection quality
     */
    function pingServer() {
        if (!isConnected || !socket) {
            return;
        }
        
        // Send ping with timestamp
        socket.emit('ping', { ts: Date.now() });
        
        // Show that we're waiting for response
        const pingResult = document.getElementById('ping-result');
        pingResult.style.display = 'block';
        document.getElementById('ping-time').textContent = 'Waiting...';
    }
    
    /**
     * Display ping result
     * @param {number} latency Ping latency in milliseconds
     */
    function displayPingResult(latency) {
        const pingResult = document.getElementById('ping-result');
        const pingTime = document.getElementById('ping-time');
        
        pingResult.style.display = 'block';
        pingTime.textContent = latency;
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            pingResult.style.display = 'none';
        }, 5000);
    }
    
    /**
     * Start a timer to periodically ping the server
     */
    function startPingTimer() {
        clearTimeout(pingTimer);
        
        // Set up periodic ping
        pingTimer = setInterval(function() {
            if (isConnected && socket) {
                // Silent ping for connection health check
                socket.emit('ping', { ts: Date.now(), silent: true });
            }
        }, PING_INTERVAL);
    }
    
    /**
     * Update the connection status indicator
     * @param {string} status Connection status (connected, connecting, disconnected)
     */
    function updateConnectionStatus(status) {
        const statusBadge = document.getElementById('connection-status');
        if (!statusBadge) return;
        
        statusBadge.className = 'badge ms-auto status-badge ' + status;
        
        switch (status) {
            case 'connected':
                statusBadge.textContent = 'Connected';
                break;
            case 'connecting':
                statusBadge.textContent = 'Connecting...';
                break;
            case 'disconnected':
                statusBadge.textContent = 'Disconnected';
                break;
            default:
                statusBadge.textContent = status;
        }
    }
    
    /**
     * Switch to the player view after successful connection
     */
    function switchToPlayerView() {
        document.getElementById('connect-form').style.display = 'none';
        document.getElementById('player-view').style.display = 'block';
        document.getElementById('player-name').textContent = playerName + ' (' + playerPin + ')';
    }
    
    /**
     * Update player status information
     * @param {Object} data Player status data
     */
    function updatePlayerStatus(data) {
        const playerStatus = document.getElementById('player-status');
        if (!playerStatus) return;
        
        if (data.status) {
            playerStatus.textContent = data.status;
        }
    }
    
    /**
     * Show error message
     * @param {string} message Error message to display
     */
    function showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
    
    /**
     * Hide error message
     */
    function hideError() {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }
    
    /**
     * Start the reconnect timer when disconnected
     */
    function startReconnectTimer() {
        // Show reconnecting view
        document.getElementById('reconnecting-view').style.display = 'block';
        
        // Set initial time remaining (use server-provided value or default)
        reconnectTimeRemaining = reconnectTimeRemaining || RECONNECT_TIMEOUT;
        
        // Update timer display
        updateReconnectTimer();
        
        // Start countdown
        reconnectInterval = setInterval(function() {
            reconnectTimeRemaining--;
            updateReconnectTimer();
            
            if (reconnectTimeRemaining <= 0) {
                clearReconnectTimer();
                disconnectFromGame();
            }
        }, 1000);
    }
    
    /**
     * Update the reconnect timer display
     */
    function updateReconnectTimer() {
        const timerElement = document.getElementById('reconnect-timer');
        if (timerElement) {
            timerElement.textContent = reconnectTimeRemaining;
        }
        
        // Update progress bar
        const progressBar = document.getElementById('reconnect-progress');
        if (progressBar) {
            const percentage = (reconnectTimeRemaining / RECONNECT_TIMEOUT) * 100;
            progressBar.style.width = percentage + '%';
        }
    }
    
    /**
     * Clear the reconnect timer
     */
    function clearReconnectTimer() {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
    
    /**
     * Hide the reconnecting view
     */
    function hideReconnectingView() {
        document.getElementById('reconnecting-view').style.display = 'none';
    }
    
    // Public API
    return {
        init: init,
        connect: connectToGame,
        disconnect: disconnectFromGame,
        ping: pingServer
    };
})(); 