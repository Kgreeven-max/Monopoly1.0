/**
 * AuctionPanel.js - Displays active auctions and allows users to place bids
 * 
 * This component handles:
 * - Displaying active auction details
 * - Countdown timer for auction expiration
 * - Bidding interface
 * - Auction results display
 */

class AuctionPanel {
  /**
   * Creates a new AuctionPanel instance
   * @param {Object} socket - The socket.io connection
   * @param {Object} gameState - The current game state
   */
  constructor(socket, gameState) {
    this.socket = socket;
    this.gameState = gameState;
    this.isActive = false;
    this.auction = null;
    this.timerInterval = null;
    this.participantsMap = new Map();
    this.currentPlayerId = gameState.currentPlayerId;
    
    // Create the panel DOM element
    this.panelElement = document.createElement('div');
    this.panelElement.className = 'auction-panel hidden';
    document.body.appendChild(this.panelElement);
    
    // Initialize socket event listeners
    this._initializeSocketListeners();
  }
  
  /**
   * Sets up all the socket event listeners for auction events
   */
  _initializeSocketListeners() {
    this.socket.on('auction_started', (data) => this.handleAuctionStart(data));
    this.socket.on('auction_bid_placed', (data) => this.handleBidPlaced(data));
    this.socket.on('auction_player_passed', (data) => this.handlePlayerPassed(data));
    this.socket.on('auction_ended', (data) => this.handleAuctionEnd(data));
    this.socket.on('auction_timeout', (data) => this.handleAuctionTimeout(data));
  }
  
  /**
   * Handles the auction_started event
   * @param {Object} data - The auction data
   */
  handleAuctionStart(data) {
    console.log('Auction started:', data);
    this.auction = data;
    this.isActive = true;
    
    // Reset the participants map
    this.participantsMap.clear();
    
    // Setup participants based on auction data
    if (data.participants) {
      data.participants.forEach(player => {
        this.participantsMap.set(player.id, {
          id: player.id,
          name: player.name,
          status: 'active', // active, passed, or winner
          isCurrentPlayer: player.id === this.currentPlayerId
        });
      });
    }
    
    // Create the auction UI
    this._createAuctionUI(data);
    
    // Show the panel
    this.panelElement.classList.remove('hidden');
    this.panelElement.classList.add('auction-active');
    
    // Start the timer
    this._startTimer(data.timeRemaining || 60);
    
    // Add initial log entry
    this._addToAuctionLog(`Auction started for ${data.propertyName}`);
  }
  
  /**
   * Creates the auction UI
   * @param {Object} auctionData - The auction data
   */
  _createAuctionUI(auctionData) {
    const property = auctionData.property;
    const propertyColor = property.color || '#999999';
    
    this.panelElement.innerHTML = `
      <div class="auction-item">
        <div class="auction-header">
          <h3>Property Auction</h3>
          <div class="auction-badge">Live Auction</div>
        </div>
        
        <div class="auction-details">
          <div class="property-info">
            <h3>${property.name}</h3>
            <div class="property-image-container">
              <div class="property-color-bar" style="background-color: ${propertyColor};"></div>
              <img class="property-image" src="/static/images/properties/${property.id}.jpg" 
                   onerror="this.src='/static/images/properties/default.jpg'" 
                   alt="${property.name}">
            </div>
          </div>
          
          <div class="auction-info">
            <div class="bid-info">
              <div class="info-row">
                <span class="info-label">Starting Price:</span>
                <span class="info-value">$${property.price}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Current Bid:</span>
                <span class="info-value" id="current-bid">$${auctionData.currentBid || property.price}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Current Winner:</span>
                <span class="info-value" id="current-winner">${auctionData.currentWinner ? auctionData.currentWinner.name : 'None'}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Time Remaining:</span>
                <span class="info-value" id="auction-timer">00:00</span>
              </div>
            </div>
            
            ${this._createBiddingControls(auctionData)}
          </div>
        </div>
        
        <div class="auction-participants-container">
          <h4>Participants</h4>
          <div class="auction-participants" id="auction-participants">
            ${this._generateParticipantsList()}
          </div>
        </div>
        
        <div class="auction-log-container">
          <h4>Auction Activity</h4>
          <div class="auction-log" id="auction-log"></div>
        </div>
      </div>
    `;
    
    // Add event listeners to the buttons
    this._setupButtonListeners();
  }
  
