// Admin Dashboard JavaScript

// Store admin key from login/auth
let adminKey = localStorage.getItem('adminKey') || '';

// System Status Management
function fetchSystemStatus() {
    return fetch('/api/admin/system-status', {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        updateSystemStatusUI(data);
        return data;
    })
    .catch(error => {
        console.error('Error fetching system status:', error);
        showErrorNotification('Failed to fetch system status');
        return null;
    });
}

function updateSystemStatusUI(statusData) {
    // Update dashboard statistics
    if (statusData) {
        // Game Info
        document.getElementById('game-status').textContent = statusData.game_info.game_status || 'Unknown';
        document.getElementById('game-current-player').textContent = statusData.game_info.current_player || 'None';
        document.getElementById('game-turn-count').textContent = statusData.game_info.turn_count || '0';
        document.getElementById('game-mode').textContent = statusData.game_info.current_game_mode || 'Standard';
        
        // Player Stats
        document.getElementById('active-players-count').textContent = statusData.player_stats.active_players || '0';
        document.getElementById('human-players-count').textContent = statusData.player_stats.human_players || '0';
        document.getElementById('bot-players-count').textContent = statusData.player_stats.bot_players || '0';
        
        // Property Stats
        document.getElementById('total-properties').textContent = statusData.property_stats.total_properties || '0';
        document.getElementById('owned-properties').textContent = statusData.property_stats.owned_properties || '0';
        document.getElementById('bank-properties').textContent = statusData.property_stats.bank_properties || '0';
        
        // Financial Stats
        document.getElementById('total-money').textContent = statusData.financial_stats.total_player_cash || '0';
        document.getElementById('interest-rate').textContent = `${(statusData.financial_stats.interest_rate_base * 100).toFixed(2)}%` || '5.00%';
        
        // Connection Stats
        document.getElementById('player-connections').textContent = statusData.connection_status.connected_players || '0';
        
        // Remote Play
        const remoteStatus = document.getElementById('remote-play-status');
        if (statusData.remote_play.enabled) {
            if (statusData.remote_play.active) {
                remoteStatus.textContent = 'Active';
                remoteStatus.classList.add('text-success');
                if (statusData.remote_play.connection_url) {
                    document.getElementById('connection-url').textContent = statusData.remote_play.connection_url;
                }
            } else {
                remoteStatus.textContent = 'Enabled (Not Active)';
                remoteStatus.classList.add('text-warning');
            }
        } else {
            remoteStatus.textContent = 'Disabled';
            remoteStatus.classList.add('text-danger');
        }
    }
}

// Game Management
function startGame() {
    fetch('/api/game/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showSuccessNotification('Game started successfully');
            fetchSystemStatus(); // Refresh status
        } else {
            showErrorNotification(`Failed to start game: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error starting game:', error);
        showErrorNotification('Failed to start game');
    });
}

function pauseGame() {
    fetch('/api/admin/modify-state', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify({
            state_changes: {
                turn_phase: 'paused'
            },
            reason: 'Admin paused game'
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showSuccessNotification('Game paused successfully');
            fetchSystemStatus(); // Refresh status
        } else {
            showErrorNotification(`Failed to pause game: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error pausing game:', error);
        showErrorNotification('Failed to pause game');
    });
}

function resetGame() {
    if (confirm('Are you sure you want to reset the game? This will remove all players and properties!')) {
        fetch('/api/admin/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': adminKey
            }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showSuccessNotification('Game reset successfully');
                fetchSystemStatus(); // Refresh status
                fetchAllPlayers(); // Refresh player list
                fetchProperties(); // Refresh properties
            } else {
                showErrorNotification(`Failed to reset game: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error resetting game:', error);
            showErrorNotification('Failed to reset game');
        });
    }
}

function saveGameSettings() {
    const startingMoney = document.getElementById('starting-money').value;
    const turnTimeout = document.getElementById('turn-timeout').value;
    const freeParkingJackpot = document.getElementById('free-parking-jackpot').checked;
    const doubleOnGo = document.getElementById('salary-on-go').checked;
    
    fetch('/api/admin/modify-state', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify({
            state_changes: {
                starting_money: parseInt(startingMoney),
                turn_timeout: parseInt(turnTimeout),
                free_parking_jackpot: freeParkingJackpot,
                double_on_go: doubleOnGo
            },
            reason: 'Admin updated game settings'
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showSuccessNotification('Game settings saved successfully');
            fetchSystemStatus(); // Refresh status
        } else {
            showErrorNotification(`Failed to save game settings: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error saving game settings:', error);
        showErrorNotification('Failed to save game settings');
    });
}

