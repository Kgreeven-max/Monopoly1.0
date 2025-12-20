/**
 * Property rules for Pinopoly
 */

import type { GameState, PropertyState, ColorGroup } from '../state/types';

/**
 * Color group sizes (number of properties per group)
 */
const GROUP_SIZES: Record<ColorGroup, number> = {
  brown: 2,
  lightBlue: 3,
  pink: 3,
  orange: 3,
  red: 3,
  yellow: 3,
  green: 3,
  darkBlue: 2,
};

/**
 * Railroad positions
 */
const RAILROAD_POSITIONS = [5, 15, 25, 35];

/**
 * Utility positions
 */
const UTILITY_POSITIONS = [12, 28];

/**
 * Get a property by its position
 */
export function getPropertyByPosition(
  state: GameState,
  position: number
): PropertyState | undefined {
  return state.properties[position];
}

/**
 * Check if a property is owned
 */
export function isPropertyOwned(
  state: GameState,
  position: number
): boolean {
  const property = state.properties[position];
  return property?.ownerId !== null;
}

/**
 * Get all properties owned by a player
 */
export function getPlayerProperties(
  state: GameState,
  playerId: string
): PropertyState[] {
  return Object.values(state.properties).filter(
    (p) => p.ownerId === playerId
  );
}

/**
 * Get all properties in a color group
 */
export function getGroupProperties(
  state: GameState,
  group: ColorGroup
): PropertyState[] {
  return Object.values(state.properties).filter(
    (p) => p.group === group
  );
}

/**
 * Check if player owns all properties in a group (monopoly)
 */
export function hasMonopoly(
  state: GameState,
  playerId: string,
  group: ColorGroup
): boolean {
  const groupProps = getGroupProperties(state, group);
  return groupProps.every((p) => p.ownerId === playerId && !p.isMortgaged);
}

/**
 * Count how many railroads a player owns
 */
export function countOwnedRailroads(
  state: GameState,
  playerId: string
): number {
  return RAILROAD_POSITIONS.filter(
    (pos) => state.properties[pos]?.ownerId === playerId
  ).length;
}

/**
 * Count how many utilities a player owns
 */
export function countOwnedUtilities(
  state: GameState,
  playerId: string
): number {
  return UTILITY_POSITIONS.filter(
    (pos) => state.properties[pos]?.ownerId === playerId
  ).length;
}

/**
 * Calculate rent for a property
 */
export function calculateRent(
  state: GameState,
  position: number
): number {
  const property = state.properties[position];
  if (!property || !property.ownerId || property.isMortgaged) {
    return 0;
  }

  const owner = state.players[property.ownerId];
  if (!owner) return 0;

  // Apply economic multiplier
  const economyMultiplier = state.economy.rentMultiplier;

  // Railroad rent
  if (property.type === 'railroad') {
    const railroadsOwned = countOwnedRailroads(state, property.ownerId);
    const baseRent = 25;
    const rent = baseRent * Math.pow(2, railroadsOwned - 1);
    return Math.floor(rent * economyMultiplier);
  }

  // Utility rent
  if (property.type === 'utility') {
    const utilitiesOwned = countOwnedUtilities(state, property.ownerId);
    const diceRoll = state.lastDiceRoll?.total || 7; // Default to 7 if no roll
    const multiplier = utilitiesOwned === 2 ? 10 : 4;
    return Math.floor(diceRoll * multiplier * economyMultiplier);
  }

  // Street property rent
  if (property.type === 'street' && property.group) {
    // No houses - check for monopoly
    if (property.houses === 0) {
      const hasFullSet = hasMonopoly(state, property.ownerId, property.group);
      const baseRent = property.baseRent;
      const rent = hasFullSet ? baseRent * 2 : baseRent;
      return Math.floor(rent * economyMultiplier);
    }

    // Has houses or hotel
    const houseIndex = Math.min(property.houses - 1, property.rentLevels.length - 1);
    const rent = property.rentLevels[houseIndex];
    return Math.floor(rent * economyMultiplier);
  }

  return 0;
}

/**
 * Check if a player can build a house on a property
 * Must own all properties in group and build evenly
 */
export function canBuildHouse(
  state: GameState,
  propertyId: number
): boolean {
  const property = state.properties[propertyId];
  if (!property || !property.ownerId || !property.group) {
    return false;
  }

  // Can't build on non-streets
  if (property.type !== 'street') {
    return false;
  }

  // Can't build if mortgaged
  if (property.isMortgaged) {
    return false;
  }

  // Can't build more than hotel (5)
  if (property.houses >= 5) {
    return false;
  }

  // Must have monopoly
  if (!hasMonopoly(state, property.ownerId, property.group)) {
    return false;
  }

  // Check even building rule
  const groupProps = getGroupProperties(state, property.group);
  const minHouses = Math.min(...groupProps.map((p) => p.houses));

  // Can only build if this property has the minimum houses in the group
  return property.houses === minHouses;
}

/**
 * Check if a player can sell a house from a property
 * Must sell evenly across the group
 */
export function canSellHouse(
  state: GameState,
  propertyId: number
): boolean {
  const property = state.properties[propertyId];
  if (!property || !property.ownerId || !property.group) {
    return false;
  }

  // Can't sell if no houses
  if (property.houses === 0) {
    return false;
  }

  // Check even selling rule
  const groupProps = getGroupProperties(state, property.group);
  const maxHouses = Math.max(...groupProps.map((p) => p.houses));

  // Can only sell if this property has the maximum houses in the group
  return property.houses === maxHouses;
}

/**
 * Calculate the total value of a player's properties
 */
export function calculatePropertyValue(
  state: GameState,
  playerId: string
): number {
  const properties = getPlayerProperties(state, playerId);
  let total = 0;

  for (const property of properties) {
    if (property.isMortgaged) {
      // Mortgaged properties worth 50% of their value
      total += property.mortgageValue;
    } else {
      // Full property value plus house value
      total += property.currentValue;
      if (property.houses > 0) {
        total += property.houses * property.houseCost;
      }
    }
  }

  return total;
}

/**
 * Calculate a player's net worth
 */
export function calculateNetWorth(
  state: GameState,
  playerId: string
): number {
  const player = state.players[playerId];
  if (!player) return 0;

  let netWorth = player.money;
  netWorth += calculatePropertyValue(state, playerId);

  // Add CD value
  for (const cd of player.cds) {
    netWorth += cd.principal;
  }

  // Subtract loan debt
  for (const loan of player.loans) {
    if (loan.isActive) {
      netWorth -= loan.balance;
    }
  }

  // Subtract HELOC debt
  for (const heloc of player.helocs) {
    if (heloc.isActive) {
      netWorth -= heloc.balance;
    }
  }

  return netWorth;
}

/**
 * Get the sell value of a house (typically 50% of cost)
 */
export function getHouseSellValue(property: PropertyState): number {
  return Math.floor(property.houseCost / 2);
}
