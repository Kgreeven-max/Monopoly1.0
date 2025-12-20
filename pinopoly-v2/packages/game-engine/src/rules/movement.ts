/**
 * Movement rules for Pinopoly
 */

export const BOARD_SIZE = 40;
export const GO_POSITION = 0;
export const JAIL_POSITION = 10;
export const GO_TO_JAIL_POSITION = 30;

/**
 * Calculate new position after moving forward
 */
export function getNextPosition(currentPosition: number, spaces: number): number {
  return (currentPosition + spaces) % BOARD_SIZE;
}

/**
 * Check if moving would pass GO
 */
export function wouldPassGo(currentPosition: number, spaces: number): boolean {
  return currentPosition + spaces >= BOARD_SIZE;
}

/**
 * Calculate spaces between two positions (going forward)
 */
export function getSpacesBetween(from: number, to: number): number {
  if (to >= from) {
    return to - from;
  }
  // Wrapped around the board
  return BOARD_SIZE - from + to;
}

/**
 * Check if position is a special space (not a property)
 */
export function isSpecialSpace(position: number): boolean {
  const specialSpaces = [
    0,  // GO
    2,  // Community Chest
    4,  // Income Tax
    7,  // Chance
    10, // Jail / Just Visiting
    17, // Community Chest
    20, // Free Parking
    22, // Chance
    30, // Go To Jail
    33, // Community Chest
    36, // Chance
    38, // Luxury Tax
  ];
  return specialSpaces.includes(position);
}

/**
 * Check if position is a Chance space
 */
export function isChanceSpace(position: number): boolean {
  return [7, 22, 36].includes(position);
}

/**
 * Check if position is a Community Chest space
 */
export function isCommunityChestSpace(position: number): boolean {
  return [2, 17, 33].includes(position);
}

/**
 * Get the nearest railroad from a position (for Chance card)
 */
export function getNearestRailroad(position: number): number {
  const railroads = [5, 15, 25, 35]; // Reading, Pennsylvania, B&O, Short Line

  for (const railroad of railroads) {
    if (railroad > position) {
      return railroad;
    }
  }
  // Wrapped around to Reading
  return 5;
}

/**
 * Get the nearest utility from a position (for Chance card)
 */
export function getNearestUtility(position: number): number {
  const electricCompany = 12;
  const waterWorks = 28;

  if (position < electricCompany || position >= waterWorks) {
    return electricCompany;
  }
  return waterWorks;
}

/**
 * Move back a number of spaces
 */
export function moveBack(currentPosition: number, spaces: number): number {
  let newPosition = currentPosition - spaces;
  if (newPosition < 0) {
    newPosition += BOARD_SIZE;
  }
  return newPosition;
}
