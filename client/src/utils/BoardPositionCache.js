/**
 * BoardPositionCache - Pre-calculates and caches board space positions
 * Eliminates need for DOM queries during animations
 */

class BoardPositionCache {
  constructor() {
    this.positions = new Map();
    this.boardSize = { width: 0, height: 0 };
    this.initialized = false;
  }

  /**
   * Initialize the cache with board dimensions
   * @param {number} boardWidth - Board container width
   * @param {number} boardHeight - Board container height
   */
  initialize(boardWidth, boardHeight) {
    this.boardSize = { width: boardWidth, height: boardHeight };
    this.calculatePositions();
    this.initialized = true;
  }

  /**
   * Calculate positions for all 40 spaces
   */
  calculatePositions() {
    const { width, height } = this.boardSize;
    const spaceWidth = width / 11;
    const spaceHeight = height / 11;

    // Helper to calculate center position of a space
    const getSpaceCenter = (col, row) => ({
      x: (col + 0.5) * spaceWidth,
      y: (row + 0.5) * spaceHeight
    });

    // Bottom row (0-10) - right to left
    for (let i = 0; i <= 10; i++) {
      this.positions.set(i, getSpaceCenter(10 - i, 10));
    }

    // Left column (11-19) - bottom to top
    for (let i = 11; i <= 19; i++) {
      this.positions.set(i, getSpaceCenter(0, 10 - (i - 10)));
    }

    // Top row (20-30) - left to right
    for (let i = 20; i <= 30; i++) {
      this.positions.set(i, getSpaceCenter(i - 20, 0));
    }

    // Right column (31-39) - top to bottom
    for (let i = 31; i <= 39; i++) {
      this.positions.set(i, getSpaceCenter(10, i - 30));
    }
  }

  /**
   * Get the center position of a space
   * @param {number} spaceId - Space index (0-39)
   * @returns {{x: number, y: number}} Position coordinates
   */
  getSpacePosition(spaceId) {
    if (!this.initialized) {
      console.warn('BoardPositionCache not initialized');
      return { x: 0, y: 0 };
    }
    return this.positions.get(spaceId) || { x: 0, y: 0 };
  }

  /**
   * Get position for a player token on a space
   * @param {number} spaceId - Space index (0-39)
   * @param {number} playerIndex - Index of player on this space (for offset)
   * @param {number} totalPlayers - Total players on this space
   * @returns {{x: number, y: number}} Position with offset applied
   */
  getPlayerPosition(spaceId, playerIndex = 0, totalPlayers = 1) {
    const basePos = this.getSpacePosition(spaceId);
    
    if (totalPlayers === 1) {
      return basePos;
    }

    // Calculate offset for multiple players on same space
    const offsetRadius = Math.min(this.boardSize.width, this.boardSize.height) * 0.015;
    const angle = (2 * Math.PI * playerIndex) / totalPlayers;
    
    return {
      x: basePos.x + offsetRadius * Math.cos(angle),
      y: basePos.y + offsetRadius * Math.sin(angle)
    };
  }

  /**
   * Get the path of positions for moving between spaces
   * @param {number} fromSpace - Starting space
   * @param {number} toSpace - Ending space
   * @param {number} steps - Number of steps to take
   * @returns {Array<{x: number, y: number}>} Array of positions
   */
  getMovementPath(fromSpace, toSpace, steps) {
    const path = [];
    let currentSpace = fromSpace;

    for (let i = 0; i <= steps; i++) {
      path.push(this.getSpacePosition(currentSpace));
      if (i < steps) {
        currentSpace = (currentSpace + 1) % 40;
      }
    }

    return path;
  }

  /**
   * Calculate board-relative percentage position
   * @param {{x: number, y: number}} position - Absolute position
   * @returns {{x: number, y: number}} Percentage position (0-100)
   */
  toPercentage(position) {
    return {
      x: (position.x / this.boardSize.width) * 100,
      y: (position.y / this.boardSize.height) * 100
    };
  }

  /**
   * Check if cache is ready
   * @returns {boolean}
   */
  isInitialized() {
    return this.initialized;
  }

  /**
   * Update board size and recalculate positions
   * @param {number} boardWidth - New board width
   * @param {number} boardHeight - New board height
   */
  updateBoardSize(boardWidth, boardHeight) {
    if (boardWidth !== this.boardSize.width || boardHeight !== this.boardSize.height) {
      this.initialize(boardWidth, boardHeight);
    }
  }
}

// Singleton instance
export const boardPositionCache = new BoardPositionCache();