// Player Management
function fetchAllPlayers() {
    fetch('/api/get-all-players', {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.players) {
            updatePlayersTable(data.players);
        } else {
            showErrorNotification('Failed to retrieve players');
        }
    })
    .catch(error => {
        console.error('Error fetching players:', error);
        showErrorNotification('Failed to fetch players');
    });
}

function updatePlayersTable(players) {
    const tableBody = document.getElementById('players-table-body');
    tableBody.innerHTML = '';
    
    if (players.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" class="text-center">No players found</td>`;
        tableBody.appendChild(row);
        return;
    }
    
    players.forEach(player => {
        // Safely get player money/cash value, defaulting to 0 if neither exists
        const playerMoney = player.money !== undefined ? player.money : 
                           (player.cash !== undefined ? player.cash : 0);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${player.username}</td>
            <td>$${playerMoney}</td>
            <td>${player.position}</td>
            <td>${player.properties ? player.properties.length : 0}</td>
            <td>${player.in_game ? (player.is_bot ? 'Bot (Active)' : 'Human (Active)') : 'Inactive'}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-primary" onclick="viewPlayerDetails(${player.id})">View</button>
                    <button class="btn btn-warning" onclick="openAdjustCashModal(${player.id}, '${player.username}')">Adjust $</button>
                    <button class="btn btn-info" onclick="auditPlayer(${player.id})">Audit</button>
                    <button class="btn btn-danger" onclick="removePlayer(${player.id}, '${player.username}')">Remove</button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function viewPlayerDetails(playerId) {
    fetch(`/api/admin/players/${playerId}`, {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.player) {
            openPlayerDetailsModal(data);
        } else {
            showErrorNotification(`Failed to retrieve player details: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error fetching player details:', error);
        showErrorNotification('Failed to fetch player details');
    });
}

function auditPlayer(playerId) {
    fetch(`/api/admin/players/audit/${playerId}`, {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.financial_summary) {
            openPlayerAuditModal(data);
        } else {
            showErrorNotification(`Failed to audit player: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error auditing player:', error);
        showErrorNotification('Failed to audit player');
    });
}

function openPlayerAuditModal(auditData) {
    // Create and show modal with audit results
    const modalContent = `
        <div class="modal-header">
            <h5 class="modal-title">Audit Results: ${auditData.username}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
            <h6>Financial Summary</h6>
            <table class="table table-sm">
                <tr><td>Cash:</td><td>$${auditData.financial_summary.cash}</td></tr>
                <tr><td>Property Count:</td><td>${auditData.financial_summary.property_count}</td></tr>
                <tr><td>Property Value:</td><td>$${auditData.financial_summary.property_value}</td></tr>
                <tr><td>Development Value:</td><td>$${auditData.financial_summary.development_value}</td></tr>
                <tr><td>Total Debt:</td><td>$${auditData.financial_summary.total_debt}</td></tr>
                <tr><td>Net Worth:</td><td>$${auditData.financial_summary.net_worth}</td></tr>
                <tr><td>Cash Flow:</td><td>$${auditData.financial_summary.cash_flow}</td></tr>
            </table>
            
            ${auditData.discrepancies && auditData.discrepancies.length > 0 ? `
                <div class="alert alert-warning">
                    <h6>Discrepancies Found</h6>
                    <ul>
                        ${auditData.discrepancies.map(d => `<li>${d}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
        <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
    `;
    
    const modalElement = document.getElementById('dynamic-modal');
    modalElement.querySelector('.modal-content').innerHTML = modalContent;
    
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

function openAdjustCashModal(playerId, playerName) {
    document.getElementById('money-player-id').value = playerId;
    document.getElementById('money-player-name').textContent = playerName;
    
    const modal = new bootstrap.Modal(document.getElementById('adjust-cash-modal'));
    modal.show();
}

function adjustPlayerCash() {
    const playerId = document.getElementById('money-player-id').value;
    const amount = parseInt(document.getElementById('money-amount').value);
    const reason = document.getElementById('money-reason').value;
    
    if (!playerId || isNaN(amount) || !reason) {
        showErrorNotification('Please complete all fields');
        return;
    }
    
    fetch('/api/admin/players/modify-cash', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify({
            player_id: parseInt(playerId),
            amount: amount,
            reason: reason
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showSuccessNotification(`Player cash adjusted from $${data.previous_cash} to $${data.current_cash}`);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('adjust-cash-modal'));
            modal.hide();
            
            // Reset form
            document.getElementById('adjust-cash-form').reset();
            
            // Refresh player list
            fetchAllPlayers();
        } else {
            showErrorNotification(`Failed to adjust player cash: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error adjusting player cash:', error);
        showErrorNotification('Failed to adjust player cash');
    });
}

function removePlayer(playerId, playerName) {
    if (confirm(`Are you sure you want to remove ${playerName} from the game?`)) {
        fetch('/api/admin/players/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': adminKey
            },
            body: JSON.stringify({
                player_id: playerId,
                handle_properties: 'bank',
                reason: 'Admin removal'
            })
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showSuccessNotification(`Player ${data.username} removed successfully`);
                fetchAllPlayers(); // Refresh player list
                fetchSystemStatus(); // Refresh status
            } else {
                showErrorNotification(`Failed to remove player: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error removing player:', error);
            showErrorNotification('Failed to remove player');
        });
    }
}

function resetAllPlayers() {
    if (confirm('Are you sure you want to reset all players? This will remove all players from the game!')) {
        fetch('/api/socket/reset_all_players', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': adminKey
            }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showSuccessNotification('All players reset successfully');
                fetchAllPlayers(); // Refresh player list
                fetchSystemStatus(); // Refresh status
            } else {
                showErrorNotification(`Failed to reset players: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error resetting players:', error);
            showErrorNotification('Failed to reset players');
        });
    }
}

// Property Management
function fetchProperties() {
    fetch('/api/admin/properties', {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.properties) {
            updatePropertiesTable(data.properties);
        } else {
            showErrorNotification('Failed to retrieve properties');
        }
    })
    .catch(error => {
        console.error('Error fetching properties:', error);
        showErrorNotification('Failed to fetch properties');
    });
}

function updatePropertiesTable(properties) {
    const tableBody = document.getElementById('properties-table-body');
    tableBody.innerHTML = '';
    
    if (properties.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="9" class="text-center">No properties found</td>`;
        tableBody.appendChild(row);
        return;
    }
    
    properties.forEach(property => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${property.id}</td>
            <td>${property.name}</td>
            <td>${property.owner_name || 'Bank'}</td>
            <td>${property.houses || 0}</td>
            <td>${property.hotel ? 'Yes' : 'No'}</td>
            <td>${property.is_mortgaged ? 'Yes' : 'No'}</td>
            <td>$${property.price}</td>
            <td>$${property.current_rent || property.rent}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-info" onclick="viewPropertyDetails(${property.id})">View</button>
                    <button class="btn btn-warning" onclick="openTransferPropertyModal(${property.id}, '${property.name}')">Transfer</button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function viewPropertyDetails(propertyId) {
    fetch(`/api/admin/properties/${propertyId}`, {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.property) {
            openPropertyDetailsModal(data.property);
        } else {
            showErrorNotification(`Failed to retrieve property details: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error fetching property details:', error);
        showErrorNotification('Failed to fetch property details');
    });
}

function openTransferPropertyModal(propertyId, propertyName) {
    document.getElementById('transfer-property-id').value = propertyId;
    document.getElementById('transfer-property-name').textContent = propertyName;
    
    // Clear and populate player dropdowns
    const fromPlayerSelect = document.getElementById('transfer-from-player');
    const toPlayerSelect = document.getElementById('transfer-to-player');
    
    // Reset options
    fromPlayerSelect.innerHTML = '<option value="">Select Source</option><option value="null">Bank</option>';
    toPlayerSelect.innerHTML = '<option value="">Select Destination</option><option value="null">Bank</option>';
    
    // Fetch players to populate dropdowns
    fetch('/api/get-all-players', {
        method: 'GET',
        headers: {
            'X-Admin-Key': adminKey
        }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.players) {
            data.players.forEach(player => {
                if (player.in_game) {
                    const fromOption = document.createElement('option');
                    fromOption.value = player.id;
                    fromOption.textContent = player.username;
                    fromPlayerSelect.appendChild(fromOption);
                    
                    const toOption = document.createElement('option');
                    toOption.value = player.id;
                    toOption.textContent = player.username;
                    toPlayerSelect.appendChild(toOption);
                }
            });
        }
    })
    .catch(error => {
        console.error('Error fetching players for transfer:', error);
    });
    
    const modal = new bootstrap.Modal(document.getElementById('transfer-property-modal'));
    modal.show();
}

function transferProperty() {
    const propertyId = document.getElementById('transfer-property-id').value;
    const fromPlayerId = document.getElementById('transfer-from-player').value;
    const toPlayerId = document.getElementById('transfer-to-player').value;
    const reason = document.getElementById('transfer-reason').value;
    
    if (!propertyId || !fromPlayerId || !toPlayerId || !reason) {
        showErrorNotification('Please complete all fields');
        return;
    }
    
    // Convert "null" string to actual null for the API
    const fromPlayerIdValue = fromPlayerId === "null" ? null : parseInt(fromPlayerId);
    const toPlayerIdValue = toPlayerId === "null" ? null : parseInt(toPlayerId);
    
    fetch('/api/admin/players/transfer-property', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify({
            property_id: parseInt(propertyId),
            from_player_id: fromPlayerIdValue,
            to_player_id: toPlayerIdValue,
            reason: reason
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showSuccessNotification(`Property ${data.property_name} transferred successfully`);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('transfer-property-modal'));
            modal.hide();
            
            // Reset form
            document.getElementById('transfer-property-form').reset();
            
            // Refresh property list
            fetchProperties();
        } else {
            showErrorNotification(`Failed to transfer property: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error transferring property:', error);
        showErrorNotification('Failed to transfer property');
    });
}

// Bot Management
function addBot() {
    const botName = document.getElementById('bot-name').value;
    const botType = document.getElementById('bot-type').value;
    
    if (!botName || !botType) {
        showErrorNotification('Please complete all fields');
        return;
    }
    
    fetch('/api/admin/bots/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey
        },
        body: JSON.stringify({
            bot_name: botName,
            bot_type: botType
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showSuccessNotification(`Bot ${data.bot_name} created successfully`);
            
            // Reset form
            document.getElementById('add-bot-form').reset();
            
            // Refresh player list to show new bot
            fetchAllPlayers();
            fetchSystemStatus();
        } else {
            showErrorNotification(`Failed to create bot: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error creating bot:', error);
        showErrorNotification('Failed to create bot');
    });
}

// Utility Functions
function showSuccessNotification(message) {
    // Implementation depends on your notification system
    // This is a simple implementation using alert
    alert('Success: ' + message);
}

function showErrorNotification(message) {
    // Implementation depends on your notification system
    // This is a simple implementation using alert
    alert('Error: ' + message);
}

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check for admin key
    adminKey = localStorage.getItem('adminKey') || '';
    if (!adminKey) {
        // Prompt for admin key if not set
        adminKey = prompt('Please enter admin key:');
        if (adminKey) {
            localStorage.setItem('adminKey', adminKey);
        } else {
            alert('Admin key required for access');
            window.location.href = '/';
            return;
        }
    }
    
    // Initial data load
    fetchSystemStatus();
    fetchAllPlayers();
    fetchProperties();
    
    // Set up event listeners for the forms
    document.getElementById('game-settings-form').addEventListener('submit', function(event) {
        event.preventDefault();
        saveGameSettings();
    });
    
    document.getElementById('adjust-cash-form').addEventListener('submit', function(event) {
        event.preventDefault();
        adjustPlayerCash();
    });
    
    document.getElementById('transfer-property-form').addEventListener('submit', function(event) {
        event.preventDefault();
        transferProperty();
    });
    
    document.getElementById('add-bot-form').addEventListener('submit', function(event) {
        event.preventDefault();
        addBot();
    });
    
    // Set up refresh interval for status
    setInterval(fetchSystemStatus, 10000); // Refresh every 10 seconds
});

// Create a function to handle finance tab initialization
function initializeFinanceTab() {
    console.log('Initializing finance tab...');
    refreshFinancialOverview();
    refreshLoans();
    refreshTransactions();
}

// Add a function to retry fetching financial data
function refreshFinancialOverview(retryCount = 0) {
    console.log('Refreshing financial overview...');
    const maxRetries = 3;
    
    fetch('/api/admin/finance/overview', {
        method: 'GET',
        headers: {
            'X-Admin-Key': window.adminKey
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update financial stats
            const statsElement = safeGetElement('finance-stats');
            if (statsElement) {
                // Check if stats exists before trying to access properties
                const stats = data.stats || {};
                
                let statsHtml = `
                    <table class="table">
                        <tr><th>Total Money in Game:</th><td>$${stats.total_money || 0}</td></tr>
                        <tr><th>Bank Reserves:</th><td>$${stats.bank_reserves || 0}</td></tr>
                        <tr><th>Player Holdings:</th><td>$${stats.player_holdings || 0}</td></tr>
                        <tr><th>Community Fund:</th><td>$${stats.community_fund || 0}</td></tr>
                        <tr><th>Total Active Loans:</th><td>$${stats.loans_total || 0}</td></tr>
                    </table>
                `;
                statsElement.innerHTML = statsHtml;
            }
            
            // Update interest rates
            const ratesElement = safeGetElement('interest-rates');
            if (ratesElement) {
                // Check if rates exists before trying to access properties
                const rates = data.rates || {};
                
                if (rates && rates.rates) {
                    let ratesHtml = `
                        <p><strong>Economic State:</strong> ${loadFinancialData({ economic_state: rates.economic_state }).economic_state}</p>
                        <p><strong>Base Rate:</strong> ${(rates.base_rate * 100).toFixed(1)}%</p>
                        <h6>Loan Rates:</h6>
                        <ul>
                            <li>Standard: ${(rates.rates.loan.standard * 100).toFixed(1)}%</li>
                            <li>Good Credit: ${(rates.rates.loan.good_credit * 100).toFixed(1)}%</li>
                            <li>Poor Credit: ${(rates.rates.loan.poor_credit * 100).toFixed(1)}%</li>
                        </ul>
                        <h6>CD Rates:</h6>
                        <ul>
                            <li>Short Term (3 laps): ${(rates.rates.cd.short_term * 100).toFixed(1)}%</li>
                            <li>Medium Term (5 laps): ${(rates.rates.cd.medium_term * 100).toFixed(1)}%</li>
                            <li>Long Term (7 laps): ${(rates.rates.cd.long_term * 100).toFixed(1)}%</li>
                        </ul>
                    `;
                    ratesElement.innerHTML = ratesHtml;
                } else {
                    ratesElement.innerHTML = '<p>No interest rate data available</p>';
                }
            }
        } else {
            console.error('Failed to fetch finance overview:', data.error);
            
            // Safely update DOM elements only if they exist
            const statsElement = safeGetElement('finance-stats');
            if (statsElement) {
                statsElement.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
            }
            
            const ratesElement = safeGetElement('interest-rates');
            if (ratesElement) {
                ratesElement.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
            }
        }
    })
    .catch(error => {
        console.error('Error fetching finance overview:', error);
        
        // Safely update DOM elements only if they exist
        const statsElement = safeGetElement('finance-stats');
        if (statsElement) {
            statsElement.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
        }
        
        const ratesElement = safeGetElement('interest-rates');
        if (ratesElement) {
            ratesElement.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
        }
        
        // Retry if we haven't exceeded max retries
        if (retryCount < maxRetries) {
            console.log(`Retrying financial overview fetch (attempt ${retryCount + 1} of ${maxRetries})...`);
            setTimeout(() => {
                refreshFinancialOverview(retryCount + 1);
            }, 1000 * (retryCount + 1)); // Exponential backoff
        } else {
            // Use fallback data if all retries fail
            provideFallbackFinancialData();
        }
    });
}

// Provide fallback financial data if the API fails
function provideFallbackFinancialData() {
    console.log('Using fallback financial data...');
    
    const statsElement = safeGetElement('finance-stats');
    if (statsElement) {
        let statsHtml = `
            <div class="alert alert-warning">
                <p><strong>Using fallback data - API connection failed</strong></p>
            </div>
            <table class="table">
                <tr><th>Total Money in Game:</th><td>$15,000</td></tr>
                <tr><th>Bank Reserves:</th><td>$10,000</td></tr>
                <tr><th>Player Holdings:</th><td>$5,000</td></tr>
                <tr><th>Community Fund:</th><td>$0</td></tr>
                <tr><th>Total Active Loans:</th><td>$0</td></tr>
            </table>
        `;
        statsElement.innerHTML = statsHtml;
    }
    
    const ratesElement = safeGetElement('interest-rates');
    if (ratesElement) {
        let ratesHtml = `
            <div class="alert alert-warning">
                <p><strong>Using fallback data - API connection failed</strong></p>
            </div>
            <p><strong>Economic State:</strong> Normal</p>
            <p><strong>Base Rate:</strong> 5.0%</p>
            <h6>Loan Rates:</h6>
            <ul>
                <li>Standard: 7.0%</li>
                <li>Good Credit: 5.0%</li>
                <li>Poor Credit: 10.0%</li>
            </ul>
            <h6>CD Rates:</h6>
            <ul>
                <li>Short Term (3 laps): 4.0%</li>
                <li>Medium Term (5 laps): 5.0%</li>
                <li>Long Term (7 laps): 6.0%</li>
            </ul>
        `;
        ratesElement.innerHTML = ratesHtml;
    }
} 