/**
 * Card definitions and execution logic for Chance and Community Chest
 */

import type { GameState, GameEvent } from '../state/types';
import {
  getNearestRailroad,
  getNearestUtility,
  moveBack,
  wouldPassGo,
  JAIL_POSITION,
  GO_POSITION,
} from './movement';

/**
 * Card effect type definitions
 */
export type CardEffectType =
  | 'move_to'
  | 'move_back'
  | 'collect'
  | 'pay'
  | 'pay_each_player'
  | 'collect_from_each'
  | 'go_to_jail'
  | 'get_out_of_jail'
  | 'repairs';

export interface CardDefinition {
  id: string;
  name: string;
  description: string;
  deck: 'chance' | 'community_chest';
  effect: CardEffectType;
  value?: number;
  destination?: number | 'nearest_railroad' | 'nearest_utility' | 'go';
  perHouse?: number;
  perHotel?: number;
  collectGoOnPass?: boolean;
}

/**
 * All card definitions
 */
export const CARD_DEFINITIONS: Record<string, CardDefinition> = {
  // ============= CHANCE CARDS =============
  advance_go: {
    id: 'advance_go',
    name: 'Advance to GO',
    description: 'Advance to GO. Collect $200.',
    deck: 'chance',
    effect: 'move_to',
    destination: 'go',
    collectGoOnPass: true,
  },
  advance_illinois: {
    id: 'advance_illinois',
    name: 'Advance to Illinois Avenue',
    description: 'Advance to Illinois Avenue. If you pass GO, collect $200.',
    deck: 'chance',
    effect: 'move_to',
    destination: 24,
    collectGoOnPass: true,
  },
  advance_stcharles: {
    id: 'advance_stcharles',
    name: 'Advance to St. Charles Place',
    description: 'Advance to St. Charles Place. If you pass GO, collect $200.',
    deck: 'chance',
    effect: 'move_to',
    destination: 11,
    collectGoOnPass: true,
  },
  advance_utility: {
    id: 'advance_utility',
    name: 'Advance to Nearest Utility',
    description: 'Advance to the nearest Utility. If unowned, you may buy it. If owned, pay 10x dice roll.',
    deck: 'chance',
    effect: 'move_to',
    destination: 'nearest_utility',
    collectGoOnPass: true,
  },
  advance_railroad: {
    id: 'advance_railroad',
    name: 'Advance to Nearest Railroad',
    description: 'Advance to the nearest Railroad. If unowned, you may buy it. If owned, pay 2x rent.',
    deck: 'chance',
    effect: 'move_to',
    destination: 'nearest_railroad',
    collectGoOnPass: true,
  },
  bank_dividend_50: {
    id: 'bank_dividend_50',
    name: 'Bank Dividend',
    description: 'Bank pays you dividend of $50.',
    deck: 'chance',
    effect: 'collect',
    value: 50,
  },
  get_out_of_jail: {
    id: 'get_out_of_jail',
    name: 'Get Out of Jail Free',
    description: 'Get Out of Jail Free. This card may be kept until needed.',
    deck: 'chance',
    effect: 'get_out_of_jail',
  },
  go_back_3: {
    id: 'go_back_3',
    name: 'Go Back 3 Spaces',
    description: 'Go back 3 spaces.',
    deck: 'chance',
    effect: 'move_back',
    value: 3,
  },
  go_to_jail: {
    id: 'go_to_jail',
    name: 'Go to Jail',
    description: 'Go directly to Jail. Do not pass GO. Do not collect $200.',
    deck: 'chance',
    effect: 'go_to_jail',
  },
  repairs_25_100: {
    id: 'repairs_25_100',
    name: 'General Repairs',
    description: 'Make general repairs on all your property. Pay $25 for each house and $100 for each hotel.',
    deck: 'chance',
    effect: 'repairs',
    perHouse: 25,
    perHotel: 100,
  },
  poor_tax_15: {
    id: 'poor_tax_15',
    name: 'Poor Tax',
    description: 'Pay poor tax of $15.',
    deck: 'chance',
    effect: 'pay',
    value: 15,
  },
  advance_reading: {
    id: 'advance_reading',
    name: 'Advance to Reading Railroad',
    description: 'Advance to Reading Railroad. If you pass GO, collect $200.',
    deck: 'chance',
    effect: 'move_to',
    destination: 5,
    collectGoOnPass: true,
  },
  advance_boardwalk: {
    id: 'advance_boardwalk',
    name: 'Advance to Boardwalk',
    description: 'Advance to Boardwalk.',
    deck: 'chance',
    effect: 'move_to',
    destination: 39,
    collectGoOnPass: false,
  },
  chairman_pay_50: {
    id: 'chairman_pay_50',
    name: 'Chairman of the Board',
    description: 'You have been elected Chairman of the Board. Pay each player $50.',
    deck: 'chance',
    effect: 'pay_each_player',
    value: 50,
  },
  building_loan_150: {
    id: 'building_loan_150',
    name: 'Building and Loan',
    description: 'Your building and loan matures. Collect $150.',
    deck: 'chance',
    effect: 'collect',
    value: 150,
  },
  crossword_100: {
    id: 'crossword_100',
    name: 'Crossword Competition',
    description: 'You have won a crossword competition. Collect $100.',
    deck: 'chance',
    effect: 'collect',
    value: 100,
  },

  // ============= COMMUNITY CHEST CARDS =============
  bank_error_200: {
    id: 'bank_error_200',
    name: 'Bank Error',
    description: 'Bank error in your favor. Collect $200.',
    deck: 'community_chest',
    effect: 'collect',
    value: 200,
  },
  doctor_fee_50: {
    id: 'doctor_fee_50',
    name: 'Doctor\'s Fee',
    description: 'Doctor\'s fee. Pay $50.',
    deck: 'community_chest',
    effect: 'pay',
    value: 50,
  },
  stock_sale_50: {
    id: 'stock_sale_50',
    name: 'Stock Sale',
    description: 'From sale of stock you get $50.',
    deck: 'community_chest',
    effect: 'collect',
    value: 50,
  },
  grand_opera_50: {
    id: 'grand_opera_50',
    name: 'Grand Opera Night',
    description: 'Grand Opera Night. Collect $50 from every player.',
    deck: 'community_chest',
    effect: 'collect_from_each',
    value: 50,
  },
  holiday_fund_100: {
    id: 'holiday_fund_100',
    name: 'Holiday Fund',
    description: 'Holiday Fund matures. Collect $100.',
    deck: 'community_chest',
    effect: 'collect',
    value: 100,
  },
  tax_refund_20: {
    id: 'tax_refund_20',
    name: 'Income Tax Refund',
    description: 'Income tax refund. Collect $20.',
    deck: 'community_chest',
    effect: 'collect',
    value: 20,
  },
  birthday_10: {
    id: 'birthday_10',
    name: 'Birthday',
    description: 'It is your birthday. Collect $10 from every player.',
    deck: 'community_chest',
    effect: 'collect_from_each',
    value: 10,
  },
  life_insurance_100: {
    id: 'life_insurance_100',
    name: 'Life Insurance',
    description: 'Life insurance matures. Collect $100.',
    deck: 'community_chest',
    effect: 'collect',
    value: 100,
  },
  hospital_fee_100: {
    id: 'hospital_fee_100',
    name: 'Hospital Fees',
    description: 'Pay hospital fees of $100.',
    deck: 'community_chest',
    effect: 'pay',
    value: 100,
  },
  school_fees_50: {
    id: 'school_fees_50',
    name: 'School Fees',
    description: 'Pay school fees of $50.',
    deck: 'community_chest',
    effect: 'pay',
    value: 50,
  },
  consultancy_25: {
    id: 'consultancy_25',
    name: 'Consultancy Fee',
    description: 'Receive $25 consultancy fee.',
    deck: 'community_chest',
    effect: 'collect',
    value: 25,
  },
  street_repairs_40_115: {
    id: 'street_repairs_40_115',
    name: 'Street Repairs',
    description: 'You are assessed for street repairs. Pay $40 per house and $115 per hotel.',
    deck: 'community_chest',
    effect: 'repairs',
    perHouse: 40,
    perHotel: 115,
  },
  beauty_contest_10: {
    id: 'beauty_contest_10',
    name: 'Beauty Contest',
    description: 'You have won second prize in a beauty contest. Collect $10.',
    deck: 'community_chest',
    effect: 'collect',
    value: 10,
  },
  inherit_100: {
    id: 'inherit_100',
    name: 'Inheritance',
    description: 'You inherit $100.',
    deck: 'community_chest',
    effect: 'collect',
    value: 100,
  },
};

