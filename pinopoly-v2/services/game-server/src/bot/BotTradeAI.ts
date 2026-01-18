/**
 * Bot Trade AI
 *
 * Advanced AI system for bot trading decisions in Pinopoly.
 * Handles property valuation, trade proposal generation, and trade response evaluation.
 */

import type {
  GameState,
  PlayerState,
  PropertyState,
  TradeOffer,
  TradeState,
  BotPersonality,
  ColorGroup,
} from '@pinopoly/game-engine';

// =============================================================================
// TYPES
// =============================================================================

export type TradeDecision = 'accept' | 'reject' | 'counter';

export interface TradeEvaluation {
  decision: TradeDecision;
  receiveValue: number;
  giveValue: number;
  counterOffer?: {
    offer: TradeOffer;
    request: TradeOffer;
  };
  reason: string;
}

export interface TradeProposal {
  recipientId: string;
  offer: TradeOffer;
  request: TradeOffer;
  priority: number; // Higher = more urgent/beneficial
}

export interface PropertyValuation {
  baseValue: number;
  strategicValue: number;
  totalValue: number;
  reasons: string[];
}

// =============================================================================
// PERSONALITY THRESHOLDS
// =============================================================================

// Multiplier applied to give value - higher = more demanding
const PERSONALITY_THRESHOLDS: Record<BotPersonality, number> = {
  conservative: 1.2,    // Needs favorable trades (receive 20% more than give)
  aggressive: 0.85,     // Accepts slightly unfair trades to accumulate
  strategic: 1.0,       // Balanced, considers blocking value
  opportunistic: 0.9,   // Slightly aggressive, seizes opportunities
  shark: 1.3,           // Only accepts winning trades
  investor: 1.1,        // Slightly conservative, focuses on value
};

// Chance of proposing a trade per turn (0-1)
const TRADE_WILLINGNESS: Record<BotPersonality, number> = {
  conservative: 0.15,
  aggressive: 0.4,
  strategic: 0.3,
  opportunistic: 0.35,
  shark: 0.25,
  investor: 0.2,
};

// High-traffic positions (more valuable for rent collection)
const HIGH_TRAFFIC_POSITIONS = new Set([
  6, 8, 9,      // Light blue
  11, 13, 14,   // Pink
  16, 18, 19,   // Orange (most landed on!)
  21, 23, 24,   // Red
]);

// =============================================================================
// PROPERTY VALUATION
// =============================================================================

/**
 * Get all properties in a color group
 */
function getColorGroupProperties(
  state: GameState,
  group: ColorGroup
): PropertyState[] {
  return Object.values(state.properties).filter(p => p.group === group);
}

/**
 * Count how many properties of a color group a player owns
 */
function countOwnedInGroup(
  state: GameState,
  playerId: string,
  group: ColorGroup
): number {
  return getColorGroupProperties(state, group)
    .filter(p => p.ownerId === playerId)
    .length;
}

/**
 * Check if player has monopoly (owns all properties in a color group)
 */
function hasMonopoly(
  state: GameState,
  playerId: string,
  group: ColorGroup
): boolean {
  const groupProps = getColorGroupProperties(state, group);
  return groupProps.every(p => p.ownerId === playerId);
}

/**
 * Check how close a player is to completing a monopoly
 */
function monopolyProgress(
  state: GameState,
  playerId: string,
  group: ColorGroup
): { owned: number; total: number; remaining: number } {
  const groupProps = getColorGroupProperties(state, group);
  const owned = groupProps.filter(p => p.ownerId === playerId).length;
  return {
    owned,
    total: groupProps.length,
    remaining: groupProps.length - owned,
  };
}

/**
 * Evaluate the strategic value of a property for a specific player
 */
