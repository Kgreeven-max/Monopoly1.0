/**
 * Core game state types for Pinopoly v2
 * These types define the complete game state structure
 */

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type GameStatus = 'lobby' | 'playing' | 'paused' | 'finished';

export type TurnPhase =
  | 'pre_roll'           // Waiting for player to roll
  | 'rolling'            // Dice animation in progress
  | 'moving'             // Token moving on board
  | 'landed'             // Landed, determining action
  | 'buy_decision'       // Player deciding to buy property
  | 'auction'            // Auction in progress
  | 'rent_payment'       // Rent being collected
  | 'card_action'        // Chance/Community Chest
  | 'jail_decision'      // Player in jail deciding action
  | 'development'        // Building houses/hotels
  | 'trade'              // Trade in progress
  | 'bankruptcy'         // Player going bankrupt
  | 'turn_end';          // Turn ending

export type EconomyPhase = 'recession' | 'stable' | 'growth' | 'boom';

export type ColorGroup =
  | 'brown'
  | 'lightBlue'
  | 'pink'
  | 'orange'
  | 'red'
  | 'yellow'
  | 'green'
  | 'darkBlue';

export type PropertyType = 'street' | 'railroad' | 'utility' | 'special';

export type SpecialSpaceType =
  | 'go'
  | 'jail'
  | 'free_parking'
  | 'go_to_jail'
  | 'chance'
  | 'community_chest'
  | 'income_tax'
  | 'luxury_tax';

export type TokenType =
  | 'car'
  | 'dog'
  | 'hat'
  | 'ship'
  | 'thimble'
  | 'boot'
  | 'wheelbarrow'
  | 'cat';

export type BotPersonality =
  | 'conservative'
  | 'aggressive'
  | 'strategic'
  | 'opportunistic'
  | 'shark'
  | 'investor';

export type Difficulty = 'easy' | 'normal' | 'hard';

// =============================================================================
// CORE STATE INTERFACES
// =============================================================================

export interface GameState {
  /** Unique game identifier */
  id: string;

  /** Room code for joining (6 chars) */
  roomCode: string;

  /** Current game status */
  status: GameStatus;

  /** Current round number (increments after all players have had a turn) */
  round: number;

  /** Index into playerOrder of current player */
  currentPlayerIndex: number;

  /** Ordered array of player IDs for turn order */
  playerOrder: string[];

  /** Current phase of the turn */
  phase: TurnPhase;

  /** Seed for RNG (for replay) */
  rngSeed: number;

  /** Current RNG state */
  rngState: number;

  /** Economic state */
  economy: EconomyState;

  /** All players keyed by ID */
  players: Record<string, PlayerState>;

  /** All properties keyed by position (0-39) */
  properties: Record<number, PropertyState>;

  /** Chance card deck */
  chanceDeck: CardDeck;

  /** Community Chest card deck */
  communityChestDeck: CardDeck;

  /** Free Parking pot (optional rule) */
  freeParkingPot: number;

  /** Active auction (if any) */
  activeAuction: AuctionState | null;

  /** Active trades */
  activeTrades: TradeState[];

  /** Game configuration */
  config: GameConfig;

  /** Last dice roll result */
  lastDiceRoll: DiceRoll | null;

  /** Consecutive doubles for current player (for jail) */
  consecutiveDoubles: number;

  /** Event log for replay/debugging */
  eventLog: GameEvent[];

  /** Timestamp of game start */
  startedAt: number | null;

  /** Timestamp of last action */
  lastActionAt: number;
}

export interface PlayerState {
  /** Unique player ID */
  id: string;

  /** Display name */
  name: string;

  /** Token type (car, hat, etc.) */
  token: TokenType;

  /** Player color (hex) */
  color: string;

  /** Current money */
  money: number;

  /** Current board position (0-39) */
  position: number;

  /** Is this a bot? */
  isBot: boolean;

  /** Bot personality (if bot) */
  botPersonality: BotPersonality | null;

  /** Bot difficulty (if bot) */
  botDifficulty: Difficulty | null;

  /** Is player in jail? */
  inJail: boolean;

  /** Turns spent in jail */
  jailTurns: number;

  /** Get out of jail free cards held */
  getOutOfJailCards: number;

  /** Is player bankrupt? */
  isBankrupt: boolean;

  /** Order in which player went bankrupt (null if not bankrupt) */
  bankruptcyOrder: number | null;

  /** Credit score (300-850) */
  creditScore: number;

  /** Number of times passed GO */
  timesPassedGo: number;

  /** Active loans */
  loans: LoanState[];