  /**
   * Creates the bidding controls HTML
   * @param {Object} auctionData - The auction data
   * @returns {string} - HTML for bidding controls
   */
  _createBiddingControls(auctionData) {
    const currentPlayer = this.participantsMap.get(this.currentPlayerId);
    const canBid = currentPlayer && currentPlayer.status === 'active';
    const minBid = (auctionData.currentBid || auctionData.property.price) + 10;
    
    if (!canBid) {
      return `
        <div class="auction-actions">
          <p>You are ${currentPlayer ? 'not eligible to bid' : 'observing this auction'}</p>
        </div>
      `;
    }
    
    return `
      <div class="auction-actions">
        <div class="bid-input-container">
          <label for="bid-amount">Your Bid:</label>
          <div class="bid-controls">
            <input type="number" id="bid-amount" class="bid-input" 
                   min="${minBid}" step="10" value="${minBid}">
            <button id="place-bid-btn" class="auction-bid-btn">Place Bid</button>
            <button id="pass-bid-btn" class="auction-pass-btn">Pass</button>
          </div>
        </div>
      </div>
    `;
  }
  
  /**
   * Generates the HTML for the participants list
   * @returns {string} - HTML for participants
   */
  _generateParticipantsList() {
    let html = '';
    
    this.participantsMap.forEach(participant => {
      const statusClass = participant.status === 'active' ? 'active' : 
                          participant.status === 'passed' ? 'passed' : 'winner';
      
      html += `
        <div class="participant" data-player-id="${participant.id}">
          <span class="participant-name">${participant.name}</span>
          <span class="participant-status ${statusClass}">${participant.status}</span>
        </div>
      `;
    });
    
    return html;
  }
  
