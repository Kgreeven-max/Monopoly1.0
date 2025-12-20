/**
 * Seeded Random Number Generator for Pinopoly
 * Uses Mulberry32 algorithm for deterministic randomness
 * Enables game replay and testing
 */

import type { DiceRoll } from '../state/types';

export class SeededRandom {
  private state: number;

  constructor(seed: number) {
    this.state = seed >>> 0; // Ensure unsigned 32-bit
  }

  /**
   * Generate next random number between 0 and 1
   * Uses Mulberry32 algorithm - fast with good distribution
   */
  next(): number {
    let t = (this.state += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /**
   * Generate random integer between min (inclusive) and max (inclusive)
   */
  nextInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  /**
   * Roll a single die (1-6)
   */
  rollDie(): number {
    return this.nextInt(1, 6);
  }

  /**
   * Roll two dice and return complete roll info
   */
  rollDice(): DiceRoll {
    const die1 = this.rollDie();
    const die2 = this.rollDie();
    return {
      die1,
      die2,
      total: die1 + die2,
      isDoubles: die1 === die2,
    };
  }

  /**
   * Get current state for serialization
   */
  getState(): number {
    return this.state;
  }

  /**
   * Set state for replay/restore
   */
  setState(state: number): void {
    this.state = state >>> 0;
  }

  /**
   * Clone the RNG with current state
   */
  clone(): SeededRandom {
    const rng = new SeededRandom(0);
    rng.setState(this.state);
    return rng;
  }

  /**
   * Shuffle array in place (Fisher-Yates)
   * Returns the shuffled array
   */
  shuffle<T>(array: T[]): T[] {
    const result = [...array];
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(this.next() * (i + 1));
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }

  /**
   * Pick random element from array
   */
  pick<T>(array: T[]): T {
    if (array.length === 0) {
      throw new Error('Cannot pick from empty array');
    }
    return array[Math.floor(this.next() * array.length)];
  }

  /**
   * Return true with given probability (0-1)
   */
  chance(probability: number): boolean {
    return this.next() < probability;
  }

  /**
   * Generate random float between min and max
   */
  nextFloat(min: number, max: number): number {
    return this.next() * (max - min) + min;
  }

  /**
   * Generate weighted random selection
   * @param weights Array of weights (higher = more likely)
   * @returns Index of selected item
   */
  weightedSelect(weights: number[]): number {
    const total = weights.reduce((sum, w) => sum + w, 0);
    let random = this.next() * total;

    for (let i = 0; i < weights.length; i++) {
      random -= weights[i];
      if (random <= 0) {
        return i;
      }
    }

    return weights.length - 1;
  }
}

/**
 * Create a new SeededRandom instance
 */
export function createRng(seed: number): SeededRandom {
  return new SeededRandom(seed);
}

/**
 * Generate a random seed for new games
 */
export function generateSeed(): number {
  return Math.floor(Math.random() * 0xffffffff);
}
