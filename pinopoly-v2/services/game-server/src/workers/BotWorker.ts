/**
 * Bot Worker
 * Handles AI player decision making in a non-blocking way
 * Uses BullMQ for job processing
 */

import { Worker, Queue, Job } from 'bullmq';
import { config } from '../config';
import type { GameState, PlayerState, GameAction } from '@pinopoly/game-engine';
import { ActionTypes } from '@pinopoly/game-engine';

// Bot job types
export interface BotTurnJob {
  gameId: string;
  playerId: string;
  playerState: PlayerState;
  gameState: GameState;
  turnNumber: number;
}

export interface BotDecision {
  action: GameAction;
  thinkingTimeMs: number;
  reasoning?: string;
}

// Bot personality weights
interface PersonalityWeights {
  riskTolerance: number;      // 0-1: How willing to take risks
  propertyAffinity: number;   // 0-1: How much they want to buy properties
  monopolyFocus: number;      // 0-1: How much they prioritize completing monopolies
  developmentSpeed: number;   // 0-1: How quickly they build houses/hotels
  cashReserve: number;        // 0-1: How much cash they like to keep
  tradeWillingness: number;   // 0-1: How willing to make trades
}

// Bot personalities matching original Python implementation
const PERSONALITIES: Record<string, PersonalityWeights> = {
  conservative: {
    riskTolerance: 0.2,
    propertyAffinity: 0.5,
    monopolyFocus: 0.4,
    developmentSpeed: 0.3,
    cashReserve: 0.8,
    tradeWillingness: 0.3,
  },
  aggressive: {
    riskTolerance: 0.9,
    propertyAffinity: 0.9,
    monopolyFocus: 0.7,
    developmentSpeed: 0.9,
    cashReserve: 0.2,
    tradeWillingness: 0.7,
  },
  strategic: {
    riskTolerance: 0.5,
    propertyAffinity: 0.7,
    monopolyFocus: 0.9,
    developmentSpeed: 0.6,
    cashReserve: 0.5,
    tradeWillingness: 0.6,
  },
  opportunistic: {
    riskTolerance: 0.7,
    propertyAffinity: 0.6,
    monopolyFocus: 0.5,
    developmentSpeed: 0.5,
    cashReserve: 0.4,
    tradeWillingness: 0.9,
  },
  shark: {
    riskTolerance: 0.8,
    propertyAffinity: 0.8,
    monopolyFocus: 0.6,
    developmentSpeed: 0.7,
    cashReserve: 0.3,
    tradeWillingness: 0.8,
  },
  investor: {
    riskTolerance: 0.4,
    propertyAffinity: 0.8,
    monopolyFocus: 0.7,
    developmentSpeed: 0.4,
    cashReserve: 0.6,
    tradeWillingness: 0.5,
  },
};

/**
 * Get personality weights for a bot
 */
function getPersonalityWeights(personality: string): PersonalityWeights {
  return PERSONALITIES[personality] || PERSONALITIES.conservative;
}

/**
 * Calculate property value score for purchasing decisions
 */
function calculatePropertyScore(
  propertyPosition: number,
  gameState: GameState,
  weights: PersonalityWeights,
  playerMoney: number
): number {
  const property = gameState.properties[propertyPosition];
  if (!property || property.ownerId) return 0;

  const { price = 0, group } = property;

  // Base affordability score
  const affordabilityRatio = playerMoney / price;
  if (affordabilityRatio < 1) return 0;

  // Check monopoly potential
  const sameColorProperties = Object.values(gameState.properties).filter(
    p => p.group === group
  );
  const ownedSameColor = sameColorProperties.filter(
    p => p.ownerId === gameState.playerOrder[gameState.currentPlayerIndex]
  ).length;

  const monopolyBonus = ownedSameColor > 0 ?
    (ownedSameColor / sameColorProperties.length) * weights.monopolyFocus : 0;

  // Cash reserve consideration
  const cashAfterPurchase = playerMoney - price;
  const reserveScore = Math.min(cashAfterPurchase / gameState.config.startingMoney, 1);
  const reservePenalty = reserveScore < weights.cashReserve ?
    (weights.cashReserve - reserveScore) : 0;

  // Final score
  return (
    weights.propertyAffinity * 0.4 +
    monopolyBonus * 0.4 +
    (1 - reservePenalty) * 0.2
  );
}

/**
 * Decide whether to buy property
 */
function shouldBuyProperty(
  gameState: GameState,
  playerState: PlayerState,
  weights: PersonalityWeights
): boolean {
  const propertyPosition = playerState.position;
  const score = calculatePropertyScore(
    propertyPosition,
    gameState,
    weights,
    playerState.money
  );

  // Compare score against risk tolerance threshold
  const threshold = 1 - weights.riskTolerance;
  return score > threshold * 0.5;
}

/**
 * Decide whether to build houses
 */
