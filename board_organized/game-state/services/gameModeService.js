import ApiService from './apiService';

/**
 * Service for game mode API operations
 */
class GameModeService {
  /**
   * Get list of available game modes
   * @returns {Promise<Object>} - Available game modes
   */
  static async getAvailableModes() {
    return ApiService.get('/game-modes/');
  }
  
  /**
   * Select and initialize a game mode
   * @param {string} gameId - Game ID
   * @param {string} modeId - Mode ID to select
   * @returns {Promise<Object>} - Result of mode selection
   */
  static async selectGameMode(gameId, modeId) {
    return ApiService.adminPost(`/game-modes/select/${gameId}`, { mode_id: modeId });
  }
  
  /**
   * Check if win condition is met for current game mode
   * @param {string} gameId - Game ID
   * @returns {Promise<Object>} - Win condition status
   */
  static async checkWinCondition(gameId) {
    return ApiService.get(`/game-modes/check-win/${gameId}`);
  }
  
  /**
   * Get current game mode settings
   * @param {string} gameId - Game ID
   * @returns {Promise<Object>} - Game mode settings
   */
  static async getGameModeSettings(gameId) {
    return ApiService.get(`/game-modes/settings/${gameId}`);
  }
  
  /**
   * Update game mode settings
   * @param {string} gameId - Game ID
   * @param {Object} settings - Settings to update
   * @returns {Promise<Object>} - Updated game mode
   */
  static async updateGameModeSettings(gameId, settings) {
    return ApiService.adminPost(`/game-modes/update-settings/${gameId}`, { settings });
  }
  
  /**
   * List all active game modes
   * @returns {Promise<Object>} - Active game modes
   */
  static async listActiveGameModes() {
    return ApiService.adminGet('/game-modes/list-active');
  }
  
  /**
   * Get mode specific configuration options
   * @param {string} modeType - Mode type (classic, speed, etc.)
   * @returns {Object} - Configuration options for the specified mode
   */
  static getModeConfigOptions(modeType) {
    const configOptions = {
      classic: {
        name: 'Classic Mode',
        settings: [
          { id: 'starting_cash', label: 'Starting Cash', type: 'number', default: 1500 },
          { id: 'go_salary', label: 'GO Salary', type: 'number', default: 200 },
          { id: 'free_parking_collects_fees', label: 'Free Parking Collects Fees', type: 'boolean', default: false },
          { id: 'auction_enabled', label: 'Auctions Enabled', type: 'boolean', default: true }
        ]
      },
      speed: {
        name: 'Speed Mode',
        settings: [
          { id: 'starting_cash', label: 'Starting Cash', type: 'number', default: 3000 },
          { id: 'go_salary', label: 'GO Salary', type: 'number', default: 400 },
          { id: 'max_turns', label: 'Maximum Turns', type: 'number', default: 20 },
          { id: 'max_time_minutes', label: 'Time Limit (minutes)', type: 'number', default: 30 },
          { id: 'turn_timer_seconds', label: 'Turn Timer (seconds)', type: 'number', default: 60 }
        ]
      },
      cooperative: {
        name: 'Co-op Mode',
        settings: [
          { id: 'starting_cash', label: 'Starting Cash', type: 'number', default: 1200 },
          { id: 'go_salary', label: 'GO Salary', type: 'number', default: 150 },
          { id: 'max_turns', label: 'Maximum Turns', type: 'number', default: 30 },
          { id: 'team_income_sharing', label: 'Income Sharing %', type: 'number', default: 10 }
        ]
      },
      tycoon: {
        name: 'Tycoon Mode',
        settings: [
          { id: 'starting_cash', label: 'Starting Cash', type: 'number', default: 2000 },
          { id: 'go_salary', label: 'GO Salary', type: 'number', default: 200 },
          { id: 'custom_settings.development_levels', label: 'Development Levels', type: 'number', default: 5 }
        ]
      },
      market_crash: {
        name: 'Market Crash Mode',
        settings: [
          { id: 'starting_cash', label: 'Starting Cash', type: 'number', default: 2500 },
          { id: 'inflation_factor', label: 'Starting Inflation Factor', type: 'number', default: 0.7 },
          { id: 'custom_settings.market_volatility', label: 'Market Volatility', type: 'number', default: 2.0 },
          { id: 'event_frequency', label: 'Event Frequency', type: 'number', default: 0.3 }
        ]
      },
      team_battle: {
        name: 'Team Battle Mode',
        settings: [
          { id: 'starting_cash', label: 'Starting Cash', type: 'number', default: 2000 },
          { id: 'team_income_sharing', label: 'Income Sharing %', type: 'number', default: 10 },
          { id: 'custom_settings.min_teams', label: 'Minimum Teams', type: 'number', default: 2 },
          { id: 'custom_settings.max_teams', label: 'Maximum Teams', type: 'number', default: 4 }
        ]
      }
    };
    
    return configOptions[modeType] || configOptions.classic;
  }
  
