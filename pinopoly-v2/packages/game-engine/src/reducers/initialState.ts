/**
 * Initial game state generator for Pinopoly
 */

import type { GameState, GameConfig, PropertyState, ColorGroup } from '../state/types';
import { SeededRandom } from '../rng/SeededRandom';

/**
 * Standard Monopoly board configuration
 */
const BOARD_PROPERTIES: Omit<PropertyState, 'currentValue' | 'mortgageValue'>[] = [
  // GO is position 0 - not a property
  { id: 1, position: 1, name: 'Mediterranean Avenue', type: 'street', group: 'brown', price: 60, baseRent: 2, rentLevels: [10, 30, 90, 160, 250], houseCost: 50, ownerId: null, houses: 0, isMortgaged: false },
  // Community Chest is position 2
  { id: 3, position: 3, name: 'Baltic Avenue', type: 'street', group: 'brown', price: 60, baseRent: 4, rentLevels: [20, 60, 180, 320, 450], houseCost: 50, ownerId: null, houses: 0, isMortgaged: false },
  // Income Tax is position 4
  { id: 5, position: 5, name: 'Reading Railroad', type: 'railroad', group: null, price: 200, baseRent: 25, rentLevels: [50, 100, 200], houseCost: 0, ownerId: null, houses: 0, isMortgaged: false },
  { id: 6, position: 6, name: 'Oriental Avenue', type: 'street', group: 'lightBlue', price: 100, baseRent: 6, rentLevels: [30, 90, 270, 400, 550], houseCost: 50, ownerId: null, houses: 0, isMortgaged: false },
  // Chance is position 7
  { id: 8, position: 8, name: 'Vermont Avenue', type: 'street', group: 'lightBlue', price: 100, baseRent: 6, rentLevels: [30, 90, 270, 400, 550], houseCost: 50, ownerId: null, houses: 0, isMortgaged: false },
  { id: 9, position: 9, name: 'Connecticut Avenue', type: 'street', group: 'lightBlue', price: 120, baseRent: 8, rentLevels: [40, 100, 300, 450, 600], houseCost: 50, ownerId: null, houses: 0, isMortgaged: false },
  // Jail/Just Visiting is position 10
  { id: 11, position: 11, name: 'St. Charles Place', type: 'street', group: 'pink', price: 140, baseRent: 10, rentLevels: [50, 150, 450, 625, 750], houseCost: 100, ownerId: null, houses: 0, isMortgaged: false },
  { id: 12, position: 12, name: 'Electric Company', type: 'utility', group: null, price: 150, baseRent: 0, rentLevels: [], houseCost: 0, ownerId: null, houses: 0, isMortgaged: false },
  { id: 13, position: 13, name: 'States Avenue', type: 'street', group: 'pink', price: 140, baseRent: 10, rentLevels: [50, 150, 450, 625, 750], houseCost: 100, ownerId: null, houses: 0, isMortgaged: false },
  { id: 14, position: 14, name: 'Virginia Avenue', type: 'street', group: 'pink', price: 160, baseRent: 12, rentLevels: [60, 180, 500, 700, 900], houseCost: 100, ownerId: null, houses: 0, isMortgaged: false },
  { id: 15, position: 15, name: 'Pennsylvania Railroad', type: 'railroad', group: null, price: 200, baseRent: 25, rentLevels: [50, 100, 200], houseCost: 0, ownerId: null, houses: 0, isMortgaged: false },
  { id: 16, position: 16, name: 'St. James Place', type: 'street', group: 'orange', price: 180, baseRent: 14, rentLevels: [70, 200, 550, 750, 950], houseCost: 100, ownerId: null, houses: 0, isMortgaged: false },
  // Community Chest is position 17
  { id: 18, position: 18, name: 'Tennessee Avenue', type: 'street', group: 'orange', price: 180, baseRent: 14, rentLevels: [70, 200, 550, 750, 950], houseCost: 100, ownerId: null, houses: 0, isMortgaged: false },
  { id: 19, position: 19, name: 'New York Avenue', type: 'street', group: 'orange', price: 200, baseRent: 16, rentLevels: [80, 220, 600, 800, 1000], houseCost: 100, ownerId: null, houses: 0, isMortgaged: false },
  // Free Parking is position 20
  { id: 21, position: 21, name: 'Kentucky Avenue', type: 'street', group: 'red', price: 220, baseRent: 18, rentLevels: [90, 250, 700, 875, 1050], houseCost: 150, ownerId: null, houses: 0, isMortgaged: false },
  // Chance is position 22
  { id: 23, position: 23, name: 'Indiana Avenue', type: 'street', group: 'red', price: 220, baseRent: 18, rentLevels: [90, 250, 700, 875, 1050], houseCost: 150, ownerId: null, houses: 0, isMortgaged: false },
  { id: 24, position: 24, name: 'Illinois Avenue', type: 'street', group: 'red', price: 240, baseRent: 20, rentLevels: [100, 300, 750, 925, 1100], houseCost: 150, ownerId: null, houses: 0, isMortgaged: false },
  { id: 25, position: 25, name: 'B&O Railroad', type: 'railroad', group: null, price: 200, baseRent: 25, rentLevels: [50, 100, 200], houseCost: 0, ownerId: null, houses: 0, isMortgaged: false },
  { id: 26, position: 26, name: 'Atlantic Avenue', type: 'street', group: 'yellow', price: 260, baseRent: 22, rentLevels: [110, 330, 800, 975, 1150], houseCost: 150, ownerId: null, houses: 0, isMortgaged: false },
  { id: 27, position: 27, name: 'Ventnor Avenue', type: 'street', group: 'yellow', price: 260, baseRent: 22, rentLevels: [110, 330, 800, 975, 1150], houseCost: 150, ownerId: null, houses: 0, isMortgaged: false },
  { id: 28, position: 28, name: 'Water Works', type: 'utility', group: null, price: 150, baseRent: 0, rentLevels: [], houseCost: 0, ownerId: null, houses: 0, isMortgaged: false },
  { id: 29, position: 29, name: 'Marvin Gardens', type: 'street', group: 'yellow', price: 280, baseRent: 24, rentLevels: [120, 360, 850, 1025, 1200], houseCost: 150, ownerId: null, houses: 0, isMortgaged: false },
  // Go To Jail is position 30
  { id: 31, position: 31, name: 'Pacific Avenue', type: 'street', group: 'green', price: 300, baseRent: 26, rentLevels: [130, 390, 900, 1100, 1275], houseCost: 200, ownerId: null, houses: 0, isMortgaged: false },
  { id: 32, position: 32, name: 'North Carolina Avenue', type: 'street', group: 'green', price: 300, baseRent: 26, rentLevels: [130, 390, 900, 1100, 1275], houseCost: 200, ownerId: null, houses: 0, isMortgaged: false },
  // Community Chest is position 33
  { id: 34, position: 34, name: 'Pennsylvania Avenue', type: 'street', group: 'green', price: 320, baseRent: 28, rentLevels: [150, 450, 1000, 1200, 1400], houseCost: 200, ownerId: null, houses: 0, isMortgaged: false },
  { id: 35, position: 35, name: 'Short Line Railroad', type: 'railroad', group: null, price: 200, baseRent: 25, rentLevels: [50, 100, 200], houseCost: 0, ownerId: null, houses: 0, isMortgaged: false },
  // Chance is position 36
  { id: 37, position: 37, name: 'Park Place', type: 'street', group: 'darkBlue', price: 350, baseRent: 35, rentLevels: [175, 500, 1100, 1300, 1500], houseCost: 200, ownerId: null, houses: 0, isMortgaged: false },
  // Luxury Tax is position 38
  { id: 39, position: 39, name: 'Boardwalk', type: 'street', group: 'darkBlue', price: 400, baseRent: 50, rentLevels: [200, 600, 1400, 1700, 2000], houseCost: 200, ownerId: null, houses: 0, isMortgaged: false },
];