export function evaluatePropertyValue(
  propertyId: number,
  forPlayerId: string,
  state: GameState
): PropertyValuation {
  const property = state.properties[propertyId];
  if (!property) {
    return { baseValue: 0, strategicValue: 0, totalValue: 0, reasons: ['Property not found'] };
  }

  const reasons: string[] = [];
  let strategicMultiplier = 1.0;

  // Base value is the purchase price
  const baseValue = property.price;

  // Railroad synergy
  if (property.type === 'railroad') {
    const ownedRailroads = Object.values(state.properties)
      .filter(p => p.type === 'railroad' && p.ownerId === forPlayerId)
      .length;
    if (ownedRailroads >= 1) {
      strategicMultiplier += 0.5 * ownedRailroads;
      reasons.push(`Railroad synergy (+${50 * ownedRailroads}% for ${ownedRailroads} owned)`);
    }
  }

  // Utility synergy
  if (property.type === 'utility') {
    const ownedUtilities = Object.values(state.properties)
      .filter(p => p.type === 'utility' && p.ownerId === forPlayerId)
      .length;
    if (ownedUtilities === 1) {
      strategicMultiplier += 0.5;
      reasons.push('Utility synergy (+50% for owning one utility)');
    }
  }

  // Color group properties
  if (property.group) {
    const progress = monopolyProgress(state, forPlayerId, property.group);

    // Completes monopoly - HUGE value!
    if (progress.remaining === 1 && property.ownerId !== forPlayerId) {
      strategicMultiplier += 3.0;
      reasons.push('COMPLETES MONOPOLY (+300%)');
    }
    // Gets closer to monopoly
    else if (progress.owned > 0 && progress.remaining > 1) {
      strategicMultiplier += 0.5 * progress.owned;
      reasons.push(`Monopoly progress (+${50 * progress.owned}% for ${progress.owned}/${progress.total})`);
    }

    // Check if this property blocks an opponent's monopoly
    for (const [opponentId, opponent] of Object.entries(state.players)) {
      if (opponentId === forPlayerId || opponent.isBankrupt) continue;

      const opponentProgress = monopolyProgress(state, opponentId, property.group);
      if (opponentProgress.remaining === 1 && property.ownerId !== opponentId) {
        strategicMultiplier += 2.0;
        reasons.push(`Blocks ${opponent.name}'s monopoly (+200%)`);
        break;
      }
    }
  }

  // High-traffic position bonus
  if (HIGH_TRAFFIC_POSITIONS.has(property.position)) {
    strategicMultiplier += 0.25;
    reasons.push('High-traffic position (+25%)');
  }

  // Mortgaged penalty
  if (property.isMortgaged) {
    strategicMultiplier *= 0.5;
    reasons.push('Mortgaged (-50%)');
  }

  // Development bonus (if houses/hotels exist)
  if (property.houses > 0) {
    const developmentValue = property.houseCost * property.houses * 0.5;
    strategicMultiplier += developmentValue / baseValue;
    reasons.push(`${property.houses} houses (+${Math.round((developmentValue / baseValue) * 100)}%)`);
  }

  const strategicValue = Math.round(baseValue * (strategicMultiplier - 1));
  const totalValue = Math.round(baseValue * strategicMultiplier);

  return {
    baseValue,
    strategicValue,
    totalValue,
    reasons,
  };
}

/**
 * Calculate total value of a trade offer for a player
 */
export function evaluateTradeOfferValue(
  offer: TradeOffer,
  forPlayerId: string,
  state: GameState
): number {
  let totalValue = offer.money;

  // Value properties
  for (const propId of offer.propertyIds) {
    const valuation = evaluatePropertyValue(propId, forPlayerId, state);
    totalValue += valuation.totalValue;
  }

  // Value Get Out of Jail cards (roughly $50 each)
  totalValue += offer.getOutOfJailCards * 50;

  return totalValue;
}

// =============================================================================
// TRADE RESPONSE EVALUATION
// =============================================================================

/**
 * Check if accepting a trade would give the opponent a monopoly
 */
function wouldGiveOpponentMonopoly(
  trade: TradeState,
  botId: string,
  state: GameState
): boolean {
  // Properties bot would give up
  const offer = trade.proposerId === botId ? trade.offer : trade.request;

  for (const propId of offer.propertyIds) {
    const property = state.properties[propId];
    if (!property?.group) continue;

    const opponentId = trade.proposerId === botId ? trade.recipientId : trade.proposerId;
    const afterTradeOwned = countOwnedInGroup(state, opponentId, property.group) + 1;
    const groupSize = getColorGroupProperties(state, property.group).length;

    if (afterTradeOwned === groupSize) {
      return true;
    }
  }

  return false;
}