  /** Active CDs */
  cds: CDState[];

  /** Active HELOCs */
  helocs: HELOCState[];

  /** Is player connected (for reconnection handling) */
  isConnected: boolean;

  /** Socket ID (for server use) */
  socketId: string | null;
}

export interface PropertyState {
  /** Property ID (same as position) */
  id: number;

  /** Board position (0-39) */
  position: number;

  /** Property name */
  name: string;

  /** Property type */
  type: PropertyType;

  /** Color group (null for non-streets) */
  group: ColorGroup | null;

  /** Base purchase price */
  price: number;

  /** Base rent (no houses) */
  baseRent: number;

  /** Rent at each development level [1 house, 2, 3, 4, hotel] */
  rentLevels: number[];

  /** Cost per house */
  houseCost: number;

  /** Owner player ID (null if unowned) */
  ownerId: string | null;

  /** Number of houses (0-4, 5 = hotel) */
  houses: number;

  /** Is property mortgaged? */
  isMortgaged: boolean;

  /** Current market value (affected by economy) */
  currentValue: number;

  /** Mortgage value (typically 50% of price) */
  mortgageValue: number;
}

export interface EconomyState {
  /** Current economic phase */
  phase: EconomyPhase;

  /** Position in economic cycle (0-100) */
  cyclePosition: number;

  /** Current inflation rate */
  inflationRate: number;

  /** Base interest rate for loans */
  baseInterestRate: number;

  /** Property value multiplier */
  propertyValueMultiplier: number;

  /** Rent multiplier */
  rentMultiplier: number;

  /** Turns until next phase check */
  turnsUntilPhaseCheck: number;
}

// =============================================================================
// FINANCIAL INSTRUMENTS
// =============================================================================

export interface LoanState {
  id: string;
  playerId: string;
  principal: number;
  balance: number;
  interestRate: number;
  isFixedRate: boolean;
  startRound: number;
  termRounds: number;
  monthlyPayment: number;
  isActive: boolean;
}

export interface CDState {
  id: string;
  playerId: string;
  principal: number;
  interestRate: number;
  startRound: number;
  maturityRound: number;
  isMatured: boolean;
}

export interface HELOCState {
  id: string;
  playerId: string;
  propertyId: number;
  creditLimit: number;
  balance: number;
  interestRate: number;
  isActive: boolean;
}

// =============================================================================
// GAME MECHANICS
// =============================================================================

export interface DiceRoll {
  die1: number;
  die2: number;
  total: number;
  isDoubles: boolean;
}

export interface CardDeck {
  cards: string[];  // Card IDs in order
  discarded: string[];
}

export interface AuctionState {
  id: string;
  propertyId: number;
  currentBid: number;
  highestBidderId: string | null;
  participants: string[];  // Player IDs still in auction
  passed: string[];  // Player IDs who passed
  startedAt: number;
  endsAt: number;
}

export interface TradeState {
  id: string;
  proposerId: string;
  recipientId: string;
  offer: TradeOffer;
  request: TradeOffer;
  status: 'pending' | 'accepted' | 'rejected' | 'countered';
  createdAt: number;
  expiresAt: number;
}

export interface TradeOffer {
  money: number;
  propertyIds: number[];
  getOutOfJailCards: number;
}

// =============================================================================
// CONFIGURATION
// =============================================================================

export interface GameConfig {
  /** Maximum players (2-8) */
  maxPlayers: number;

  /** Starting money */
  startingMoney: number;

  /** GO salary */
  goSalary: number;

  /** Jail fine amount */
  jailFine: number;

  /** Max turns in jail before forced fine */
  maxJailTurns: number;

  /** Enable free parking pot */
  freeParkingEnabled: boolean;

  /** Enable economic cycles */
  economicCyclesEnabled: boolean;

  /** Enable financial instruments (loans, CDs, HELOC) */
  financialInstrumentsEnabled: boolean;

  /** Auction required if property declined */
  auctionRequired: boolean;

  /** Turn time limit in seconds (0 = no limit) */
  turnTimeLimit: number;

  /** Maximum rounds (0 = no limit) */
  maxRounds: number;
}

// =============================================================================
// EVENTS (for event log)
// =============================================================================

export interface GameEvent {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  playerId: string | null;
  round: number;
  timestamp: number;
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

export interface Position {
  x: number;
  y: number;
}

export interface NetWorth {
  cash: number;
  propertyValue: number;
  mortgagedValue: number;
  houseValue: number;
  cdValue: number;
  loanDebt: number;
  helocDebt: number;
  total: number;
}