/**
 * Chance cards
 */
const CHANCE_CARDS = [
  'advance_go',
  'advance_illinois',
  'advance_stcharles',
  'advance_utility',
  'advance_railroad',
  'bank_dividend_50',
  'get_out_of_jail',
  'go_back_3',
  'go_to_jail',
  'repairs_25_100',
  'poor_tax_15',
  'advance_reading',
  'advance_boardwalk',
  'chairman_pay_50',
  'building_loan_150',
  'crossword_100',
];

/**
 * Community Chest cards
 */
const COMMUNITY_CHEST_CARDS = [
  'advance_go',
  'bank_error_200',
  'doctor_fee_50',
  'stock_sale_50',
  'get_out_of_jail',
  'go_to_jail',
  'grand_opera_50',
  'holiday_fund_100',
  'tax_refund_20',
  'birthday_10',
  'life_insurance_100',
  'hospital_fee_100',
  'school_fees_50',
  'consultancy_25',
  'street_repairs_40_115',
  'beauty_contest_10',
  'inherit_100',
];

/**
 * Default game configuration
 */
export const DEFAULT_CONFIG: GameConfig = {
  maxPlayers: 8,
  startingMoney: 1500,
  goSalary: 200,
  jailFine: 50,
  maxJailTurns: 3,
  freeParkingEnabled: true,
  economicCyclesEnabled: true,
  financialInstrumentsEnabled: true,
  auctionRequired: true,
  turnTimeLimit: 0,
  maxRounds: 0,
};

