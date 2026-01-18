import { describe, it, expect } from 'vitest';
import {
  getNextPosition,
  wouldPassGo,
  BOARD_SIZE,
} from '../rules/movement';
import {
  calculateRent,
  hasMonopoly,
  canBuildHouse,
} from '../rules/property';
import { gameReducer } from '../reducers/gameReducer';
import { ActionTypes } from '../actions/types';
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

function createTestGame(): GameState {
  const [state] = gameReducer(null as unknown as GameState, {
    type: ActionTypes.INITIALIZE_GAME,
    payload: {
      gameId: 'test-game',
      roomCode: 'TEST',
      hostId: 'host-1',
      config: defaultConfig,
      seed: 12345,
    },
  });
  return state;
}

describe('movement rules', () => {
  describe('getNextPosition', () => {
    it('should move forward by dice total', () => {
      expect(getNextPosition(0, 7)).toBe(7);
      expect(getNextPosition(5, 3)).toBe(8);
    });

    it('should wrap around the board', () => {
      expect(getNextPosition(38, 5)).toBe(3);
      expect(getNextPosition(35, 10)).toBe(5);
    });
  });

  describe('wouldPassGo', () => {
    it('should detect passing GO', () => {
      expect(wouldPassGo(38, 3)).toBe(true);
      expect(wouldPassGo(35, 10)).toBe(true);
    });

    it('should not detect passing GO on normal moves', () => {
      expect(wouldPassGo(5, 3)).toBe(false);
      expect(wouldPassGo(20, 5)).toBe(false);
    });

    it('should detect passing GO when landing on GO', () => {
      expect(wouldPassGo(35, 5)).toBe(true);
    });
  });
});

describe('property rules', () => {
  describe('calculateRent', () => {
    it('should return base rent for unimproved property', () => {
      const state = createTestGame();
      // Give ownership of Mediterranean (position 1) to a player
      const stateWithPlayer = {
        ...state,
        players: {
          p1: {
            id: 'p1',
            name: 'Player 1',
            token: 'car' as const,
            color: '#ff0000',
            money: 1500,
            position: 0,
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
            socketId: null,
          },
        },
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1' },
        },
      };

      const rent = calculateRent(stateWithPlayer, 1);
      expect(rent).toBe(2); // Mediterranean base rent
    });

    it('should return 0 for mortgaged property', () => {
      const state = createTestGame();
      const stateWithPlayer = {
        ...state,
        players: {
          p1: {
            id: 'p1',
            name: 'Player 1',
            token: 'car' as const,
            color: '#ff0000',
            money: 1500,
            position: 0,
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
            socketId: null,
          },
        },
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1', isMortgaged: true },
        },
      };

      const rent = calculateRent(stateWithPlayer, 1);
      expect(rent).toBe(0);
    });

    it('should double rent with monopoly (no houses)', () => {
      const state = createTestGame();
      const stateWithPlayer = {
        ...state,
        players: {
          p1: {
            id: 'p1',
            name: 'Player 1',
            token: 'car' as const,
            color: '#ff0000',
            money: 1500,
            position: 0,
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
            socketId: null,
          },
        },
        properties: {
          ...state.properties,
          // Both brown properties owned by p1
          1: { ...state.properties[1], ownerId: 'p1' }, // Mediterranean
          3: { ...state.properties[3], ownerId: 'p1' }, // Baltic
        },
      };

      const rent = calculateRent(stateWithPlayer, 1);
      expect(rent).toBe(4); // Double base rent (2 * 2)
    });
  });

  describe('hasMonopoly', () => {
    it('should return true when player owns all properties in group', () => {
      const state = createTestGame();
      const stateWithMonopoly = {
        ...state,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1' }, // Mediterranean
          3: { ...state.properties[3], ownerId: 'p1' }, // Baltic
        },
      };

      expect(hasMonopoly(stateWithMonopoly, 'p1', 'brown')).toBe(true);
    });

    it('should return false when player does not own all', () => {
      const state = createTestGame();
      const stateWithPartialOwnership = {
        ...state,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1' }, // Mediterranean
          3: { ...state.properties[3], ownerId: 'p2' }, // Baltic owned by different player
        },
      };

      expect(hasMonopoly(stateWithPartialOwnership, 'p1', 'brown')).toBe(false);
    });
  });

  describe('canBuildHouse', () => {
    it('should return true when player has monopoly', () => {
      const state = createTestGame();
      const stateWithMonopoly = {
        ...state,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1' }, // Mediterranean
          3: { ...state.properties[3], ownerId: 'p1' }, // Baltic
        },
      };

      expect(canBuildHouse(stateWithMonopoly, 1)).toBe(true);
    });

    it('should return false without monopoly', () => {
      const state = createTestGame();
      const stateWithoutMonopoly = {
        ...state,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1' }, // Mediterranean
          3: { ...state.properties[3], ownerId: 'p2' }, // Baltic owned by different player
        },
      };

      expect(canBuildHouse(stateWithoutMonopoly, 1)).toBe(false);
    });

    it('should return false when property has hotel (5 houses)', () => {
      const state = createTestGame();
      const stateWithHotel = {
        ...state,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1', houses: 5 },
          3: { ...state.properties[3], ownerId: 'p1', houses: 5 },
        },
      };

      expect(canBuildHouse(stateWithHotel, 1)).toBe(false);
    });

    it('should enforce even building rule', () => {
      const state = createTestGame();
      const stateWithUnevenBuilding = {
        ...state,
        properties: {
          ...state.properties,
          1: { ...state.properties[1], ownerId: 'p1', houses: 2 },
          3: { ...state.properties[3], ownerId: 'p1', houses: 0 },
        },
      };

      // Can't build on property with 2 houses when another has 0
      expect(canBuildHouse(stateWithUnevenBuilding, 1)).toBe(false);
      // But can build on the one with 0
      expect(canBuildHouse(stateWithUnevenBuilding, 3)).toBe(true);
    });
  });
});