  /**
   * Get formatted mode description
   * @param {string} modeType - Mode type
   * @returns {Object} - Mode description
   */
  static getModeDescription(modeType) {
    const descriptions = {
      classic: {
        title: 'Classic Mode',
        description: 'Traditional Pi-nopoly experience with standard rules',
        objective: 'Accumulate wealth and drive opponents to bankruptcy',
        winCondition: 'Last player remaining solvent',
        estimatedTime: '1-3 hours',
        difficulty: 'Standard'
      },
      speed: {
        title: 'Speed Mode',
        description: 'Faster-paced version designed for shorter play sessions',
        objective: 'Same as classic, but accelerated',
        winCondition: 'Player with highest net worth after fixed time/turns',
        estimatedTime: '30 minutes',
        difficulty: 'Standard'
      },
      cooperative: {
        title: 'Co-op Mode',
        description: 'Cooperative experience where players work together against the game system',
        objective: 'Collectively develop all properties before economic collapse',
        winCondition: 'All properties developed to at least level 2',
        estimatedTime: '1 hour',
        difficulty: 'Hard'
      },
      tycoon: {
        title: 'Tycoon Mode',
        description: 'Development-focused mode emphasizing property improvement',
        objective: 'Build the most impressive property empire',
        winCondition: 'First to achieve specified development milestones',
        estimatedTime: '1-2 hours',
        difficulty: 'Medium'
      },
      market_crash: {
        title: 'Market Crash Mode',
        description: 'Challenging mode centered around economic instability',
        objective: 'Survive and thrive during economic turmoil',
        winCondition: 'Highest net worth after market stabilizes',
        estimatedTime: '1-2 hours',
        difficulty: 'Hard'
      },
      team_battle: {
        title: 'Team Battle Mode',
        description: 'Competitive mode pitting teams of players against each other',
        objective: 'Establish team monopolies and bankrupt opposing teams',
        winCondition: 'First team to bankrupt all opponents or highest team net worth after time limit',
        estimatedTime: '1-2 hours',
        difficulty: 'Medium'
      }
    };
    
    return descriptions[modeType] || descriptions.classic;
  }

  /**
   * Get market crash specific data
   * @param {string} gameId - Game ID
   * @returns {Promise<Object>} - Market crash data
   */
  static async getMarketCrashData(gameId) {
    return ApiService.get(`/game-modes/market-crash/${gameId}`);
  }

  /**
   * Get property value history for market crash mode
   * @param {string} gameId - Game ID
   * @param {string} propertyId - Property ID
   * @returns {Promise<Object>} - Property value history
   */
  static async getPropertyValueHistory(gameId, propertyId) {
    return ApiService.get(`/game-modes/market-crash/${gameId}/property/${propertyId}/history`);
  }

  /**
   * Get market crash event notifications
   * @param {string} gameId - Game ID
   * @returns {Promise<Object>} - Market crash events
   */
  static async getMarketCrashEvents(gameId) {
    return ApiService.get(`/game-modes/market-crash/${gameId}/events`);
  }
}

export default GameModeService; 