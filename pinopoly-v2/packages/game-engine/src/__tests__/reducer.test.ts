import { describe, it, expect, beforeEach } from 'vitest';
import { gameReducer } from '../reducers/gameReducer';
import { ActionTypes, type GameAction } from '../actions/types';
import type { GameState, GameConfig } from '../state/types';

const defaultConfig: GameConfig = {
  maxPlayers: 4,
  startingMoney: 1500,
  goSalary: 200,
  jailFine: 50,
  maxJailTurns: 3,
  freeParkingEnabled: true,
  economicCyclesEnabled: false,
  financialInstrumentsEnabled: false,
  auctionRequired: true,
  turnTimeLimit: 0,
  maxRounds: 0,
};

describe('gameReducer', () => {
  let initialState: GameState;

  beforeEach(() => {
    // Initialize a fresh game state for each test
    const initAction: GameAction = {
      type: ActionTypes.INITIALIZE_GAME,
      payload: {
        gameId: 'test-game-1',
        roomCode: 'TEST',
        hostId: 'host-1',
        config: defaultConfig,
        seed: 12345,
      },
    };

    const [state] = gameReducer(null as unknown as GameState, initAction);
    initialState = state;
  });

  describe('INITIALIZE_GAME', () => {
    it('should create a new game state with correct properties', () => {
      expect(initialState.roomCode).toBe('TEST');
      expect(initialState.status).toBe('lobby');
      expect(initialState.round).toBe(0);
      expect(initialState.rngSeed).toBe(12345);
      expect(Object.keys(initialState.players)).toHaveLength(0);
    });

    it('should initialize all 28 purchasable properties', () => {
      // There are 28 purchasable properties on a Monopoly board
      // (22 streets, 4 railroads, 2 utilities)
      expect(Object.keys(initialState.properties)).toHaveLength(28);
    });
  });

  describe('ADD_PLAYER', () => {
    it('should add a player to the game', () => {
      const action: GameAction = {
        type: ActionTypes.ADD_PLAYER,
        payload: {
          playerId: 'player-1',
          name: 'Test Player',
          token: 'car',
          color: '#ff0000',
        },
      };

      const [state, events] = gameReducer(initialState, action);

      expect(state.players['player-1']).toBeDefined();
      expect(state.players['player-1'].name).toBe('Test Player');
      expect(state.players['player-1'].token).toBe('car');
      expect(state.players['player-1'].money).toBe(1500);
      expect(state.playerOrder).toContain('player-1');
      expect(events).toHaveLength(1);
      expect(events[0].type).toBe('PLAYER_JOINED');
    });
  });

  describe('ADD_BOT', () => {
    it('should add bot players with personality', () => {
      const action: GameAction = {
        type: ActionTypes.ADD_BOT,
        payload: {
          botId: 'bot-1',
          name: 'Bot Player',
          token: 'hat',
          color: '#00ff00',
          personality: 'aggressive',
          difficulty: 'normal',
        },
      };

      const [state] = gameReducer(initialState, action);

      expect(state.players['bot-1'].isBot).toBe(true);
      expect(state.players['bot-1'].botPersonality).toBe('aggressive');
    });
  });

  describe('START_GAME', () => {
    it('should start the game when there are enough players', () => {
      // Add two players
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p1', name: 'Player 1', token: 'car', color: '#ff0000' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p2', name: 'Player 2', token: 'dog', color: '#00ff00' },
      });

      // Start the game
      [state] = gameReducer(state, {
        type: ActionTypes.START_GAME,
        payload: { initiatorId: 'p1' },
      });

      expect(state.status).toBe('playing');
      expect(state.round).toBe(1);
      expect(state.phase).toBe('pre_roll');
    });
  });

  describe('ROLL_DICE', () => {
    let gameState: GameState;

    beforeEach(() => {
      // Set up a game with two players
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p1', name: 'Player 1', token: 'car', color: '#ff0000' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p2', name: 'Player 2', token: 'dog', color: '#00ff00' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.START_GAME,
        payload: { initiatorId: 'p1' },
      });

      gameState = state;
    });

    it('should roll dice and update player position', () => {
      const currentPlayer = gameState.playerOrder[gameState.currentPlayerIndex];

      const [state, events] = gameReducer(gameState, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: currentPlayer },
      });

      expect(state.players[currentPlayer].position).toBeGreaterThan(0);
      expect(state.lastDiceRoll).not.toBeNull();

      const rollEvent = events.find(e => e.type === 'DICE_ROLLED');
      expect(rollEvent).toBeDefined();
    });
  });

  describe('BUY_PROPERTY', () => {
    let gameState: GameState;

    beforeEach(() => {
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p1', name: 'Player 1', token: 'car', color: '#ff0000' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p2', name: 'Player 2', token: 'dog', color: '#00ff00' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.START_GAME,
        payload: { initiatorId: 'p1' },
      });

      // Get the current player after start (order is shuffled)
      const currentPlayerId = state.playerOrder[state.currentPlayerIndex];

      // Move current player to a purchasable property (position 1 = Mediterranean Ave)
      state = {
        ...state,
        players: {
          ...state.players,
          [currentPlayerId]: { ...state.players[currentPlayerId], position: 1 },
        },
        phase: 'buy_decision' as const,
      };

      gameState = state;
    });

    it('should allow player to buy unowned property', () => {
      const currentPlayer = gameState.playerOrder[gameState.currentPlayerIndex];

      const [state, events] = gameReducer(gameState, {
        type: ActionTypes.BUY_PROPERTY,
        payload: { playerId: currentPlayer, propertyId: 1 },
      });

      expect(state.properties[1].ownerId).toBe(currentPlayer);
      expect(state.players[currentPlayer].money).toBe(1500 - gameState.properties[1].price);

      const buyEvent = events.find(e => e.type === 'PROPERTY_BOUGHT');
      expect(buyEvent).toBeDefined();
    });
  });

  describe('END_TURN', () => {
    it('should advance to next player', () => {
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p1', name: 'Player 1', token: 'car', color: '#ff0000' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p2', name: 'Player 2', token: 'dog', color: '#00ff00' },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.START_GAME,
        payload: { initiatorId: 'p1' },
      });

      // Roll dice first
      const currentPlayer = state.playerOrder[state.currentPlayerIndex];
      [state] = gameReducer(state, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: currentPlayer },
      });

      // Set phase to turn_end
      state = { ...state, phase: 'turn_end' as const };

      // End turn
      [state] = gameReducer(state, {
        type: ActionTypes.END_TURN,
        payload: { playerId: currentPlayer },
      });

      expect(state.currentPlayerIndex).toBe(1);
      expect(state.phase).toBe('pre_roll');
    });
  });

  describe('BUILD_HOUSE', () => {
    it('should build house when player has monopoly', () => {
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { playerId: 'p1', name: 'Player 1', token: 'car', color: '#ff0000' },
      });

      // Give player both brown properties (positions 1 and 3)
      state = {
        ...state,
        status: 'playing' as const,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1' },
          3: { ...state.properties[3], ownerId: 'p1' },
        },
        phase: 'pre_roll' as const,
      };

      const houseCost = state.properties[1].houseCost;
      const moneyBefore = state.players['p1'].money;

      const [newState, events] = gameReducer(state, {
        type: ActionTypes.BUILD_HOUSE,
        payload: { playerId: 'p1', propertyId: 1 },
      });

      expect(newState.properties[1].houses).toBe(1);
      expect(newState.players['p1'].money).toBe(moneyBefore - houseCost);
    });
  });
});
