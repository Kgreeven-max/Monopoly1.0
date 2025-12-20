/**
 * Shared types, schemas, and utilities for Pinopoly
 */

// =============================================================================
// SOCKET EVENT NAMES
// =============================================================================

export const SocketEvents = {
  // Client -> Server
  AUTH_PLAYER: 'auth:player',
  AUTH_DISPLAY: 'auth:display',
  AUTH_ADMIN: 'auth:admin',

  // Lobby events (client -> server)
  JOIN_GAME: 'lobby:join',           // Alias for controller compatibility
  LOBBY_JOIN: 'lobby:join',
  LOBBY_READY: 'lobby:ready',
  LOBBY_UNREADY: 'lobby:unready',
  LOBBY_ADD_BOT: 'lobby:addBot',
  ADD_BOT: 'lobby:addBot',           // Alias for controller compatibility
  LOBBY_REMOVE_BOT: 'lobby:removeBot',
  REMOVE_BOT: 'lobby:removeBot',     // Alias for controller compatibility
  LOBBY_START_GAME: 'lobby:startGame',
  START_GAME: 'lobby:startGame',     // Alias for controller compatibility

  // Game actions (client -> server)
  GAME_ROLL_DICE: 'game:rollDice',
  ROLL_DICE: 'game:rollDice',        // Alias for controller compatibility
  GAME_END_TURN: 'game:endTurn',
  END_TURN: 'game:endTurn',          // Alias for controller compatibility
  GAME_BUY_PROPERTY: 'game:buyProperty',
  BUY_PROPERTY: 'game:buyProperty',  // Alias for controller compatibility
  GAME_DECLINE_PROPERTY: 'game:declineProperty',
  DECLINE_PROPERTY: 'game:declineProperty', // Alias
  GAME_BUILD_HOUSE: 'game:buildHouse',
  BUILD_HOUSE: 'game:buildHouse',    // Alias
  GAME_SELL_HOUSE: 'game:sellHouse',
  GAME_MORTGAGE: 'game:mortgageProperty',
  GAME_UNMORTGAGE: 'game:unmortgageProperty',
  GAME_PAY_JAIL_FINE: 'game:payJailFine',
  PAY_JAIL_FINE: 'game:payJailFine', // Alias for controller compatibility
  GAME_USE_JAIL_CARD: 'game:useJailCard',
  USE_JAIL_CARD: 'game:useJailCard', // Alias
  GAME_ROLL_FOR_DOUBLES: 'game:rollForDoubles',
  GAME_EXECUTE_CARD: 'game:executeCard',
  EXECUTE_CARD: 'game:executeCard', // Alias for controller compatibility
  GAME_DECLARE_BANKRUPTCY: 'game:declareBankruptcy',

  TRADE_PROPOSE: 'trade:propose',
  TRADE_ACCEPT: 'trade:accept',
  TRADE_REJECT: 'trade:reject',
  TRADE_COUNTER: 'trade:counter',

  AUCTION_BID: 'auction:bid',
  AUCTION_PASS: 'auction:pass',

  ADMIN_PAUSE: 'admin:pauseGame',
  ADMIN_RESUME: 'admin:resumeGame',
  ADMIN_END: 'admin:endGame',
  ADMIN_KICK: 'admin:kickPlayer',
  ADMIN_ADJUST_MONEY: 'admin:adjustMoney',
  ADMIN_TRIGGER_EVENT: 'admin:triggerEvent',

  CHAT_MESSAGE: 'chat:message',

  // Server -> Client responses
  AUTH_SUCCESS: 'auth:success',
  AUTH_ERROR: 'auth:error',

  // Join responses
  JOINED_GAME: 'lobby:joined',       // Response to JOIN_GAME
  JOIN_ERROR: 'lobby:joinError',     // Error response to JOIN_GAME

  // Lobby state updates
  LOBBY_STATE: 'lobby:state',
  LOBBY_PLAYER_JOINED: 'lobby:playerJoined',
  LOBBY_PLAYER_LEFT: 'lobby:playerLeft',
  LOBBY_PLAYER_READY: 'lobby:playerReady',
  LOBBY_GAME_STARTING: 'lobby:gameStarting',

  // Aliases for controller compatibility
  PLAYER_JOINED: 'lobby:playerJoined',
  PLAYER_LEFT: 'lobby:playerLeft',
  GAME_STARTED: 'game:started',

  // Game state updates
  GAME_STATE: 'game:state',
  GAME_DICE_ROLLED: 'game:diceRolled',
  GAME_PLAYER_MOVED: 'game:playerMoved',
  GAME_PROPERTY_BOUGHT: 'game:propertyBought',
  GAME_RENT_PAID: 'game:rentPaid',
  GAME_HOUSE_BUILT: 'game:houseBuilt',
  GAME_CARD_DRAWN: 'game:cardDrawn',
  GAME_PLAYER_BANKRUPT: 'game:playerBankrupt',
  GAME_PLAYER_RELEASED_FROM_JAIL: 'game:playerReleasedFromJail',
  GAME_TURN_CHANGED: 'game:turnChanged',
  GAME_ENDED: 'game:ended',

  // Aliases for controller compatibility
  DICE_RESULT: 'game:diceRolled',
  TURN_CHANGED: 'game:turnChanged',
  PROPERTY_PURCHASED: 'game:propertyBought',
  RENT_PAID: 'game:rentPaid',

  // Animation/display events
  DICE_ROLLING: 'game:diceRolling',
  MOVEMENT_COMPLETE: 'game:movementComplete',
  GAME_EVENT: 'game:event',

  // Player events
  KICKED: 'player:kicked',

  AUCTION_STARTED: 'auction:started',
  AUCTION_BID_PLACED: 'auction:bid',
  AUCTION_ENDED: 'auction:ended',

  TRADE_PROPOSED: 'trade:proposed',
  TRADE_ACCEPTED: 'trade:accepted',
  TRADE_REJECTED: 'trade:rejected',
  TRADE_COUNTERED: 'trade:countered',

  ECONOMY_CHANGED: 'economy:changed',
  ECONOMY_EVENT: 'economy:event',

  CHAT_RECEIVED: 'chat:message',
  ERROR: 'error',
} as const;

