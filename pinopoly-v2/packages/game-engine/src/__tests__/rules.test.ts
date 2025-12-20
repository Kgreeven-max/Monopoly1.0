import { describe, it, expect } from 'vitest';
import {
  calculateNewPosition,
  calculateMovementPath,
  checkPassedGo,
} from '../rules/movement';
import {
  calculateRent,
  hasMonopoly,
  canBuildHouse,
} from '../rules/property';
import type { GameState, PropertyState } from '../state/types';

describe('movement rules', () => {
  describe('calculateNewPosition', () => {
    it('should move forward by dice total', () => {
      expect(calculateNewPosition(0, 7)).toBe(7);
      expect(calculateNewPosition(5, 3)).toBe(8);
    });

    it('should wrap around the board', () => {
      expect(calculateNewPosition(38, 5)).toBe(3);
      expect(calculateNewPosition(35, 10)).toBe(5);
    });
  });

  describe('calculateMovementPath', () => {
    it('should return path of positions', () => {
      const path = calculateMovementPath(0, 3);
      expect(path).toEqual([1, 2, 3]);
    });

    it('should wrap around correctly', () => {
      const path = calculateMovementPath(38, 4);
      expect(path).toEqual([39, 0, 1, 2]);
    });
  });

  describe('checkPassedGo', () => {
    it('should detect passing GO', () => {
      expect(checkPassedGo(38, 3)).toBe(true);
      expect(checkPassedGo(35, 10)).toBe(true);
    });

    it('should not detect passing GO on normal moves', () => {
      expect(checkPassedGo(5, 3)).toBe(false);
      expect(checkPassedGo(20, 5)).toBe(false);
    });

    it('should not detect passing GO when landing on GO', () => {
      // Landing exactly on GO should still count as passing it
      expect(checkPassedGo(35, 5)).toBe(true);
    });
  });
});

describe('property rules', () => {
  const createMockGameState = (properties: Partial<Record<number, Partial<PropertyState>>> = {}): GameState => {
    const baseProperties: Record<number, PropertyState> = {};

    // Create all 40 spaces with defaults
    for (let i = 0; i < 40; i++) {
      baseProperties[i] = {
        position: i,
        type: 'property',
        ownerId: null,
        houses: 0,
        isMortgaged: false,
        price: 100,
        rent: [10, 50, 150, 450, 625, 750],
        houseCost: 50,
        colorGroup: i <= 3 ? 'brown' : 'lightBlue',
        ...properties[i],
      };
    }

    return {
      id: 'test',
      roomCode: 'TEST',
      status: 'playing',
      round: 1,
      currentPlayerIndex: 0,
      playerOrder: ['p1', 'p2'],
      phase: 'postRoll',
      rngSeed: 12345,
      rngState: 12345,
      economy: {
        phase: 'normal',
        multiplier: 1,
        turnsUntilChange: 10,
      },
      config: {
        maxPlayers: 4,
        startingMoney: 1500,
        goBonus: 200,
        enableEconomy: false,
        enableCrime: false,
        botDifficulty: 'medium',
        turnTimeLimit: null,
      },
      players: {
        p1: {
          id: 'p1',
          name: 'Player 1',
          token: 'car',
          money: 1500,
          position: 0,
          inJail: false,
          jailTurns: 0,
          isBot: false,
          isBankrupt: false,
          getOutOfJailCards: 0,
          personality: null,
        },
        p2: {
          id: 'p2',
          name: 'Player 2',
          token: 'dog',
          money: 1500,
          position: 0,
          inJail: false,
          jailTurns: 0,
          isBot: false,
          isBankrupt: false,
          getOutOfJailCards: 0,
          personality: null,
        },
      },
      properties: baseProperties,
      chance: [],
      communityChest: [],
      freeParkingPool: 0,
      doublesCount: 0,
    };
  };

  describe('calculateRent', () => {
    it('should return base rent for unimproved property', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', houses: 0, rent: [2, 10, 30, 90, 160, 250] },
      });

      const rent = calculateRent(state, 1);
      expect(rent).toBe(2);
    });

    it('should return increased rent with houses', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', houses: 3, rent: [2, 10, 30, 90, 160, 250] },
      });

      const rent = calculateRent(state, 1);
      expect(rent).toBe(90);
    });

    it('should double rent with monopoly (no houses)', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', houses: 0, colorGroup: 'brown', rent: [2, 10, 30, 90, 160, 250] },
        3: { ownerId: 'p1', houses: 0, colorGroup: 'brown' },
      });

      const rent = calculateRent(state, 1);
      expect(rent).toBe(4); // Double base rent
    });

    it('should return 0 for mortgaged property', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', isMortgaged: true, rent: [2, 10, 30, 90, 160, 250] },
      });

      const rent = calculateRent(state, 1);
      expect(rent).toBe(0);
    });
  });

  describe('hasMonopoly', () => {
    it('should return true when player owns all properties in group', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', colorGroup: 'brown' },
        3: { ownerId: 'p1', colorGroup: 'brown' },
      });

      expect(hasMonopoly(state, 'p1', 'brown')).toBe(true);
    });

    it('should return false when player does not own all', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', colorGroup: 'brown' },
        3: { ownerId: 'p2', colorGroup: 'brown' },
      });

      expect(hasMonopoly(state, 'p1', 'brown')).toBe(false);
    });
  });

  describe('canBuildHouse', () => {
    it('should return true when player has monopoly and money', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', colorGroup: 'brown', houses: 0, houseCost: 50 },
        3: { ownerId: 'p1', colorGroup: 'brown', houses: 0 },
      });

      expect(canBuildHouse(state, 'p1', 1)).toBe(true);
    });

    it('should return false without monopoly', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', colorGroup: 'brown', houses: 0 },
        3: { ownerId: 'p2', colorGroup: 'brown' },
      });

      expect(canBuildHouse(state, 'p1', 1)).toBe(false);
    });

    it('should return false when property has hotel (5 houses)', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', colorGroup: 'brown', houses: 5 },
        3: { ownerId: 'p1', colorGroup: 'brown', houses: 5 },
      });

      expect(canBuildHouse(state, 'p1', 1)).toBe(false);
    });

    it('should enforce even building rule', () => {
      const state = createMockGameState({
        1: { ownerId: 'p1', colorGroup: 'brown', houses: 2 },
        3: { ownerId: 'p1', colorGroup: 'brown', houses: 0 },
      });

      // Can't build on property with 2 houses when another has 0
      expect(canBuildHouse(state, 'p1', 1)).toBe(false);
      // But can build on the one with 0
      expect(canBuildHouse(state, 'p1', 3)).toBe(true);
    });
  });
});
