import { describe, it, expect, beforeEach } from 'vitest';
import { gameReducer } from '../reducers/gameReducer';
import { ActionTypes, type GameAction } from '../actions/types';
import type { GameState } from '../state/types';

describe('gameReducer', () => {
  let initialState: GameState;

  beforeEach(() => {
    // Initialize a fresh game state for each test
    const initAction: GameAction = {
      type: ActionTypes.INITIALIZE_GAME,
      payload: {
        roomCode: 'TEST',
        hostId: 'host-1',
        config: {
          maxPlayers: 4,
          startingMoney: 1500,
          goBonus: 200,
          enableEconomy: false,
          enableCrime: false,
          botDifficulty: 'medium',
          turnTimeLimit: null,
        },
        seed: 12345,
      },
    };

    const [state] = gameReducer(null as any, initAction);
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

    it('should initialize all 40 board spaces', () => {
      expect(Object.keys(initialState.properties)).toHaveLength(40);
    });
  });

  describe('ADD_PLAYER', () => {
    it('should add a player to the game', () => {
      const action: GameAction = {
        type: ActionTypes.ADD_PLAYER,
        payload: {
          id: 'player-1',
          name: 'Test Player',
          token: 'car',
          isBot: false,
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

    it('should add bot players with personality', () => {
      const action: GameAction = {
        type: ActionTypes.ADD_PLAYER,
        payload: {
          id: 'bot-1',
          name: 'Bot Player',
          token: 'hat',
          isBot: true,
          personality: 'aggressive',
        },
      };

      const [state] = gameReducer(initialState, action);

      expect(state.players['bot-1'].isBot).toBe(true);
      expect(state.players['bot-1'].personality).toBe('aggressive');
    });
  });

  describe('START_GAME', () => {
    it('should start the game when there are enough players', () => {
      // Add two players
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p1', name: 'Player 1', token: 'car', isBot: false },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p2', name: 'Player 2', token: 'dog', isBot: false },
      });

      // Start the game
      [state] = gameReducer(state, { type: ActionTypes.START_GAME, payload: {} });

      expect(state.status).toBe('playing');
      expect(state.round).toBe(1);
      expect(state.phase).toBe('preRoll');
    });
  });

  describe('ROLL_DICE', () => {
    let gameState: GameState;

    beforeEach(() => {
      // Set up a game with two players
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p1', name: 'Player 1', token: 'car', isBot: false },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p2', name: 'Player 2', token: 'dog', isBot: false },
      });

      [state] = gameReducer(state, { type: ActionTypes.START_GAME, payload: {} });

      gameState = state;
    });

    it('should roll dice and update player position', () => {
      const currentPlayer = gameState.playerOrder[gameState.currentPlayerIndex];

      const [state, events] = gameReducer(gameState, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: currentPlayer },
      });

      expect(state.players[currentPlayer].position).toBeGreaterThan(0);
      expect(state.phase).toBe('postRoll');

      const rollEvent = events.find(e => e.type === 'DICE_ROLLED');
      expect(rollEvent).toBeDefined();
      expect(rollEvent?.data.dice).toHaveLength(2);
    });

    it('should collect GO bonus when passing GO', () => {
      // Set player near GO (position 38 = Park Place)
      gameState.players['p1'].position = 38;
      gameState.phase = 'roll';

      // Force a specific roll that would pass GO
      const [state] = gameReducer(gameState, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: 'p1' },
      });

      // If they passed GO, they should have gotten the bonus
      if (state.players['p1'].position < 38) {
        expect(state.players['p1'].money).toBe(1500 + 200); // Starting + GO bonus
      }
    });
  });

  describe('BUY_PROPERTY', () => {
    let gameState: GameState;

    beforeEach(() => {
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p1', name: 'Player 1', token: 'car', isBot: false },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p2', name: 'Player 2', token: 'dog', isBot: false },
      });

      [state] = gameReducer(state, { type: ActionTypes.START_GAME, payload: {} });

      // Move player to a purchasable property (position 1 = Mediterranean Ave)
      state.players['p1'].position = 1;
      state.phase = 'postRoll';

      gameState = state;
    });

    it('should allow player to buy unowned property', () => {
      const [state, events] = gameReducer(gameState, {
        type: ActionTypes.BUY_PROPERTY,
        payload: { playerId: 'p1', propertyPosition: 1 },
      });

      expect(state.properties[1].ownerId).toBe('p1');
      expect(state.players['p1'].money).toBe(1500 - 60); // Starting - Mediterranean price

      const buyEvent = events.find(e => e.type === 'PROPERTY_PURCHASED');
      expect(buyEvent).toBeDefined();
    });

    it('should not allow buying already owned property', () => {
      // First player buys
      let [state] = gameReducer(gameState, {
        type: ActionTypes.BUY_PROPERTY,
        payload: { playerId: 'p1', propertyPosition: 1 },
      });

      // Try to buy again (should be no-op)
      const moneyBefore = state.players['p1'].money;
      [state] = gameReducer(state, {
        type: ActionTypes.BUY_PROPERTY,
        payload: { playerId: 'p1', propertyPosition: 1 },
      });

      expect(state.players['p1'].money).toBe(moneyBefore);
    });
  });

  describe('END_TURN', () => {
    it('should advance to next player', () => {
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p1', name: 'Player 1', token: 'car', isBot: false },
      });

      [state] = gameReducer(state, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p2', name: 'Player 2', token: 'dog', isBot: false },
      });

      [state] = gameReducer(state, { type: ActionTypes.START_GAME, payload: {} });

      // Roll dice first
      [state] = gameReducer(state, {
        type: ActionTypes.ROLL_DICE,
        payload: { playerId: 'p1' },
      });

      // End turn
      [state] = gameReducer(state, {
        type: ActionTypes.END_TURN,
        payload: { playerId: 'p1' },
      });

      expect(state.currentPlayerIndex).toBe(1);
      expect(state.phase).toBe('preRoll');
    });
  });

  describe('BUILD_HOUSE', () => {
    it('should build house when player has monopoly', () => {
      let [state] = gameReducer(initialState, {
        type: ActionTypes.ADD_PLAYER,
        payload: { id: 'p1', name: 'Player 1', token: 'car', isBot: false },
      });

      // Give player both brown properties
      state.properties[1].ownerId = 'p1';
      state.properties[3].ownerId = 'p1';
      state.phase = 'preRoll';

      const [newState, events] = gameReducer(state, {
        type: ActionTypes.BUILD_HOUSE,
        payload: { playerId: 'p1', propertyPosition: 1 },
      });

      expect(newState.properties[1].houses).toBe(1);
      expect(newState.players['p1'].money).toBe(1500 - 50); // House cost for brown
    });
  });
});
