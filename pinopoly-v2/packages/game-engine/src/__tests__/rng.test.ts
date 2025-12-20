import { describe, it, expect } from 'vitest';
import { SeededRandom } from '../rng/SeededRandom';

describe('SeededRandom', () => {
  describe('determinism', () => {
    it('should produce the same sequence with the same seed', () => {
      const rng1 = new SeededRandom(12345);
      const rng2 = new SeededRandom(12345);

      const sequence1 = Array.from({ length: 10 }, () => rng1.next());
      const sequence2 = Array.from({ length: 10 }, () => rng2.next());

      expect(sequence1).toEqual(sequence2);
    });

    it('should produce different sequences with different seeds', () => {
      const rng1 = new SeededRandom(12345);
      const rng2 = new SeededRandom(54321);

      const sequence1 = Array.from({ length: 10 }, () => rng1.next());
      const sequence2 = Array.from({ length: 10 }, () => rng2.next());

      expect(sequence1).not.toEqual(sequence2);
    });

    it('should produce values between 0 and 1', () => {
      const rng = new SeededRandom(12345);

      for (let i = 0; i < 100; i++) {
        const value = rng.next();
        expect(value).toBeGreaterThanOrEqual(0);
        expect(value).toBeLessThan(1);
      }
    });
  });

  describe('nextInt', () => {
    it('should produce integers within the specified range', () => {
      const rng = new SeededRandom(12345);

      for (let i = 0; i < 100; i++) {
        const value = rng.nextInt(1, 6);
        expect(value).toBeGreaterThanOrEqual(1);
        expect(value).toBeLessThanOrEqual(6);
        expect(Number.isInteger(value)).toBe(true);
      }
    });

    it('should be deterministic', () => {
      const rng1 = new SeededRandom(12345);
      const rng2 = new SeededRandom(12345);

      const sequence1 = Array.from({ length: 10 }, () => rng1.nextInt(1, 100));
      const sequence2 = Array.from({ length: 10 }, () => rng2.nextInt(1, 100));

      expect(sequence1).toEqual(sequence2);
    });
  });

  describe('rollDice', () => {
    it('should return two dice values between 1 and 6', () => {
      const rng = new SeededRandom(12345);

      for (let i = 0; i < 50; i++) {
        const [die1, die2] = rng.rollDice();
        expect(die1).toBeGreaterThanOrEqual(1);
        expect(die1).toBeLessThanOrEqual(6);
        expect(die2).toBeGreaterThanOrEqual(1);
        expect(die2).toBeLessThanOrEqual(6);
      }
    });

    it('should be deterministic', () => {
      const rng1 = new SeededRandom(12345);
      const rng2 = new SeededRandom(12345);

      const rolls1 = Array.from({ length: 10 }, () => rng1.rollDice());
      const rolls2 = Array.from({ length: 10 }, () => rng2.rollDice());

      expect(rolls1).toEqual(rolls2);
    });
  });

  describe('state management', () => {
    it('should allow getting and setting state', () => {
      const rng1 = new SeededRandom(12345);

      // Advance the RNG
      for (let i = 0; i < 5; i++) {
        rng1.next();
      }

      // Save state
      const state = rng1.getState();

      // Get next few values
      const futureValues = Array.from({ length: 5 }, () => rng1.next());

      // Create new RNG from saved state
      const rng2 = new SeededRandom(0);
      rng2.setState(state);

      // Should produce same values
      const reproducedValues = Array.from({ length: 5 }, () => rng2.next());

      expect(futureValues).toEqual(reproducedValues);
    });
  });

  describe('shuffle', () => {
    it('should shuffle array in place', () => {
      const rng = new SeededRandom(12345);
      const original = [1, 2, 3, 4, 5];
      const shuffled = [...original];

      rng.shuffle(shuffled);

      expect(shuffled).toHaveLength(original.length);
      expect(shuffled.sort()).toEqual(original.sort());
    });

    it('should be deterministic', () => {
      const rng1 = new SeededRandom(12345);
      const rng2 = new SeededRandom(12345);

      const arr1 = [1, 2, 3, 4, 5];
      const arr2 = [1, 2, 3, 4, 5];

      rng1.shuffle(arr1);
      rng2.shuffle(arr2);

      expect(arr1).toEqual(arr2);
    });
  });
});
