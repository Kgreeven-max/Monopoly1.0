/**
 * Main game reducer for Pinopoly
 * Pure function: (state, action) => [newState, events]
 * No side effects, deterministic, testable
 */

import type { GameState, GameEvent } from '../state/types';
import type { GameAction } from '../actions/types';
import { ActionTypes } from '../actions/types';
import { SeededRandom } from '../rng/SeededRandom';
import {
  calculateRent,
  canBuildHouse,
} from '../rules/property';
import {
  getNextPosition,
  wouldPassGo,
  JAIL_POSITION,
  GO_POSITION,
} from '../rules/movement';
import {
  drawCard,
  discardCard,
  executeCardEffect,
  getCardDefinition,
} from '../rules/cards';
import { createInitialState } from './initialState';

/**
 * Result of applying an action to game state
 */
export type ReducerResult = [GameState, GameEvent[]];

/**
 * Create a game event
 */
function createEvent(
  state: GameState,
  type: string,
  payload: Record<string, unknown>,
  playerId: string | null = null
): GameEvent {
  return {
    id: `${state.id}-${state.eventLog.length}`,
    type,
    payload,
    playerId,
    round: state.round,
    timestamp: Date.now(),
  };
}

/**
 * Main game reducer - processes all game actions
 */
export function gameReducer(
  state: GameState,
  action: GameAction
): ReducerResult {
  const events: GameEvent[] = [];

  switch (action.type) {
    // =========================================================================
    // GAME LIFECYCLE
    // =========================================================================

    case ActionTypes.INITIALIZE_GAME: {
      const { gameId, roomCode, config, seed } = action.payload;
      const newState = createInitialState(gameId, roomCode, config, seed);
      events.push(createEvent(newState, 'GAME_INITIALIZED', { config }));
      return [newState, events];
    }

    case ActionTypes.START_GAME: {
      if (state.status !== 'lobby') {
        throw new Error('Game can only be started from lobby');
      }
      if (Object.keys(state.players).length < 2) {
        throw new Error('Need at least 2 players to start');
      }

      // Shuffle player order
      const rng = new SeededRandom(state.rngState);
      const playerIds = Object.keys(state.players);
      const shuffledOrder = rng.shuffle(playerIds);

      const newState: GameState = {
        ...state,
        status: 'playing',
        playerOrder: shuffledOrder,
        currentPlayerIndex: 0,
        phase: 'pre_roll',
        round: 1,
        rngState: rng.getState(),
        startedAt: Date.now(),
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(newState, 'GAME_STARTED', {
          playerOrder: shuffledOrder,
        })
      );

      return [newState, events];
    }

    case ActionTypes.PAUSE_GAME: {
      if (state.status !== 'playing') {
        throw new Error('Can only pause a playing game');
      }

      const newState: GameState = {
        ...state,
        status: 'paused',
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(newState, 'GAME_PAUSED', {
          reason: action.payload.reason,
        })
      );

      return [newState, events];
    }

    case ActionTypes.RESUME_GAME: {
      if (state.status !== 'paused') {
        throw new Error('Can only resume a paused game');
      }

      const newState: GameState = {
        ...state,
        status: 'playing',
        lastActionAt: Date.now(),
      };

      events.push(createEvent(newState, 'GAME_RESUMED', {}));

      return [newState, events];
    }

    case ActionTypes.END_GAME: {
      const newState: GameState = {
        ...state,
        status: 'finished',
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(newState, 'GAME_ENDED', {
          reason: action.payload.reason,
          winnerId: action.payload.winnerId,
        })
      );

      return [newState, events];
    }

    // =========================================================================
    // LOBBY ACTIONS
    // =========================================================================

    case ActionTypes.ADD_PLAYER: {
      if (state.status !== 'lobby') {
        throw new Error('Can only add players in lobby');
      }

      const { playerId, name, token, color, socketId } = action.payload;

      if (state.players[playerId]) {
        throw new Error('Player already exists');
      }

      const playerCount = Object.keys(state.players).length;
      if (playerCount >= state.config.maxPlayers) {
        throw new Error('Game is full');
      }

      const newPlayer = {
        id: playerId,
        name,
        token,
        color,
        money: state.config.startingMoney,
        position: GO_POSITION,
        isBot: false,
        botPersonality: null,
        botDifficulty: null,
        inJail: false,
        jailTurns: 0,
        getOutOfJailCards: 0,
        isBankrupt: false,
        bankruptcyOrder: null,
        creditScore: 700,
        timesPassedGo: 0,
        loans: [],
        cds: [],
        helocs: [],
        isConnected: true,
        socketId: socketId ?? null,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: newPlayer,
        },
        playerOrder: [...state.playerOrder, playerId],
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(newState, 'PLAYER_JOINED', { player: newPlayer }, playerId)
      );

      return [newState, events];
    }

    case ActionTypes.ADD_BOT: {
      if (state.status !== 'lobby') {
        throw new Error('Can only add bots in lobby');
      }

      const { botId, name, token, color, personality, difficulty } =
        action.payload;

      const playerCount = Object.keys(state.players).length;
      if (playerCount >= state.config.maxPlayers) {
        throw new Error('Game is full');
      }

      const newBot = {
        id: botId,
        name,
        token,
        color,
        money: state.config.startingMoney,
        position: GO_POSITION,
        isBot: true,
        botPersonality: personality,
        botDifficulty: difficulty,
        inJail: false,
        jailTurns: 0,
        getOutOfJailCards: 0,
        isBankrupt: false,
        bankruptcyOrder: null,
        creditScore: 700,
        timesPassedGo: 0,
        loans: [],
        cds: [],
        helocs: [],
        isConnected: true,
        socketId: null,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [botId]: newBot,
        },
        playerOrder: [...state.playerOrder, botId],
        lastActionAt: Date.now(),
      };

      events.push(createEvent(newState, 'BOT_ADDED', { bot: newBot }));

      return [newState, events];
    }

    case ActionTypes.REMOVE_PLAYER: {
      if (state.status !== 'lobby') {
        throw new Error('Can only remove players in lobby');
      }

      const { playerId } = action.payload;
      const { [playerId]: removed, ...remainingPlayers } = state.players;

      if (!removed) {
        throw new Error('Player not found');
      }

      const newState: GameState = {
        ...state,
        players: remainingPlayers,
        playerOrder: state.playerOrder.filter(id => id !== playerId),
        lastActionAt: Date.now(),
      };

      events.push(createEvent(newState, 'PLAYER_LEFT', { playerId }, playerId));

      return [newState, events];
    }

    // =========================================================================
    // TURN ACTIONS
    // =========================================================================

    case ActionTypes.ROLL_DICE: {
      const { playerId } = action.payload;
      const currentPlayer = getCurrentPlayer(state);

      if (currentPlayer.id !== playerId) {
        throw new Error('Not your turn');
      }

      if (state.phase !== 'pre_roll' && state.phase !== 'jail_decision') {
        throw new Error(`Cannot roll in phase: ${state.phase}`);
      }

      // Handle jail roll
      if (currentPlayer.inJail && state.phase === 'jail_decision') {
        return handleJailRoll(state, playerId, events);
      }

      // Normal roll
      const rng = new SeededRandom(state.rngState);
      const diceRoll = rng.rollDice();

      events.push(
        createEvent(
          state,
          'DICE_ROLLED',
          {
            dice: diceRoll,
          },
          playerId
        )
      );

      // Check for third consecutive doubles (go to jail)
      const newConsecutiveDoubles = diceRoll.isDoubles
        ? state.consecutiveDoubles + 1
        : 0;

      if (newConsecutiveDoubles >= 3) {
        return handleGoToJail(
          { ...state, rngState: rng.getState() },
          playerId,
          'three_doubles',
          events
        );
      }

      // Calculate new position
      const oldPosition = currentPlayer.position;
      const newPosition = getNextPosition(oldPosition, diceRoll.total);
      const passedGo = wouldPassGo(oldPosition, diceRoll.total);

      // Update player position and money
      let updatedPlayer = {
        ...currentPlayer,
        position: newPosition,
      };

      if (passedGo) {
        updatedPlayer = {
          ...updatedPlayer,
          money: updatedPlayer.money + state.config.goSalary,
          timesPassedGo: updatedPlayer.timesPassedGo + 1,
        };

        events.push(
          createEvent(
            state,
            'PASSED_GO',
            {
              amount: state.config.goSalary,
            },
            playerId
          )
        );
      }

      events.push(
        createEvent(
          state,
          'PLAYER_MOVED',
          {
            from: oldPosition,
            to: newPosition,
            spaces: diceRoll.total,
            passedGo,
          },
          playerId
        )
      );

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        lastDiceRoll: diceRoll,
        consecutiveDoubles: newConsecutiveDoubles,
        rngState: rng.getState(),
        phase: 'landed',
        lastActionAt: Date.now(),
      };

      // Handle landing on space
      return handleLanding(newState, playerId, newPosition, events);
    }

    case ActionTypes.END_TURN: {
      const { playerId } = action.payload;
      const currentPlayer = getCurrentPlayer(state);

      if (currentPlayer.id !== playerId) {
        throw new Error('Not your turn');
      }

      // Allow doubles to roll again
      if (state.lastDiceRoll?.isDoubles && !currentPlayer.inJail) {
        const newState: GameState = {
          ...state,
          phase: 'pre_roll',
          lastActionAt: Date.now(),
        };

        events.push(
          createEvent(newState, 'EXTRA_TURN', { reason: 'doubles' }, playerId)
        );

        return [newState, events];
      }

      // Advance to next player
      return advanceToNextPlayer(state, events);
    }

    // =========================================================================
    // PROPERTY ACTIONS
    // =========================================================================

    case ActionTypes.BUY_PROPERTY: {
      const { playerId, propertyId } = action.payload;
      const player = state.players[playerId];
      const property = state.properties[propertyId];

      if (!player) throw new Error('Player not found');
      if (!property) throw new Error('Property not found');
      if (property.ownerId) throw new Error('Property already owned');
      if (player.money < property.price) throw new Error('Insufficient funds');
      if (player.position !== property.position) {
        throw new Error('Player not on property');
      }

      const updatedPlayer = {
        ...player,
        money: player.money - property.price,
      };

      const updatedProperty = {
        ...property,
        ownerId: playerId,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        properties: {
          ...state.properties,
          [propertyId]: updatedProperty,
        },
        phase: 'turn_end',
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'PROPERTY_BOUGHT',
          {
            propertyId,
            price: property.price,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.DECLINE_PROPERTY: {
      const { playerId, propertyId } = action.payload;

      if (state.config.auctionRequired) {
        // Start auction
        return handleStartAuction(state, propertyId, events);
      }

      // No auction, just end turn phase
      const newState: GameState = {
        ...state,
        phase: 'turn_end',
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'PROPERTY_DECLINED',
          {
            propertyId,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.BUILD_HOUSE: {
      const { playerId, propertyId } = action.payload;
      const player = state.players[playerId];
      const property = state.properties[propertyId];

      if (!player) throw new Error('Player not found');
      if (!property) throw new Error('Property not found');
      if (property.ownerId !== playerId) throw new Error('Not your property');
      if (property.houses >= 5) throw new Error('Property at max development');
      if (player.money < property.houseCost) {
        throw new Error('Insufficient funds');
      }

      // Check if can build (even building rule)
      if (!canBuildHouse(state, propertyId)) {
        throw new Error('Cannot build here - must build evenly');
      }

      const updatedPlayer = {
        ...player,
        money: player.money - property.houseCost,
      };

      const updatedProperty = {
        ...property,
        houses: property.houses + 1,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        properties: {
          ...state.properties,
          [propertyId]: updatedProperty,
        },
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'HOUSE_BUILT',
          {
            propertyId,
            houses: updatedProperty.houses,
            isHotel: updatedProperty.houses === 5,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.MORTGAGE_PROPERTY: {
      const { playerId, propertyId } = action.payload;
      const player = state.players[playerId];
      const property = state.properties[propertyId];

      if (!player) throw new Error('Player not found');
      if (!property) throw new Error('Property not found');
      if (property.ownerId !== playerId) throw new Error('Not your property');
      if (property.isMortgaged) throw new Error('Already mortgaged');
      if (property.houses > 0) throw new Error('Must sell houses first');

      const updatedPlayer = {
        ...player,
        money: player.money + property.mortgageValue,
      };

      const updatedProperty = {
        ...property,
        isMortgaged: true,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        properties: {
          ...state.properties,
          [propertyId]: updatedProperty,
        },
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'PROPERTY_MORTGAGED',
          {
            propertyId,
            amount: property.mortgageValue,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.UNMORTGAGE_PROPERTY: {
      const { playerId, propertyId } = action.payload;
      const player = state.players[playerId];
      const property = state.properties[propertyId];

      if (!player) throw new Error('Player not found');
      if (!property) throw new Error('Property not found');
      if (property.ownerId !== playerId) throw new Error('Not your property');
      if (!property.isMortgaged) throw new Error('Not mortgaged');

      const unmortgageCost = Math.floor(property.mortgageValue * 1.1); // 10% interest
      if (player.money < unmortgageCost) {
        throw new Error('Insufficient funds');
      }

      const updatedPlayer = {
        ...player,
        money: player.money - unmortgageCost,
      };

      const updatedProperty = {
        ...property,
        isMortgaged: false,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        properties: {
          ...state.properties,
          [propertyId]: updatedProperty,
        },
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'PROPERTY_UNMORTGAGED',
          {
            propertyId,
            cost: unmortgageCost,
          },
          playerId
        )
      );

      return [newState, events];
    }

    // =========================================================================
    // JAIL ACTIONS
    // =========================================================================

    case ActionTypes.PAY_JAIL_FINE: {
      const { playerId } = action.payload;
      const player = state.players[playerId];

      if (!player) throw new Error('Player not found');
      if (!player.inJail) throw new Error('Player not in jail');
      if (player.money < state.config.jailFine) {
        throw new Error('Insufficient funds');
      }

      const updatedPlayer = {
        ...player,
        money: player.money - state.config.jailFine,
        inJail: false,
        jailTurns: 0,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        phase: 'pre_roll',
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'JAIL_FINE_PAID',
          {
            amount: state.config.jailFine,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.USE_JAIL_CARD: {
      const { playerId } = action.payload;
      const player = state.players[playerId];

      if (!player) throw new Error('Player not found');
      if (!player.inJail) throw new Error('Player not in jail');
      if (player.getOutOfJailCards < 1) throw new Error('No jail cards');

      const updatedPlayer = {
        ...player,
        inJail: false,
        jailTurns: 0,
        getOutOfJailCards: player.getOutOfJailCards - 1,
      };

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        phase: 'pre_roll',
        lastActionAt: Date.now(),
      };

      events.push(createEvent(newState, 'JAIL_CARD_USED', {}, playerId));

      return [newState, events];
    }

    case ActionTypes.ROLL_FOR_DOUBLES: {
      const { playerId } = action.payload;
      const currentPlayer = getCurrentPlayer(state);

      if (currentPlayer.id !== playerId) {
        throw new Error('Not your turn');
      }

      if (!currentPlayer.inJail) {
        throw new Error('Player not in jail');
      }

      if (state.phase !== 'jail_decision') {
        throw new Error('Cannot roll for doubles in current phase');
      }

      return handleJailRoll(state, playerId, events);
    }

    // =========================================================================
    // CARD ACTIONS
    // =========================================================================

    case ActionTypes.DRAW_CARD: {
      const { playerId, deck } = action.payload;

      if (state.phase !== 'card_action') {
        throw new Error('Cannot draw card in current phase');
      }

      const rng = new SeededRandom(state.rngState);
      const deckToUse = deck === 'chance' ? state.chanceDeck : state.communityChestDeck;

      const { cardId, newDeck } = drawCard(deckToUse, rng);
      const cardDef = getCardDefinition(cardId);

      const newState: GameState = {
        ...state,
        chanceDeck: deck === 'chance' ? newDeck : state.chanceDeck,
        communityChestDeck: deck === 'community_chest' ? newDeck : state.communityChestDeck,
        currentCard: { cardId, deck },
        rngState: rng.getState(),
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'CARD_DRAWN',
          {
            cardId,
            deck,
            name: cardDef?.name || cardId,
            description: cardDef?.description || '',
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.EXECUTE_CARD: {
      const { playerId, cardId } = action.payload;

      if (!state.currentCard || state.currentCard.cardId !== cardId) {
        throw new Error('Invalid card to execute');
      }

      const { newState, events: cardEvents, requiresLanding, newPosition } = executeCardEffect(
        state,
        playerId,
        cardId,
        createEvent
      );

      // Discard the card (unless it's a "Get Out of Jail Free" card)
      const deck = state.currentCard.deck;
      const updatedDeck = discardCard(
        deck === 'chance' ? newState.chanceDeck : newState.communityChestDeck,
        cardId
      );

      const finalState: GameState = {
        ...newState,
        chanceDeck: deck === 'chance' ? updatedDeck : newState.chanceDeck,
        communityChestDeck: deck === 'community_chest' ? updatedDeck : newState.communityChestDeck,
        currentCard: null,
        lastActionAt: Date.now(),
      };

      events.push(...cardEvents);

      // If card caused movement, handle landing on new space
      if (requiresLanding && newPosition !== undefined) {
        return handleLanding(finalState, playerId, newPosition, events);
      }

      return [finalState, events];
    }

    // =========================================================================
    // AUCTION ACTIONS
    // =========================================================================

    case ActionTypes.PLACE_BID: {
      const { playerId, auctionId, amount } = action.payload;
      const auction = state.activeAuction;

      if (!auction || auction.id !== auctionId) {
        throw new Error('No active auction or auction ID mismatch');
      }

      if (!auction.participants.includes(playerId)) {
        throw new Error('Not a participant in this auction');
      }

      if (auction.passed.includes(playerId)) {
        throw new Error('Player has already passed');
      }

      const player = state.players[playerId];
      if (!player) throw new Error('Player not found');

      if (amount <= auction.currentBid) {
        throw new Error('Bid must be higher than current bid');
      }

      if (player.money < amount) {
        throw new Error('Insufficient funds for bid');
      }

      const updatedAuction = {
        ...auction,
        currentBid: amount,
        highestBidderId: playerId,
      };

      const newState: GameState = {
        ...state,
        activeAuction: updatedAuction,
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'BID_PLACED',
          {
            playerId,
            amount,
            propertyId: auction.propertyId,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.PASS_AUCTION: {
      const { playerId, auctionId } = action.payload;
      const auction = state.activeAuction;

      if (!auction || auction.id !== auctionId) {
        throw new Error('No active auction or auction ID mismatch');
      }

      if (!auction.participants.includes(playerId)) {
        throw new Error('Not a participant in this auction');
      }

      if (auction.passed.includes(playerId)) {
        throw new Error('Player has already passed');
      }

      // Add player to passed list
      const newPassed = [...auction.passed, playerId];
      const remainingBidders = auction.participants.filter(
        (id) => !newPassed.includes(id)
      );

      // Check if auction should end
      if (remainingBidders.length <= 1) {
        // Auction ends
        if (auction.highestBidderId) {
          // Someone won the auction
          const winner = state.players[auction.highestBidderId];
          const property = state.properties[auction.propertyId];

          const updatedWinner = {
            ...winner,
            money: winner.money - auction.currentBid,
          };

          const updatedProperty = {
            ...property,
            ownerId: auction.highestBidderId,
          };

          const newState: GameState = {
            ...state,
            players: {
              ...state.players,
              [auction.highestBidderId]: updatedWinner,
            },
            properties: {
              ...state.properties,
              [auction.propertyId]: updatedProperty,
            },
            activeAuction: null,
            phase: 'turn_end',
            lastActionAt: Date.now(),
          };

          events.push(
            createEvent(
              newState,
              'AUCTION_ENDED',
              {
                propertyId: auction.propertyId,
                winnerId: auction.highestBidderId,
                winningBid: auction.currentBid,
              },
              playerId
            )
          );

          return [newState, events];
        } else {
          // No bids - property remains unowned
          const newState: GameState = {
            ...state,
            activeAuction: null,
            phase: 'turn_end',
            lastActionAt: Date.now(),
          };

          events.push(
            createEvent(
              newState,
              'AUCTION_ENDED',
              {
                propertyId: auction.propertyId,
                winnerId: null,
                winningBid: 0,
              },
              playerId
            )
          );

          return [newState, events];
        }
      }

      // Auction continues
      const updatedAuction = {
        ...auction,
        passed: newPassed,
      };

      const newState: GameState = {
        ...state,
        activeAuction: updatedAuction,
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'AUCTION_PLAYER_PASSED',
          {
            playerId,
            propertyId: auction.propertyId,
            remainingBidders: remainingBidders.length,
          },
          playerId
        )
      );

      return [newState, events];
    }

    // =========================================================================
    // BANKRUPTCY ACTIONS
    // =========================================================================

    case ActionTypes.BANKRUPT_PLAYER: {
      const { playerId, creditorId } = action.payload;
      const player = state.players[playerId];

      if (!player) throw new Error('Player not found');
      if (player.isBankrupt) throw new Error('Player already bankrupt');

      // Count existing bankruptcies
      const bankruptCount = Object.values(state.players).filter(
        (p) => p.isBankrupt
      ).length;

      // Get all properties owned by the bankrupt player
      const playerProperties = Object.entries(state.properties)
        .filter(([_, prop]) => prop.ownerId === playerId)
        .map(([id, prop]) => ({ id: parseInt(id), prop }));

      // Update player state
      const bankruptPlayer = {
        ...player,
        isBankrupt: true,
        bankruptcyOrder: bankruptCount + 1,
        money: 0,
        getOutOfJailCards: 0,
      };

      // Transfer properties
      const updatedProperties = { ...state.properties };
      let creditorMoney = 0;

      if (creditorId && state.players[creditorId]) {
        // Transfer to creditor
        creditorMoney = player.money; // Give remaining cash to creditor

        for (const { id, prop } of playerProperties) {
          updatedProperties[id] = {
            ...prop,
            ownerId: creditorId,
            // Keep mortgage status - creditor must pay 10% to keep mortgaged
          };
        }
      } else {
        // Return to bank - unmortgage and make available
        for (const { id, prop } of playerProperties) {
          updatedProperties[id] = {
            ...prop,
            ownerId: null,
            isMortgaged: false,
            houses: 0,
          };
        }
      }

      // Update creditor if applicable
      const updatedPlayers = {
        ...state.players,
        [playerId]: bankruptPlayer,
      };

      if (creditorId && state.players[creditorId]) {
        updatedPlayers[creditorId] = {
          ...state.players[creditorId],
          money: state.players[creditorId].money + creditorMoney,
          getOutOfJailCards:
            state.players[creditorId].getOutOfJailCards + player.getOutOfJailCards,
        };
      }

      // Check if game should end
      const activePlayers = state.playerOrder.filter(
        (id) => !updatedPlayers[id].isBankrupt
      );

      let newState: GameState = {
        ...state,
        players: updatedPlayers,
        properties: updatedProperties,
        phase: 'turn_end',
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'PLAYER_BANKRUPT',
          {
            playerId,
            creditorId,
            propertiesTransferred: playerProperties.length,
          },
          playerId
        )
      );

      // Check for game end
      if (activePlayers.length <= 1) {
        const winnerId = activePlayers[0];
        newState = {
          ...newState,
          status: 'finished',
        };

        events.push(
          createEvent(newState, 'GAME_ENDED', {
            reason: 'bankruptcy',
            winnerId,
          })
        );
      }

      return [newState, events];
    }

    // =========================================================================
    // TRADE ACTIONS
    // =========================================================================

    case ActionTypes.PROPOSE_TRADE: {
      const { proposerId, recipientId, offer, request } = action.payload;
      const proposer = state.players[proposerId];
      const recipient = state.players[recipientId];

      if (!proposer) throw new Error('Proposer not found');
      if (!recipient) throw new Error('Recipient not found');
      if (proposer.isBankrupt) throw new Error('Bankrupt players cannot trade');
      if (recipient.isBankrupt) throw new Error('Cannot trade with bankrupt player');

      // Validate proposer has offered items
      if (offer.money > proposer.money) {
        throw new Error('Insufficient funds for trade offer');
      }
      if (offer.getOutOfJailCards > proposer.getOutOfJailCards) {
        throw new Error('Insufficient Get Out of Jail cards');
      }
      for (const propId of offer.propertyIds || []) {
        const prop = state.properties[propId];
        if (!prop || prop.ownerId !== proposerId) {
          throw new Error('Cannot offer property you do not own');
        }
      }

      const trade = {
        id: `trade-${Date.now()}-${proposerId}`,
        proposerId,
        recipientId,
        offer,
        request,
        status: 'pending' as const,
        createdAt: Date.now(),
        expiresAt: Date.now() + 120000, // 2 minute expiry
      };

      const newState: GameState = {
        ...state,
        activeTrades: [...state.activeTrades, trade],
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'TRADE_PROPOSED',
          { trade },
          proposerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.ACCEPT_TRADE: {
      const { tradeId, playerId } = action.payload;
      const trade = state.activeTrades.find(t => t.id === tradeId);

      if (!trade) throw new Error('Trade not found');
      if (trade.recipientId !== playerId) throw new Error('Not the trade recipient');
      if (trade.status !== 'pending') throw new Error('Trade is not pending');

      const proposer = state.players[trade.proposerId];
      const recipient = state.players[trade.recipientId];

      if (!proposer || !recipient) throw new Error('Trade participants not found');

      // Validate both parties can still fulfill the trade
      if (trade.offer.money > proposer.money) {
        throw new Error('Proposer no longer has sufficient funds');
      }
      if (trade.request.money > recipient.money) {
        throw new Error('Recipient cannot afford requested items');
      }

      // Execute the trade - transfer assets
      const updatedProposer = { ...proposer };
      const updatedRecipient = { ...recipient };
      const updatedProperties = { ...state.properties };

      // Transfer money
      updatedProposer.money = updatedProposer.money - trade.offer.money + trade.request.money;
      updatedRecipient.money = updatedRecipient.money - trade.request.money + trade.offer.money;

      // Transfer Get Out of Jail cards
      updatedProposer.getOutOfJailCards =
        updatedProposer.getOutOfJailCards - trade.offer.getOutOfJailCards + trade.request.getOutOfJailCards;
      updatedRecipient.getOutOfJailCards =
        updatedRecipient.getOutOfJailCards - trade.request.getOutOfJailCards + trade.offer.getOutOfJailCards;

      // Transfer properties from proposer to recipient
      for (const propId of trade.offer.propertyIds || []) {
        updatedProperties[propId] = {
          ...updatedProperties[propId],
          ownerId: trade.recipientId,
        };
      }

      // Transfer properties from recipient to proposer
      for (const propId of trade.request.propertyIds || []) {
        updatedProperties[propId] = {
          ...updatedProperties[propId],
          ownerId: trade.proposerId,
        };
      }

      const newState: GameState = {
        ...state,
        players: {
          ...state.players,
          [trade.proposerId]: updatedProposer,
          [trade.recipientId]: updatedRecipient,
        },
        properties: updatedProperties,
        activeTrades: state.activeTrades.filter(t => t.id !== tradeId),
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'TRADE_ACCEPTED',
          {
            tradeId,
            proposerId: trade.proposerId,
            recipientId: trade.recipientId,
          },
          playerId
        )
      );

      return [newState, events];
    }

    case ActionTypes.REJECT_TRADE: {
      const { tradeId, playerId } = action.payload;
      const trade = state.activeTrades.find(t => t.id === tradeId);

      if (!trade) throw new Error('Trade not found');
      if (trade.recipientId !== playerId && trade.proposerId !== playerId) {
        throw new Error('Not a trade participant');
      }

      const newState: GameState = {
        ...state,
        activeTrades: state.activeTrades.filter(t => t.id !== tradeId),
        lastActionAt: Date.now(),
      };

      events.push(
        createEvent(
          newState,
          'TRADE_REJECTED',
          {
            tradeId,
            rejectedBy: playerId,
          },
          playerId
        )
      );

      return [newState, events];
    }

    default:
      // Unknown action - return state unchanged
      return [state, events];
  }
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function getCurrentPlayer(state: GameState) {
  const playerId = state.playerOrder[state.currentPlayerIndex];
  const player = state.players[playerId];
  if (!player) throw new Error('Current player not found');
  return player;
}

function advanceToNextPlayer(
  state: GameState,
  events: GameEvent[]
): ReducerResult {
  const activePlayers = state.playerOrder.filter(
    (id) => !state.players[id].isBankrupt
  );

  if (activePlayers.length <= 1) {
    // Game over - one player left
    const winnerId = activePlayers[0];
    const newState: GameState = {
      ...state,
      status: 'finished',
      lastActionAt: Date.now(),
    };

    events.push(
      createEvent(newState, 'GAME_ENDED', {
        reason: 'winner',
        winnerId,
      })
    );

    return [newState, events];
  }

  let nextIndex = (state.currentPlayerIndex + 1) % state.playerOrder.length;

  // Skip bankrupt players
  while (state.players[state.playerOrder[nextIndex]].isBankrupt) {
    nextIndex = (nextIndex + 1) % state.playerOrder.length;
  }

  // Check if we've completed a round
  const completedRound = nextIndex <= state.currentPlayerIndex;

  const newState: GameState = {
    ...state,
    currentPlayerIndex: nextIndex,
    round: completedRound ? state.round + 1 : state.round,
    phase: 'pre_roll',
    consecutiveDoubles: 0,
    lastDiceRoll: null,
    lastActionAt: Date.now(),
  };

  events.push(
    createEvent(newState, 'TURN_CHANGED', {
      previousPlayer: state.playerOrder[state.currentPlayerIndex],
      currentPlayer: state.playerOrder[nextIndex],
      round: newState.round,
    })
  );

  return [newState, events];
}

function handleLanding(
  state: GameState,
  playerId: string,
  position: number,
  events: GameEvent[]
): ReducerResult {
  const property = state.properties[position];

  if (!property) {
    // Special space - handle accordingly
    return handleSpecialSpace(state, playerId, position, events);
  }

  if (property.type === 'special') {
    return handleSpecialSpace(state, playerId, position, events);
  }

  // Regular property
  if (!property.ownerId) {
    // Unowned - offer to buy
    const newState: GameState = {
      ...state,
      phase: 'buy_decision',
    };

    events.push(
      createEvent(
        newState,
        'PROPERTY_OFFERED',
        {
          propertyId: position,
          price: property.price,
        },
        playerId
      )
    );

    return [newState, events];
  }

  if (property.ownerId === playerId) {
    // Own property - nothing happens
    const newState: GameState = {
      ...state,
      phase: 'turn_end',
    };

    return [newState, events];
  }

  // Someone else's property - pay rent
  if (property.isMortgaged) {
    // Mortgaged - no rent
    const newState: GameState = {
      ...state,
      phase: 'turn_end',
    };

    return [newState, events];
  }

  const rent = calculateRent(state, position);
  const renter = state.players[playerId];
  const owner = state.players[property.ownerId];

  if (renter.money < rent) {
    // Cannot afford rent - bankruptcy handling would go here
    // For now, just proceed
    const newState: GameState = {
      ...state,
      phase: 'bankruptcy',
    };

    return [newState, events];
  }

  const updatedRenter = {
    ...renter,
    money: renter.money - rent,
  };

  const updatedOwner = {
    ...owner,
    money: owner.money + rent,
  };

  const newState: GameState = {
    ...state,
    players: {
      ...state.players,
      [playerId]: updatedRenter,
      [property.ownerId]: updatedOwner,
    },
    phase: 'turn_end',
  };

  events.push(
    createEvent(
      newState,
      'RENT_PAID',
      {
        from: playerId,
        to: property.ownerId,
        propertyId: position,
        amount: rent,
      },
      playerId
    )
  );

  return [newState, events];
}

function handleSpecialSpace(
  state: GameState,
  playerId: string,
  position: number,
  events: GameEvent[]
): ReducerResult {
  // Handle special spaces (GO, Jail, Chance, Community Chest, etc.)
  // This would be expanded with full card logic

  switch (position) {
    case 30: // Go to Jail
      return handleGoToJail(state, playerId, 'go_to_jail_space', events);

    case 2:
    case 17:
    case 33: { // Community Chest
      const rng = new SeededRandom(state.rngState);
      const { cardId, newDeck } = drawCard(state.communityChestDeck, rng);
      const cardDef = getCardDefinition(cardId);

      const newState: GameState = {
        ...state,
        communityChestDeck: newDeck,
        currentCard: { cardId, deck: 'community_chest' },
        phase: 'card_action',
        rngState: rng.getState(),
      };
      events.push(
        createEvent(
          newState,
          'CARD_DRAWN',
          {
            cardId,
            deck: 'community_chest',
            name: cardDef?.name || cardId,
            description: cardDef?.description || '',
          },
          playerId
        )
      );
      return [newState, events];
    }

    case 7:
    case 22:
    case 36: { // Chance
      const rng2 = new SeededRandom(state.rngState);
      const { cardId: cardId2, newDeck: newDeck2 } = drawCard(state.chanceDeck, rng2);
      const cardDef2 = getCardDefinition(cardId2);

      const newState2: GameState = {
        ...state,
        chanceDeck: newDeck2,
        currentCard: { cardId: cardId2, deck: 'chance' },
        phase: 'card_action',
        rngState: rng2.getState(),
      };
      events.push(
        createEvent(
          newState2,
          'CARD_DRAWN',
          {
            cardId: cardId2,
            deck: 'chance',
            name: cardDef2?.name || cardId2,
            description: cardDef2?.description || '',
          },
          playerId
        )
      );
      return [newState2, events];
    }

    case 4: // Income Tax
      const player = state.players[playerId];
      const tax = 200;
      const updatedPlayer = {
        ...player,
        money: player.money - tax,
      };

      const newState3: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer,
        },
        freeParkingPot: state.config.freeParkingEnabled
          ? state.freeParkingPot + tax
          : state.freeParkingPot,
        phase: 'turn_end',
      };

      events.push(
        createEvent(newState3, 'TAX_PAID', { amount: tax }, playerId)
      );
      return [newState3, events];

    case 38: // Luxury Tax
      const player2 = state.players[playerId];
      const luxuryTax = 100;
      const updatedPlayer2 = {
        ...player2,
        money: player2.money - luxuryTax,
      };

      const newState4: GameState = {
        ...state,
        players: {
          ...state.players,
          [playerId]: updatedPlayer2,
        },
        freeParkingPot: state.config.freeParkingEnabled
          ? state.freeParkingPot + luxuryTax
          : state.freeParkingPot,
        phase: 'turn_end',
      };

      events.push(
        createEvent(newState4, 'TAX_PAID', { amount: luxuryTax }, playerId)
      );
      return [newState4, events];

    case 20: // Free Parking
      if (state.config.freeParkingEnabled && state.freeParkingPot > 0) {
        const player3 = state.players[playerId];
        const pot = state.freeParkingPot;
        const updatedPlayer3 = {
          ...player3,
          money: player3.money + pot,
        };

        const newState5: GameState = {
          ...state,
          players: {
            ...state.players,
            [playerId]: updatedPlayer3,
          },
          freeParkingPot: 0,
          phase: 'turn_end',
        };

        events.push(
          createEvent(
            newState5,
            'FREE_PARKING_COLLECTED',
            { amount: pot },
            playerId
          )
        );
        return [newState5, events];
      }
      // Just a rest stop
      return [{ ...state, phase: 'turn_end' }, events];

    case 10: // Just Visiting Jail
    case 0: // GO (already handled in movement)
    default:
      return [{ ...state, phase: 'turn_end' }, events];
  }
}

function handleGoToJail(
  state: GameState,
  playerId: string,
  reason: 'three_doubles' | 'go_to_jail_space' | 'card',
  events: GameEvent[]
): ReducerResult {
  const player = state.players[playerId];

  const updatedPlayer = {
    ...player,
    position: JAIL_POSITION,
    inJail: true,
    jailTurns: 0,
  };

  const newState: GameState = {
    ...state,
    players: {
      ...state.players,
      [playerId]: updatedPlayer,
    },
    consecutiveDoubles: 0,
    phase: 'turn_end',
    lastActionAt: Date.now(),
  };

  events.push(
    createEvent(newState, 'SENT_TO_JAIL', { reason }, playerId)
  );

  return [newState, events];
}

function handleJailRoll(
  state: GameState,
  playerId: string,
  events: GameEvent[]
): ReducerResult {
  const player = state.players[playerId];
  const rng = new SeededRandom(state.rngState);
  const diceRoll = rng.rollDice();

  events.push(
    createEvent(state, 'DICE_ROLLED', { dice: diceRoll }, playerId)
  );

  if (diceRoll.isDoubles) {
    // Rolled doubles - free!
    const updatedPlayer = {
      ...player,
      inJail: false,
      jailTurns: 0,
    };

    // Calculate movement from jail
    const newPosition = getNextPosition(JAIL_POSITION, diceRoll.total);

    const movedPlayer = {
      ...updatedPlayer,
      position: newPosition,
    };

    const newState: GameState = {
      ...state,
      players: {
        ...state.players,
        [playerId]: movedPlayer,
      },
      lastDiceRoll: diceRoll,
      rngState: rng.getState(),
      phase: 'landed',
      lastActionAt: Date.now(),
    };

    events.push(
      createEvent(newState, 'RELEASED_FROM_JAIL', { reason: 'doubles' }, playerId)
    );

    events.push(
      createEvent(
        newState,
        'PLAYER_MOVED',
        {
          from: JAIL_POSITION,
          to: newPosition,
          spaces: diceRoll.total,
          passedGo: false,
        },
        playerId
      )
    );

    return handleLanding(newState, playerId, newPosition, events);
  }

  // Failed to roll doubles
  const newJailTurns = player.jailTurns + 1;

  if (newJailTurns >= state.config.maxJailTurns) {
    // Forced to pay fine
    const updatedPlayer = {
      ...player,
      money: player.money - state.config.jailFine,
      inJail: false,
      jailTurns: 0,
    };

    const newState: GameState = {
      ...state,
      players: {
        ...state.players,
        [playerId]: updatedPlayer,
      },
      lastDiceRoll: diceRoll,
      rngState: rng.getState(),
      phase: 'pre_roll',
      lastActionAt: Date.now(),
    };

    events.push(
      createEvent(
        newState,
        'JAIL_FINE_FORCED',
        { amount: state.config.jailFine },
        playerId
      )
    );

    return [newState, events];
  }

  // Still in jail
  const updatedPlayer = {
    ...player,
    jailTurns: newJailTurns,
  };

  const newState: GameState = {
    ...state,
    players: {
      ...state.players,
      [playerId]: updatedPlayer,
    },
    lastDiceRoll: diceRoll,
    rngState: rng.getState(),
    phase: 'turn_end',
    lastActionAt: Date.now(),
  };

  events.push(
    createEvent(
      newState,
      'JAIL_ROLL_FAILED',
      { turnsRemaining: state.config.maxJailTurns - newJailTurns },
      playerId
    )
  );

  return [newState, events];
}

function handleStartAuction(
  state: GameState,
  propertyId: number,
  events: GameEvent[]
): ReducerResult {
  const activePlayers = state.playerOrder.filter(
    (id) => !state.players[id].isBankrupt
  );

  const auction = {
    id: `auction-${propertyId}-${Date.now()}`,
    propertyId,
    currentBid: 0,
    highestBidderId: null,
    participants: activePlayers,
    passed: [],
    startedAt: Date.now(),
    endsAt: Date.now() + 60000, // 60 second auction
  };

  const newState: GameState = {
    ...state,
    activeAuction: auction,
    phase: 'auction',
    lastActionAt: Date.now(),
  };

  events.push(
    createEvent(newState, 'AUCTION_STARTED', {
      propertyId,
      participants: activePlayers,
    })
  );

  return [newState, events];
}

export { createInitialState };