// Community Chest also has advance_go, get_out_of_jail, and go_to_jail (shared with Chance)

/**
 * Get card definition by ID
 */
export function getCardDefinition(cardId: string): CardDefinition | null {
  return CARD_DEFINITIONS[cardId] || null;
}

/**
 * Calculate repairs cost for a player
 */
export function calculateRepairsCost(
  state: GameState,
  playerId: string,
  perHouse: number,
  perHotel: number
): number {
  let houses = 0;
  let hotels = 0;

  for (const property of Object.values(state.properties)) {
    if (property.ownerId === playerId) {
      if (property.houses === 5) {
        hotels++;
      } else {
        houses += property.houses;
      }
    }
  }

  return houses * perHouse + hotels * perHotel;
}

/**
 * Result of executing a card
 */
export interface CardExecutionResult {
  newState: GameState;
  events: GameEvent[];
  requiresLanding: boolean; // If true, need to handle landing on new position
  newPosition?: number;
}

/**
 * Execute a card's effect
 */
export function executeCardEffect(
  state: GameState,
  playerId: string,
  cardId: string,
  createEvent: (
    state: GameState,
    type: string,
    payload: Record<string, unknown>,
    playerId: string | null
  ) => GameEvent
): CardExecutionResult {
  const card = getCardDefinition(cardId);
  if (!card) {
    return {
      newState: { ...state, phase: 'turn_end' },
      events: [],
      requiresLanding: false,
    };
  }

  const player = state.players[playerId];
  const events: GameEvent[] = [];
  let newState = state;
  let requiresLanding = false;
  let newPosition: number | undefined;

  switch (card.effect) {
    case 'collect': {
      const amount = card.value || 0;
      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: {
            ...player,
            money: player.money + amount,
          },
        },
        phase: 'turn_end',
      };
      events.push(
        createEvent(newState, 'MONEY_COLLECTED', { amount, reason: card.name }, playerId)
      );
      break;
    }

    case 'pay': {
      const amount = card.value || 0;
      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: {
            ...player,
            money: player.money - amount,
          },
        },
        freeParkingPot: state.config.freeParkingEnabled
          ? state.freeParkingPot + amount
          : state.freeParkingPot,
        phase: 'turn_end',
      };
      events.push(
        createEvent(newState, 'MONEY_PAID', { amount, reason: card.name }, playerId)
      );
      break;
    }

    case 'collect_from_each': {
      const amount = card.value || 0;
      const activePlayers = state.playerOrder.filter(
        (id) => id !== playerId && !state.players[id].isBankrupt
      );
      const totalCollected = amount * activePlayers.length;

      const updatedPlayers = { ...state.players };
      for (const otherId of activePlayers) {
        updatedPlayers[otherId] = {
          ...updatedPlayers[otherId],
          money: updatedPlayers[otherId].money - amount,
        };
      }
      updatedPlayers[playerId] = {
        ...updatedPlayers[playerId],
        money: updatedPlayers[playerId].money + totalCollected,
      };

      newState = {
        ...state,
        players: updatedPlayers,
        phase: 'turn_end',
      };
      events.push(
        createEvent(
          newState,
          'COLLECTED_FROM_PLAYERS',
          { amountEach: amount, total: totalCollected, reason: card.name },
          playerId
        )
      );
      break;
    }

    case 'pay_each_player': {
      const amount = card.value || 0;
      const activePlayers = state.playerOrder.filter(
        (id) => id !== playerId && !state.players[id].isBankrupt
      );
      const totalPaid = amount * activePlayers.length;

      const updatedPlayers = { ...state.players };
      updatedPlayers[playerId] = {
        ...updatedPlayers[playerId],
        money: updatedPlayers[playerId].money - totalPaid,
      };
      for (const otherId of activePlayers) {
        updatedPlayers[otherId] = {
          ...updatedPlayers[otherId],
          money: updatedPlayers[otherId].money + amount,
        };
      }

      newState = {
        ...state,
        players: updatedPlayers,
        phase: 'turn_end',
      };
      events.push(
        createEvent(
          newState,
          'PAID_TO_PLAYERS',
          { amountEach: amount, total: totalPaid, reason: card.name },
          playerId
        )
      );
      break;
    }

    case 'repairs': {
      const cost = calculateRepairsCost(
        state,
        playerId,
        card.perHouse || 0,
        card.perHotel || 0
      );
      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: {
            ...player,
            money: player.money - cost,
          },
        },
        freeParkingPot: state.config.freeParkingEnabled
          ? state.freeParkingPot + cost
          : state.freeParkingPot,
        phase: 'turn_end',
      };
      events.push(
        createEvent(newState, 'REPAIRS_PAID', { amount: cost, reason: card.name }, playerId)
      );
      break;
    }

    case 'move_to': {
      let destination: number;
      const currentPosition = player.position;

      if (card.destination === 'go') {
        destination = GO_POSITION;
      } else if (card.destination === 'nearest_railroad') {
        destination = getNearestRailroad(currentPosition);
      } else if (card.destination === 'nearest_utility') {
        destination = getNearestUtility(currentPosition);
      } else {
        destination = card.destination as number;
      }

      // Check if passing GO
      const passedGo = card.collectGoOnPass && wouldPassGo(currentPosition, getSpacesToDestination(currentPosition, destination));
      let updatedPlayer = {
        ...player,
        position: destination,
      };

      if (passedGo) {
        updatedPlayer = {
          ...updatedPlayer,
          money: updatedPlayer.money + state.config.goSalary,
          timesPassedGo: updatedPlayer.timesPassedGo + 1,
        };
        events.push(
          createEvent(state, 'PASSED_GO', { amount: state.config.goSalary }, playerId)
        );
      }

      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        phase: 'landed',
      };

      events.push(
        createEvent(
          newState,
          'PLAYER_MOVED',
          { from: currentPosition, to: destination, reason: card.name, passedGo },
          playerId
        )
      );

      requiresLanding = true;
      newPosition = destination;
      break;
    }

    case 'move_back': {
      const spaces = card.value || 0;
      const currentPosition = player.position;
      const destination = moveBack(currentPosition, spaces);

      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: {
            ...player,
            position: destination,
          },
        },
        phase: 'landed',
      };

      events.push(
        createEvent(
          newState,
          'PLAYER_MOVED',
          { from: currentPosition, to: destination, reason: card.name, passedGo: false },
          playerId
        )
      );

      requiresLanding = true;
      newPosition = destination;
      break;
    }

    case 'go_to_jail': {
      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: {
            ...player,
            position: JAIL_POSITION,
            inJail: true,
            jailTurns: 0,
          },
        },
        consecutiveDoubles: 0,
        phase: 'turn_end',
      };
      events.push(
        createEvent(newState, 'SENT_TO_JAIL', { reason: 'card' }, playerId)
      );
      break;
    }

    case 'get_out_of_jail': {
      newState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: {
            ...player,
            getOutOfJailCards: player.getOutOfJailCards + 1,
          },
        },
        phase: 'turn_end',
      };
      events.push(
        createEvent(newState, 'JAIL_CARD_RECEIVED', {}, playerId)
      );
      // Note: Don't add card back to discard pile - player keeps it
      break;
    }

    default:
      newState = { ...state, phase: 'turn_end' };
  }

  return { newState, events, requiresLanding, newPosition };
}