/**
 * Create initial game state
 */
export function createInitialState(
  gameId: string,
  roomCode: string,
  config: Partial<GameConfig> = {},
  seed: number
): GameState {
  const rng = new SeededRandom(seed);
  const fullConfig = { ...DEFAULT_CONFIG, ...config };

  // Initialize properties
  const properties: Record<number, PropertyState> = {};
  for (const prop of BOARD_PROPERTIES) {
    properties[prop.position] = {
      ...prop,
      currentValue: prop.price,
      mortgageValue: Math.floor(prop.price / 2),
    };
  }

  // Shuffle card decks
  const chanceDeck = rng.shuffle([...CHANCE_CARDS]);
  const communityChestDeck = rng.shuffle([...COMMUNITY_CHEST_CARDS]);

  const initialState: GameState = {
    id: gameId,
    roomCode,
    status: 'lobby',
    round: 0,
    currentPlayerIndex: 0,
    playerOrder: [],
    phase: 'pre_roll',
    rngSeed: seed,
    rngState: rng.getState(),
    economy: {
      phase: 'stable',
      cyclePosition: 50,
      inflationRate: 0.03,
      baseInterestRate: 0.05,
      propertyValueMultiplier: 1.0,
      rentMultiplier: 1.0,
      turnsUntilPhaseCheck: 10,
    },
    players: {},
    properties,
    chanceDeck: {
      cards: chanceDeck,
      discarded: [],
    },
    communityChestDeck: {
      cards: communityChestDeck,
      discarded: [],
    },
    currentCard: null,
    freeParkingPot: 0,
    activeAuction: null,
    activeTrades: [],
    config: fullConfig,
    lastDiceRoll: null,
    consecutiveDoubles: 0,
    eventLog: [],
    startedAt: null,
    lastActionAt: Date.now(),
  };

  return initialState;
}

/**
 * Get all properties in a color group
 */
export function getPropertiesInGroup(
  state: GameState,
  group: ColorGroup
): PropertyState[] {
  return Object.values(state.properties).filter(
    (p) => p.group === group
  );
}

/**
 * Check if player has monopoly on a color group
 */
export function hasMonopoly(
  state: GameState,
  playerId: string,
  group: ColorGroup
): boolean {
  const groupProperties = getPropertiesInGroup(state, group);
  return groupProperties.every((p) => p.ownerId === playerId);
}