/**
 * Check if accepting a trade would give the bot a monopoly
 */
function wouldGiveBotMonopoly(
  trade: TradeState,
  botId: string,
  state: GameState
): boolean {
  // Properties bot would receive
  const request = trade.proposerId === botId ? trade.request : trade.offer;

  for (const propId of request.propertyIds) {
    const property = state.properties[propId];
    if (!property?.group) continue;

    const afterTradeOwned = countOwnedInGroup(state, botId, property.group) + 1;
    const groupSize = getColorGroupProperties(state, property.group).length;

    if (afterTradeOwned === groupSize) {
      return true;
    }
  }

  return false;
}

/**
 * Evaluate an incoming trade offer and decide whether to accept, reject, or counter
 */
export function evaluateTrade(
  trade: TradeState,
  botId: string,
  state: GameState
): TradeEvaluation {
  const bot = state.players[botId];
  if (!bot || !bot.isBot || !bot.botPersonality) {
    return {
      decision: 'reject',
      receiveValue: 0,
      giveValue: 0,
      reason: 'Not a valid bot',
    };
  }

  const personality = bot.botPersonality;
  const threshold = PERSONALITY_THRESHOLDS[personality];

  // What the bot would receive
  const receive = trade.proposerId === botId ? trade.request : trade.offer;
  // What the bot would give
  const give = trade.proposerId === botId ? trade.offer : trade.request;

  // Calculate values
  let receiveValue = evaluateTradeOfferValue(receive, botId, state);
  let giveValue = evaluateTradeOfferValue(give, botId, state);

  // Strategic modifiers
  const givesOpponentMonopoly = wouldGiveOpponentMonopoly(trade, botId, state);
  const givesBotMonopoly = wouldGiveBotMonopoly(trade, botId, state);

  if (givesOpponentMonopoly) {
    giveValue *= 2; // Heavily penalize
  }

  if (givesBotMonopoly) {
    receiveValue *= 1.5; // Bonus for completing monopoly
  }

  // Decision logic
  const ratio = receiveValue / giveValue;

  if (ratio >= threshold) {
    return {
      decision: 'accept',
      receiveValue,
      giveValue,
      reason: `Trade ratio ${ratio.toFixed(2)} meets threshold ${threshold}`,
    };
  }

  // Check if close enough to counter
  if (ratio >= threshold * 0.7 && ratio < threshold) {
    // Calculate money difference needed to make it fair
    const valueDiff = Math.round(giveValue * threshold - receiveValue);

    // Counter offer: same properties, adjust money
    const counterOffer: TradeOffer = { ...receive };
    const counterRequest: TradeOffer = { ...give };

    if (receive.money >= valueDiff) {
      // They offered enough money, we want more properties
      // (Complex counter - skip for now, just adjust money)
      counterOffer.money = receive.money + valueDiff;
    } else {
      // Request more money from them
      counterOffer.money = receive.money + valueDiff;
    }

    return {
      decision: 'counter',
      receiveValue,
      giveValue,
      counterOffer: {
        offer: counterRequest, // What we give
        request: counterOffer, // What we want
      },
      reason: `Trade ratio ${ratio.toFixed(2)} is close, countering with $${valueDiff} adjustment`,
    };
  }

  return {
    decision: 'reject',
    receiveValue,
    giveValue,
    reason: `Trade ratio ${ratio.toFixed(2)} below threshold ${threshold}`,
  };
}

// =============================================================================
// TRADE PROPOSAL GENERATION
// =============================================================================

/**
 * Find properties the bot needs to complete color groups
 */
function findNeededProperties(
  botId: string,
  state: GameState
): Array<{ property: PropertyState; priority: number; ownerId: string }> {
  const bot = state.players[botId];
  if (!bot) return [];

  const needed: Array<{ property: PropertyState; priority: number; ownerId: string }> = [];

  // Get all color groups the bot has at least one property in
  const botGroups = new Set<ColorGroup>();
  for (const prop of Object.values(state.properties)) {
    if (prop.ownerId === botId && prop.group) {
      botGroups.add(prop.group);
    }
  }

  // For each group, find missing properties
  for (const group of botGroups) {
    const progress = monopolyProgress(state, botId, group);

    if (progress.remaining > 0 && progress.remaining <= 2) {
      // Find properties we need
      const groupProps = getColorGroupProperties(state, group);
      for (const prop of groupProps) {
        if (prop.ownerId && prop.ownerId !== botId && !state.players[prop.ownerId]?.isBankrupt) {
          needed.push({
            property: prop,
            priority: progress.remaining === 1 ? 10 : 5, // Higher priority if one away from monopoly
            ownerId: prop.ownerId,
          });
        }
      }
    }
  }

  return needed;
}