// =============================================================================
// CONSTANTS
// =============================================================================

export const ROOM_CODE_LENGTH = 6;
export const ROOM_CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // No confusing chars

export const TOKEN_TYPES = [
  'car',
  'dog',
  'hat',
  'ship',
  'thimble',
  'boot',
  'wheelbarrow',
  'cat',
] as const;

export const BOT_PERSONALITIES = [
  'conservative',
  'aggressive',
  'strategic',
  'opportunistic',
  'shark',
  'investor',
] as const;

export const DIFFICULTIES = ['easy', 'normal', 'hard'] as const;

export const PLAYER_COLORS = [
  '#FF6B6B', // Red
  '#4ECDC4', // Teal
  '#45B7D1', // Blue
  '#96CEB4', // Green
  '#FFEAA7', // Yellow
  '#DDA0DD', // Plum
  '#98D8C8', // Mint
  '#F7DC6F', // Gold
] as const;

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Generate a random room code
 */
export function generateRoomCode(): string {
  let code = '';
  for (let i = 0; i < ROOM_CODE_LENGTH; i++) {
    code += ROOM_CODE_CHARS[Math.floor(Math.random() * ROOM_CODE_CHARS.length)];
  }
  return code;
}

/**
 * Validate a room code format
 */
export function isValidRoomCode(code: string): boolean {
  if (code.length !== ROOM_CODE_LENGTH) return false;
  return [...code].every((char) => ROOM_CODE_CHARS.includes(char));
}

/**
 * Format money with dollar sign and commas
 */
export function formatMoney(amount: number): string {
  return `$${amount.toLocaleString()}`;
}

/**
 * Get ordinal suffix for a number (1st, 2nd, 3rd, etc.)
 */
export function getOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

/**
 * Sleep for a given number of milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Generate a UUID v4
 */
export function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