  /**
   * Sets up event listeners for the bidding buttons
   */
  _setupButtonListeners() {
    const placeBidBtn = document.getElementById('place-bid-btn');
    const passBidBtn = document.getElementById('pass-bid-btn');
    const closeBtn = document.getElementById('close-auction-btn');
    
    if (placeBidBtn) {
      placeBidBtn.addEventListener('click', () => this.placeBid());
    }
    
    if (passBidBtn) {
      passBidBtn.addEventListener('click', () => this.passBid());
    }
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }
  }
  
  /**
   * Places a bid for the current player
   */
  placeBid() {
    if (!this.isActive || !this.auction) return;
    
    const bidInput = document.getElementById('bid-amount');
    if (!bidInput) return;
    
    const bidAmount = parseInt(bidInput.value, 10);
    const minBid = (this.auction.currentBid || this.auction.property.price) + 10;
    
    if (isNaN(bidAmount) || bidAmount < minBid) {
      alert(`Bid must be at least $${minBid}`);
      return;
    }
    
    this.socket.emit('place_bid', {
      auction_id: this.auction.id,
      player_id: this.currentPlayerId,
      bid_amount: bidAmount
    });
    
    // Temporarily disable the button to prevent multiple clicks
    const placeBidBtn = document.getElementById('place-bid-btn');
    if (placeBidBtn) {
      placeBidBtn.disabled = true;
      setTimeout(() => {
        if (placeBidBtn) placeBidBtn.disabled = false;
      }, 1000);
    }
  }
  
  /**
   * Passes on bidding for the current player
   */
  passBid() {
    if (!this.isActive || !this.auction) return;
    
    this.socket.emit('pass_auction', {
      auction_id: this.auction.id,
      player_id: this.currentPlayerId
    });
    
    // Update UI to show player passed
    const currentPlayer = this.participantsMap.get(this.currentPlayerId);
    if (currentPlayer) {
      currentPlayer.status = 'passed';
      this._updateParticipantStatus(this.currentPlayerId, 'passed');
    }
    
    // Disable bidding controls
    const placeBidBtn = document.getElementById('place-bid-btn');
    const passBidBtn = document.getElementById('pass-bid-btn');
    
    if (placeBidBtn) placeBidBtn.disabled = true;
    if (passBidBtn) passBidBtn.disabled = true;
    
    this._addToAuctionLog(`You passed on bidding`);
  }
  
  /**
   * Handles the bid_placed event
   * @param {Object} data - The bid data
   */
  handleBidPlaced(data) {
    console.log('Bid placed:', data);
    
    if (!this.auction || this.auction.id !== data.auction_id) return;
    
    // Update auction data
    this.auction.currentBid = data.bid_amount;
    this.auction.currentWinner = data.player;
    
    // Update UI
    this._updateCurrentBid(data.bid_amount);
    this._updateCurrentWinner(data.player.name);
    this._addToAuctionLog(`${data.player.name} placed a bid of $${data.bid_amount}`);
    
    // Reset timer if configured to do so
    if (data.resetTimer && data.timeRemaining) {
      this._resetTimer(data.timeRemaining);
    }
    
    // Highlight the bid in the UI
    const bidInfo = document.querySelector('.bid-info');
    if (bidInfo) {
      bidInfo.classList.add('bid-highlight');
      setTimeout(() => bidInfo.classList.remove('bid-highlight'), 2000);
    }
    
    // Update min bid value for the input field
    const bidInput = document.getElementById('bid-amount');
    if (bidInput) {
      const minBid = data.bid_amount + 10;
      bidInput.min = minBid;
      bidInput.value = minBid;
    }
  }
  
  /**
   * Handles when a player passes on bidding
   * @param {Object} data - The pass data
   */
  handlePlayerPassed(data) {
    console.log('Player passed:', data);
    
    if (!this.auction || this.auction.id !== data.auction_id) return;
    
    // Update participant status
    this._updateParticipantStatus(data.player_id, 'passed');
    
    // Add to log
    const playerName = data.player_name || 'Player ' + data.player_id;
    this._addToAuctionLog(`${playerName} passed on bidding`);
  }
  
  /**
   * Handles the auction_ended event
   * @param {Object} data - The auction end data
   */
  handleAuctionEnd(data) {
    console.log('Auction ended:', data);
    
    if (!this.auction || this.auction.id !== data.auction_id) return;
    
    // Stop the timer
    this._stopTimer();
    
    // Update UI to show auction ended
    this.isActive = false;
    const auctionBadge = this.panelElement.querySelector('.auction-badge');
    if (auctionBadge) {
      auctionBadge.textContent = 'Auction Ended';
      auctionBadge.classList.add('auction-ended');
    }
    
    // Update the timer display
    const timerElement = document.getElementById('auction-timer');
    if (timerElement) {
      timerElement.textContent = '00:00';
      timerElement.classList.add('expired');
    }
    
    // Add result to log
    if (data.winner) {
      this._addToAuctionLog(`Auction ended. ${data.winner.name} won with a bid of $${data.final_bid}`);
      
      // Mark winner in participants
      this._updateParticipantStatus(data.winner.id, 'winner');
    } else {
      this._addToAuctionLog(`Auction ended with no winner. Property remains unowned.`);
    }
    
    // Add close button
    const auctionActions = this.panelElement.querySelector('.auction-actions');
    if (auctionActions) {
      auctionActions.innerHTML = `
        <button id="close-auction-btn" class="auction-close-btn">Close</button>
      `;
      
      // Add event listener to the close button
      const closeBtn = document.getElementById('close-auction-btn');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.close());
      }
    }
    
    // Add class to panel for styling
    this.panelElement.classList.add('auction-ended');
  }
  
  /**
   * Handles auction timeout event
   * @param {Object} data - The timeout data
   */
  handleAuctionTimeout(data) {
    console.log('Auction timeout:', data);
    
    if (!this.auction || this.auction.id !== data.auction_id) return;
    
    this._addToAuctionLog(`Time expired for the auction`);
    
    // The server should send an auction_ended event after this
  }
  
  /**
   * Updates the current bid display
   * @param {number} amount - The bid amount
   */
  _updateCurrentBid(amount) {
    const bidElement = document.getElementById('current-bid');
    if (bidElement) {
      bidElement.textContent = `$${amount}`;
    }
  }
  
  /**
   * Updates the current winner display
   * @param {string} name - The winner's name
   */
  _updateCurrentWinner(name) {
    const winnerElement = document.getElementById('current-winner');
    if (winnerElement) {
      winnerElement.textContent = name;
    }
  }
  
  /**
   * Updates a participant's status in the UI
   * @param {string} playerId - The player ID
   * @param {string} status - The new status
   */
  _updateParticipantStatus(playerId, status) {
    // Update in our data structure
    const participant = this.participantsMap.get(playerId);
    if (participant) {
      participant.status = status;
    }
    
    // Update in the DOM
    const participantElement = document.querySelector(`.participant[data-player-id="${playerId}"]`);
    if (participantElement) {
      const statusElement = participantElement.querySelector('.participant-status');
      if (statusElement) {
        // Remove existing status classes
        statusElement.classList.remove('active', 'passed', 'winner');
        // Add new status class
        statusElement.classList.add(status);
        // Update text
        statusElement.textContent = status;
      }
    }
  }
  
  /**
   * Adds an entry to the auction log
   * @param {string} message - The log message
   */
  _addToAuctionLog(message) {
    const logElement = document.getElementById('auction-log');
    if (!logElement) return;
    
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-message">${message}</span>
    `;
    
    logElement.appendChild(logEntry);
    
    // Scroll to the bottom
    logElement.scrollTop = logElement.scrollHeight;
  }
  
  /**
   * Starts the auction timer
   * @param {number} seconds - The starting time in seconds
   */
  _startTimer(seconds) {
    this._stopTimer(); // Clear any existing timer
    
    let timeRemaining = seconds;
    this._updateTimerDisplay(timeRemaining);
    
    this.timerInterval = setInterval(() => {
      timeRemaining--;
      
      if (timeRemaining <= 0) {
        this._stopTimer();
        this._updateTimerDisplay(0);
        return;
      }
      
      this._updateTimerDisplay(timeRemaining);
      
      // Add warning class when time is running low
      if (timeRemaining <= 10) {
        const timerElement = document.getElementById('auction-timer');
        if (timerElement) {
          timerElement.classList.add('urgent');
        }
      }
    }, 1000);
  }
  
  /**
   * Resets the timer to a new value
   * @param {number} seconds - The new time in seconds
   */
  _resetTimer(seconds) {
    this._stopTimer();
    this._startTimer(seconds);
    
    // Remove urgent class if it was added
    const timerElement = document.getElementById('auction-timer');
    if (timerElement) {
      timerElement.classList.remove('urgent');
    }
  }
  
  /**
   * Stops the timer
   */
  _stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }
  
  /**
   * Updates the timer display
   * @param {number} seconds - The time in seconds
   */
  _updateTimerDisplay(seconds) {
    const timerElement = document.getElementById('auction-timer');
    if (!timerElement) return;
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
  
  /**
   * Closes the auction panel
   */
  close() {
    this._stopTimer();
    this.panelElement.classList.add('hidden');
    
    // Reset after animation
    setTimeout(() => {
      this.isActive = false;
      this.auction = null;
      this.panelElement.classList.remove('auction-active', 'auction-ended');
      this.panelElement.innerHTML = '';
    }, 300);
  }
  
  /**
   * Checks if the auction is active
   * @returns {boolean} - Whether the auction is active
   */
  isAuctionActive() {
    return this.isActive;
  }
}

// Export the AuctionPanel class
export default AuctionPanel; 