/**
 * Helper to calculate spaces to destination (going forward around board)
 */
function getSpacesToDestination(from: number, to: number): number {
  if (to > from) {
    return to - from;
  }
  return 40 - from + to;
}

/**
 * Draw a card from a deck, reshuffling discards if needed
 */
export function drawCard(
  deck: { cards: string[]; discarded: string[] },
  rng: { shuffle: <T>(arr: T[]) => T[] }
): { cardId: string; newDeck: { cards: string[]; discarded: string[] } } {
  let cards = [...deck.cards];
  let discarded = [...deck.discarded];

  // Reshuffle if deck is empty
  if (cards.length === 0) {
    cards = rng.shuffle(discarded);
    discarded = [];
  }

  const cardId = cards.shift()!;

  return {
    cardId,
    newDeck: { cards, discarded },
  };
}

/**
 * Return a card to the discard pile (unless it's a Get Out of Jail Free card)
 */
export function discardCard(
  deck: { cards: string[]; discarded: string[] },
  cardId: string
): { cards: string[]; discarded: string[] } {
  // Get Out of Jail Free cards are kept by the player, not discarded
  if (cardId === 'get_out_of_jail') {
    return deck;
  }

  return {
    cards: deck.cards,
    discarded: [...deck.discarded, cardId],
  };
}