function shouldBuildHouse(
  gameState: GameState,
  playerState: PlayerState,
  weights: PersonalityWeights
): { shouldBuild: boolean; propertyPosition?: number } {
  // Find properties where we can build
  const ownedProperties = Object.entries(gameState.properties)
    .filter(([_, p]) => p.ownerId === playerState.id && p.group)
    .map(([pos, p]) => ({ position: parseInt(pos), property: p }));

  if (ownedProperties.length === 0) {
    return { shouldBuild: false };
  }

  // Group by color
  const colorGroups = new Map<string, typeof ownedProperties>();
  for (const item of ownedProperties) {
    const color = item.property.group!;
    if (!colorGroups.has(color)) {
      colorGroups.set(color, []);
    }
    colorGroups.get(color)!.push(item);
  }

  // Find monopolies (all properties of a color owned)
  for (const [color, properties] of colorGroups) {
    const totalInColor = Object.values(gameState.properties).filter(
      p => p.group === color
    ).length;

    if (properties.length === totalInColor) {
      // We have a monopoly, consider building
      const buildableProperty = properties.find(
        p => (p.property.houses || 0) < 5 && p.property.houseCost
      );

      if (buildableProperty) {
        const cost = buildableProperty.property.houseCost || 0;
        const affordability = playerState.money / cost;

        // Check if building fits our strategy
        if (affordability > (1 + weights.cashReserve) &&
            Math.random() < weights.developmentSpeed) {
          return { shouldBuild: true, propertyPosition: buildableProperty.position };
        }
      }
    }
  }

  return { shouldBuild: false };
}

/**
 * Make a decision for a bot's turn
 */
export function makeBotDecision(job: BotTurnJob): BotDecision {
  const startTime = Date.now();
  const { gameState, playerState } = job;

  // Get personality from player state
  const personality = playerState.botPersonality || 'conservative';
  const weights = getPersonalityWeights(personality);

  // Add artificial "thinking" delay for realism
  const baseThinkingTime = 500 + Math.random() * 1500;

  // Determine current game phase and make appropriate decision
  const phase = gameState.phase;

  let action: GameAction;
  let reasoning: string;

  switch (phase) {
    case 'pre_roll': {
      // Bot needs to roll dice
      action = {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: playerState.id },
      };
      reasoning = 'Rolling dice to start turn';
      break;
    }

    case 'buy_decision':
    case 'landed': {
      // Landed on property - decide to buy or not
      const property = gameState.properties[playerState.position];

      if (property && !property.ownerId && property.price) {
        if (shouldBuyProperty(gameState, playerState, weights)) {
          action = {
            type: ActionTypes.BUY_PROPERTY,
            payload: {
              playerId: playerState.id,
              propertyId: playerState.position,
            },
          };
          reasoning = `Buying property at position ${playerState.position} based on ${personality} strategy`;
        } else {
          action = {
            type: ActionTypes.END_TURN,
            payload: { playerId: playerState.id },
          };
          reasoning = `Declining to buy property - ${personality} strategy prefers to conserve cash`;
        }
      } else {
        action = {
          type: ActionTypes.END_TURN,
          payload: { playerId: playerState.id },
        };
        reasoning = 'No action needed, ending turn';
      }
      break;
    }

    case 'development': {
      // Opportunity to build before rolling
      const buildDecision = shouldBuildHouse(gameState, playerState, weights);

      if (buildDecision.shouldBuild && buildDecision.propertyPosition !== undefined) {
        action = {
          type: ActionTypes.BUILD_HOUSE,
          payload: {
            playerId: playerState.id,
            propertyId: buildDecision.propertyPosition,
          },
        };
        reasoning = `Building house on property ${buildDecision.propertyPosition}`;
      } else {
        // Ready to roll
        action = {
          type: ActionTypes.ROLL_DICE,
          payload: { playerId: playerState.id },
        };
        reasoning = 'No pre-roll actions, proceeding to roll';
      }
      break;
    }

    case 'jail_decision': {
      // In jail - decide whether to pay or try to roll
      if (weights.riskTolerance > 0.5 && playerState.money > 200) {
        // Risk-takers pay to get out quickly
        action = {
          type: ActionTypes.PAY_JAIL_FINE,
          payload: { playerId: playerState.id },
        };
        reasoning = 'Paying jail fine to get back in the game quickly';
      } else {
        // Try to roll doubles
        action = {
          type: ActionTypes.ROLL_DICE,
          payload: { playerId: playerState.id },
        };
        reasoning = 'Attempting to roll doubles to escape jail';
      }
      break;
    }

    default: {
      // Default action - end turn
      action = {
        type: ActionTypes.END_TURN,
        payload: { playerId: playerState.id },
      };
      reasoning = `Unknown phase "${phase}", ending turn`;
    }
  }

  return {
    action,
    thinkingTimeMs: Date.now() - startTime + baseThinkingTime,
    reasoning,
  };
}

/**
 * Create the bot worker queue
 */
export function createBotQueue(): Queue<BotTurnJob> {
  return new Queue<BotTurnJob>('bot-turns', {
    connection: {
      host: config.redis.host,
      port: config.redis.port,
    },
  });
}

/**
 * Create the bot worker
 */
export function createBotWorker(
  onDecision: (gameId: string, decision: BotDecision) => void
): Worker<BotTurnJob, BotDecision> {
  return new Worker<BotTurnJob, BotDecision>(
    'bot-turns',
    async (job: Job<BotTurnJob>) => {
      const decision = makeBotDecision(job.data);

      // Simulate thinking time
      await new Promise(resolve => setTimeout(resolve, decision.thinkingTimeMs));

      // Notify about the decision
      onDecision(job.data.gameId, decision);

      return decision;
    },
    {
      connection: {
        host: config.redis.host,
        port: config.redis.port,
      },
      concurrency: 5,
    }
  );
}
