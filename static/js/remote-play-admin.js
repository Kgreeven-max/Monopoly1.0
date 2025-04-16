/**
 * Remote Play Administration Module
 * 
 * Provides functionality for managing Cloudflare Tunnel connections and
 * monitoring remote player connections from the admin interface.
 */

// Create the RemotePlayAdmin module
const RemotePlayAdmin = (function() {
    // Constants
    const API_BASE = '/api/remote';
    const REMOTE_API = API_BASE;
    const REFRESH_INTERVAL = 10000; // 10 seconds
    
    // State variables
    let tunnelStatus = null;
    let connectedPlayers = {};
    let adminKey = null;
    let refreshTimer = null;
    
    /**
     * Initialize the remote play admin module
     * @param {string} key - Admin key for API authentication
     */
    function init(key) {
        adminKey = key;
        
        // Set up event listeners for buttons
        document.getElementById('create-tunnel-btn')?.addEventListener('click', createTunnel);
        document.getElementById('start-tunnel-btn')?.addEventListener('click', startTunnel);
        document.getElementById('stop-tunnel-btn')?.addEventListener('click', stopTunnel);
        document.getElementById('delete-tunnel-btn')?.addEventListener('click', deleteTunnel);
        document.getElementById('save-timeout-btn')?.addEventListener('click', saveTimeout);
        
        // Initialize data
        refreshRemoteStatus();
        refreshConnectedPlayers();
        
        // Set up refresh timer
        refreshTimer = setInterval(() => {
            refreshRemoteStatus();
            refreshConnectedPlayers();
        }, REFRESH_INTERVAL);
        
        console.log('Remote Play Admin Module initialized');
    }
    
    /**
     * Get current tunnel status
     */
    async function refreshRemoteStatus() {
        try {
            const response = await fetch(`${REMOTE_API}/status`, {
                headers: {
                    'X-Admin-Key': adminKey
                }
            });
            if (!response.ok) throw new Error('Failed to fetch remote status');
            
            const data = await response.json();
            updateTunnelStatusUI(data);
            tunnelStatus = data;
        } catch (error) {
            console.error('Error fetching tunnel status:', error);
            showError('Failed to fetch tunnel status');
        }
    }
    
    /**
     * Get connected players information
     */
    async function refreshConnectedPlayers() {
        try {
            const response = await fetch(`${REMOTE_API}/players`, {
                headers: {
                    'X-Admin-Key': adminKey
                }
            });
            if (!response.ok) throw new Error('Failed to fetch connected players');
            
            const data = await response.json();
            updateConnectedPlayersUI(data);
            connectedPlayers = data.players || {};
        } catch (error) {
            console.error('Error fetching connected players:', error);
            showError('Failed to fetch connected players');
        }
    }
    
    /**
     * Create a new Cloudflare Tunnel
     */
    async function createTunnel() {
        try {
            const tunnelName = document.getElementById('tunnel-name-input').value || 'pinopoly';
            
            showLoading('Creating tunnel...');
            
            const response = await fetch(`${REMOTE_API}/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                },
                body: JSON.stringify({ tunnel_name: tunnelName })
            });
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                showSuccess(`Tunnel created: ${data.tunnel_name}`);
                refreshRemoteStatus();
            } else {
                showError(`Failed to create tunnel: ${data.message}`);
            }
        } catch (error) {
            hideLoading();
            console.error('Error creating tunnel:', error);
            showError('Failed to create tunnel');
        }
    }
    
    /**
     * Start the Cloudflare Tunnel
     */
    async function startTunnel() {
        try {
            showLoading('Starting tunnel...');
            
            const response = await fetch(`${REMOTE_API}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                }
            });
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                showSuccess(`Tunnel started: ${data.tunnel_url}`);
                refreshRemoteStatus();
            } else {
                showError(`Failed to start tunnel: ${data.message}`);
            }
        } catch (error) {
            hideLoading();
            console.error('Error starting tunnel:', error);
            showError('Failed to start tunnel');
        }
    }
    
    /**
     * Stop the Cloudflare Tunnel
     */
    async function stopTunnel() {
        try {
            showLoading('Stopping tunnel...');
            
            const response = await fetch(`${REMOTE_API}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                }
            });
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                showSuccess('Tunnel stopped successfully');
                refreshRemoteStatus();
            } else {
                showError(`Failed to stop tunnel: ${data.message}`);
            }
        } catch (error) {
            hideLoading();
            console.error('Error stopping tunnel:', error);
            showError('Failed to stop tunnel');
        }
    }
    
    /**
     * Delete the Cloudflare Tunnel
     */
    async function deleteTunnel() {
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this tunnel? This action cannot be undone.')) {
            return;
        }
        
        try {
            showLoading('Deleting tunnel...');
            
            const response = await fetch(`${REMOTE_API}/delete`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                }
            });
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                showSuccess('Tunnel deleted successfully');
                refreshRemoteStatus();
            } else {
                showError(`Failed to delete tunnel: ${data.message}`);
            }
        } catch (error) {
            hideLoading();
            console.error('Error deleting tunnel:', error);
            showError('Failed to delete tunnel');
        }
    }
    
    /**
     * Save timeout settings
     */
    async function saveTimeout() {
        try {
            const timeout = parseInt(document.getElementById('timeout-input').value || '60');
            
            if (isNaN(timeout) || timeout < 10 || timeout > 300) {
                showError('Timeout must be between 10 and 300 seconds');
                return;
            }
            
            showLoading('Saving timeout...');
            
            const response = await fetch(`${REMOTE_API}/timeout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                },
                body: JSON.stringify({ timeout })
            });
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                showSuccess(`Timeout set to ${timeout} seconds`);
                refreshRemoteStatus();
            } else {
                showError(`Failed to set timeout: ${data.error}`);
            }
        } catch (error) {
            hideLoading();
            console.error('Error saving timeout:', error);
            showError('Failed to save timeout');
        }
    }
    
    /**
     * Ping a player to check connection quality
     * @param {string} playerId - ID of player to ping
     */
    async function pingPlayer(playerId) {
        try {
            // Update UI to show pinging
            const statusElement = document.getElementById(`player-status-${playerId}`);
            if (statusElement) {
                statusElement.textContent = 'Pinging...';
                statusElement.className = 'pinging';
            }
            
            const response = await fetch(`${REMOTE_API}/players/ping/${playerId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                }
            });
            
            const data = await response.json();
            
            if (!data.success) {
                showError(`Failed to ping player: ${data.error}`);
                
                // Reset status display
                if (statusElement) {
                    const playerData = connectedPlayers[playerId];
                    if (playerData) {
                        statusElement.textContent = playerData.connected ? 'Connected' : 'Disconnected';
                        statusElement.className = playerData.connected ? 'status-success' : 'status-error';
                    }
                }
            }
        } catch (error) {
            console.error('Error pinging player:', error);
            showError('Failed to ping player');
        }
    }
    
    /**
     * Remove a player from remote connections
     * @param {string} playerId - ID of player to remove
     */
    async function removePlayer(playerId) {
        // Confirm removal
        if (!confirm('Are you sure you want to remove this player from the remote connections?')) {
            return;
        }
        
        try {
            showLoading('Removing player...');
            
            const response = await fetch(`${REMOTE_API}/players/remove/${playerId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Key': adminKey
                }
            });
            
            const data = await response.json();
            hideLoading();
            
            if (data.success) {
                showSuccess('Player removed successfully');
                refreshConnectedPlayers();
            } else {
                showError(`Failed to remove player: ${data.error}`);
            }
        } catch (error) {
            hideLoading();
            console.error('Error removing player:', error);
            showError('Failed to remove player');
        }
    }
    
    /**
     * Update the tunnel status UI based on server response
     * @param {Object} data - Tunnel status data
     */
    function updateTunnelStatusUI(data) {
        // Update remote enabled status
        const remoteEnabledEl = document.getElementById('remote-enabled');
        if (remoteEnabledEl) {
            if (data.remote_enabled) {
                remoteEnabledEl.textContent = 'Enabled';
                remoteEnabledEl.className = 'status-success';
            } else {
                remoteEnabledEl.textContent = 'Disabled';
                remoteEnabledEl.className = 'status-error';
            }
        }
        
        // Update cloudflared installed status
        const cloudflaredInstalledEl = document.getElementById('cloudflared-installed');
        if (cloudflaredInstalledEl) {
            if (data.cloudflared_installed) {
                cloudflaredInstalledEl.textContent = data.cloudflared_version || 'Installed';
                cloudflaredInstalledEl.className = 'status-success';
            } else {
                cloudflaredInstalledEl.textContent = 'Not Installed';
                cloudflaredInstalledEl.className = 'status-error';
            }
        }
        
        // Update tunnel status
        const tunnelStatusEl = document.getElementById('tunnel-status');
        if (tunnelStatusEl) {
            if (data.running) {
                tunnelStatusEl.textContent = 'Running';
                tunnelStatusEl.className = 'status-success';
            } else if (data.configured) {
                tunnelStatusEl.textContent = 'Configured (Not Running)';
                tunnelStatusEl.className = 'status-warning';
            } else {
                tunnelStatusEl.textContent = 'Not Configured';
                tunnelStatusEl.className = 'status-error';
            }
        }
        
        // Update tunnel URL
        const tunnelUrlEl = document.getElementById('tunnel-url');
        if (tunnelUrlEl) {
            if (data.url) {
                tunnelUrlEl.textContent = data.url;
            } else {
                tunnelUrlEl.textContent = 'N/A';
            }
        }
        
        // Update timeout input
        const timeoutInput = document.getElementById('timeout-input');
        if (timeoutInput && data.timeout) {
            timeoutInput.value = data.timeout;
        }
        
        // Show/hide QR code
        const connectionInfo = document.getElementById('connection-info');
        if (connectionInfo) {
            if (data.running && data.url) {
                connectionInfo.style.display = 'block';
                
                // Generate QR code URL (using server endpoint)
                const qrCode = document.getElementById('qr-code');
                if (qrCode) {
                    qrCode.src = `/api/remote/qr?key=${encodeURIComponent(adminKey)}`;
                }
            } else {
                connectionInfo.style.display = 'none';
            }
        }
        
        // Update UI state based on status
        const createBtn = document.getElementById('create-tunnel-btn');
        const startBtn = document.getElementById('start-tunnel-btn');
        const stopBtn = document.getElementById('stop-tunnel-btn');
        const deleteBtn = document.getElementById('delete-tunnel-btn');
        
        if (createBtn && startBtn && stopBtn && deleteBtn) {
            // Create button is enabled only if cloudflared is installed
            createBtn.disabled = !data.cloudflared_installed || (data.configured && !data.tunnel_name);
            
            // Start button is enabled if tunnel is configured but not running
            startBtn.disabled = !data.cloudflared_installed || !data.configured || data.running;
            
            // Stop button is enabled if tunnel is running
            stopBtn.disabled = !data.cloudflared_installed || !data.running;
            
            // Delete button is enabled if tunnel is configured but not running
            deleteBtn.disabled = !data.cloudflared_installed || !data.configured || data.running;
        }
    }
    
    /**
     * Update the connected players UI based on server response
     * @param {Object} data - Connected players data
     */
    function updateConnectedPlayersUI(data) {
        const players = data.players || {};
        const tableBody = document.getElementById('players-table-body');
        const connectedCount = document.getElementById('connected-count');
        
        if (!tableBody) return;
        
        // Update player count
        if (connectedCount) {
            const count = Object.keys(players).length;
            connectedCount.textContent = count;
        }
        
        // Clear existing rows
        tableBody.innerHTML = '';
        
        // If no players, show message
        if (Object.keys(players).length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6" class="text-center">No players connected</td>';
            tableBody.appendChild(row);
            return;
        }
        
        // Add each player to the table
        for (const [playerId, player] of Object.entries(players)) {
            const row = document.createElement('tr');
            
            // Calculate time since last disconnect
            let disconnectedFor = '';
            if (!player.connected && player.last_disconnect) {
                const disconnectTime = new Date(player.last_disconnect);
                const now = new Date();
                const diffSeconds = Math.floor((now - disconnectTime) / 1000);
                
                if (diffSeconds < 60) {
                    disconnectedFor = `${diffSeconds} seconds`;
                } else if (diffSeconds < 3600) {
                    disconnectedFor = `${Math.floor(diffSeconds / 60)} minutes`;
                } else {
                    disconnectedFor = `${Math.floor(diffSeconds / 3600)} hours`;
                }
            }
            
            // Create row HTML
            row.innerHTML = `
                <td>${player.display_name || player.username}</td>
                <td>
                    <span id="player-status-${playerId}" class="${player.connected ? 'status-success' : 'status-error'}">
                        ${player.connected ? 'Connected' : 'Disconnected'}
                    </span>
                </td>
                <td>${player.last_connect ? new Date(player.last_connect).toLocaleString() : 'N/A'}</td>
                <td>${player.last_disconnect ? new Date(player.last_disconnect).toLocaleString() : 'N/A'}</td>
                <td>${disconnectedFor || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="RemotePlayAdmin.pingPlayer('${playerId}')">Ping</button>
                    <button class="btn btn-sm btn-danger" onclick="RemotePlayAdmin.removePlayer('${playerId}')">Remove</button>
                </td>
            `;
            
            tableBody.appendChild(row);
        }
    }
    
    /**
     * Show loading message
     * @param {string} message - Message to display
     */
    function showLoading(message = 'Loading...') {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.textContent = message;
            loadingEl.style.display = 'block';
        }
    }
    
    /**
     * Hide loading message
     */
    function hideLoading() {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }
    
    /**
     * Show success message
     * @param {string} message - Success message
     */
    function showSuccess(message) {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;
        
        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-success alert-dismissible fade show';
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alertEl);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertEl.classList.remove('show');
            setTimeout(() => alertEl.remove(), 150);
        }, 5000);
    }
    
    /**
     * Show error message
     * @param {string} message - Error message
     */
    function showError(message) {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) return;
        
        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-danger alert-dismissible fade show';
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alertEl);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertEl.classList.remove('show');
            setTimeout(() => alertEl.remove(), 150);
        }, 5000);
    }
    
    /**
     * Handle ping response from a player
     * @param {Object} data - Ping response data
     */
    function handlePingResponse(data) {
        if (!data || !data.player_id) return;
        
        const statusElement = document.getElementById(`player-status-${data.player_id}`);
        if (statusElement) {
            statusElement.textContent = `Connected (${data.latency}ms)`;
            statusElement.className = 'status-success';
            
            // Reset back to normal status after 5 seconds
            setTimeout(() => {
                if (connectedPlayers[data.player_id]?.connected) {
                    statusElement.textContent = 'Connected';
                }
            }, 5000);
        }
    }
    
    /**
     * Set up socket event handlers for remote play events
     * @param {Object} socket - Socket.IO socket instance
     */
    function setupSocketHandlers(socket) {
        // Player connected event
        socket.on('player_connected', (data) => {
            console.log('Player connected:', data);
            refreshConnectedPlayers();
        });
        
        // Player disconnected event
        socket.on('player_disconnected', (data) => {
            console.log('Player disconnected:', data);
            refreshConnectedPlayers();
        });
        
        // Player reconnected event
        socket.on('player_reconnected', (data) => {
            console.log('Player reconnected:', data);
            refreshConnectedPlayers();
        });
        
        // Player timed out event
        socket.on('player_timed_out', (data) => {
            console.log('Player timed out:', data);
            refreshConnectedPlayers();
        });
        
        // Ping response
        socket.on('ping_response', (data) => {
            console.log('Ping response:', data);
            handlePingResponse(data);
        });
    }
    
    // Return public methods and properties
    return {
        init: init,
        refreshRemoteStatus: refreshRemoteStatus,
        refreshConnectedPlayers: refreshConnectedPlayers,
        pingPlayer: pingPlayer,
        removePlayer: removePlayer,
        setupSocketHandlers: setupSocketHandlers
    };
})(); 