/**
 * Find properties the bot owns that others might want
 */
function findTradableProperties(
  botId: string,
  state: GameState
): Array<{ property: PropertyState; priority: number }> {
  const tradable: Array<{ property: PropertyState; priority: number }> = [];

  for (const prop of Object.values(state.properties)) {
    if (prop.ownerId !== botId || !prop.group) continue;
    if (prop.houses > 0) continue; // Don't trade developed properties

    const progress = monopolyProgress(state, botId, prop.group);

    // Don't trade if we have the monopoly
    if (progress.remaining === 0) continue;

    // Lower priority if we're close to completing
    if (progress.remaining === 1) continue; // Don't trade if one away

    tradable.push({
      property: prop,
      priority: progress.remaining, // Higher remaining = more willing to trade
    });
  }

  return tradable;
}

/**
 * Generate trade proposals for a bot
 * Returns a list of potential trades sorted by priority
 */
export function generateTradeProposals(
  botId: string,
  state: GameState
): TradeProposal[] {
  const bot = state.players[botId];
  if (!bot || !bot.isBot || !bot.botPersonality) return [];

  // Check trade willingness based on personality
  // Random value should be LESS than willingness for the check to pass
  if (Math.random() >= TRADE_WILLINGNESS[bot.botPersonality]) {
    return [];
  }

  const proposals: TradeProposal[] = [];
  const neededProps = findNeededProperties(botId, state);
  const tradableProps = findTradableProperties(botId, state);

  // Try to find mutually beneficial trades
  for (const needed of neededProps) {
    const opponent = state.players[needed.ownerId];
    if (!opponent || opponent.isBankrupt) continue;

    // Find what we could offer in return
    for (const tradable of tradableProps) {
      // Check if opponent would want this property
      const opponentProgress = tradable.property.group
        ? monopolyProgress(state, needed.ownerId, tradable.property.group)
        : null;

      if (!opponentProgress || opponentProgress.owned === 0) continue;

      // Calculate fair trade values
      const weReceiveValue = evaluatePropertyValue(needed.property.id, botId, state).totalValue;
      const weGiveValue = evaluatePropertyValue(tradable.property.id, needed.ownerId, state).totalValue;

      // Calculate money needed to balance
      const moneyDiff = weReceiveValue - weGiveValue;

      const offer: TradeOffer = {
        money: Math.max(0, moneyDiff),
        propertyIds: [tradable.property.id],
        getOutOfJailCards: 0,
      };

      const request: TradeOffer = {
        money: Math.max(0, -moneyDiff),
        propertyIds: [needed.property.id],
        getOutOfJailCards: 0,
      };

      // Check if bot can afford this trade
      if (offer.money > bot.money * 0.5) continue; // Don't spend more than half our money

      proposals.push({
        recipientId: needed.ownerId,
        offer,
        request,
        priority: needed.priority + (opponentProgress.remaining === 1 ? 5 : 0),
      });
    }
  }

  // Sort by priority (highest first)
  proposals.sort((a, b) => b.priority - a.priority);

  return proposals;
}

/**
 * Check if a bot should respond to any pending trades
 * Returns the trade to respond to and the decision
 */
export function getPendingTradeResponse(
  botId: string,
  state: GameState
): { trade: TradeState; evaluation: TradeEvaluation } | null {
  const pendingTrades = state.activeTrades.filter(
    t => t.recipientId === botId && t.status === 'pending'
  );

  if (pendingTrades.length === 0) return null;

  // Evaluate the oldest pending trade
  const trade = pendingTrades[0];
  const evaluation = evaluateTrade(trade, botId, state);

  return { trade, evaluation };
}
