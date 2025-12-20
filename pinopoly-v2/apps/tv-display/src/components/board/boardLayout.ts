/**
 * Standard Monopoly board layout
 * 40 spaces, starting from GO and going clockwise
 */

interface SpaceDefinition {
  name: string;
  type: 'property' | 'railroad' | 'utility' | 'chance' | 'community' | 'tax' | 'corner';
  colorGroup?: string;
  price?: number;
}

export const BOARD_LAYOUT: SpaceDefinition[] = [
  // Bottom row (right to left when looking at board)
  { name: 'GO', type: 'corner' },
  { name: 'Mediterranean Avenue', type: 'property', colorGroup: 'brown', price: 60 },
  { name: 'Community Chest', type: 'community' },
  { name: 'Baltic Avenue', type: 'property', colorGroup: 'brown', price: 60 },
  { name: 'Income Tax', type: 'tax', price: 200 },
  { name: 'Reading Railroad', type: 'railroad', price: 200 },
  { name: 'Oriental Avenue', type: 'property', colorGroup: 'lightBlue', price: 100 },
  { name: 'Chance', type: 'chance' },
  { name: 'Vermont Avenue', type: 'property', colorGroup: 'lightBlue', price: 100 },
  { name: 'Connecticut Avenue', type: 'property', colorGroup: 'lightBlue', price: 120 },
  { name: 'Jail', type: 'corner' },

  // Left column (bottom to top)
  { name: 'St. Charles Place', type: 'property', colorGroup: 'pink', price: 140 },
  { name: 'Electric Company', type: 'utility', price: 150 },
  { name: 'States Avenue', type: 'property', colorGroup: 'pink', price: 140 },
  { name: 'Virginia Avenue', type: 'property', colorGroup: 'pink', price: 160 },
  { name: 'Pennsylvania Railroad', type: 'railroad', price: 200 },
  { name: 'St. James Place', type: 'property', colorGroup: 'orange', price: 180 },
  { name: 'Community Chest', type: 'community' },
  { name: 'Tennessee Avenue', type: 'property', colorGroup: 'orange', price: 180 },
  { name: 'New York Avenue', type: 'property', colorGroup: 'orange', price: 200 },
  { name: 'Free Parking', type: 'corner' },

  // Top row (left to right)
  { name: 'Kentucky Avenue', type: 'property', colorGroup: 'red', price: 220 },
  { name: 'Chance', type: 'chance' },
  { name: 'Indiana Avenue', type: 'property', colorGroup: 'red', price: 220 },
  { name: 'Illinois Avenue', type: 'property', colorGroup: 'red', price: 240 },
  { name: 'B&O Railroad', type: 'railroad', price: 200 },
  { name: 'Atlantic Avenue', type: 'property', colorGroup: 'yellow', price: 260 },
  { name: 'Ventnor Avenue', type: 'property', colorGroup: 'yellow', price: 260 },
  { name: 'Water Works', type: 'utility', price: 150 },
  { name: 'Marvin Gardens', type: 'property', colorGroup: 'yellow', price: 280 },
  { name: 'Go To Jail', type: 'corner' },

  // Right column (top to bottom)
  { name: 'Pacific Avenue', type: 'property', colorGroup: 'green', price: 300 },
  { name: 'North Carolina Avenue', type: 'property', colorGroup: 'green', price: 300 },
  { name: 'Community Chest', type: 'community' },
  { name: 'Pennsylvania Avenue', type: 'property', colorGroup: 'green', price: 320 },
  { name: 'Short Line', type: 'railroad', price: 200 },
  { name: 'Chance', type: 'chance' },
  { name: 'Park Place', type: 'property', colorGroup: 'blue', price: 350 },
  { name: 'Luxury Tax', type: 'tax', price: 100 },
  { name: 'Boardwalk', type: 'property', colorGroup: 'blue', price: 400 },
];

// Color group definitions
export const COLOR_GROUPS: Record<string, { count: number; houseCost: number }> = {
  brown: { count: 2, houseCost: 50 },
  lightBlue: { count: 3, houseCost: 50 },
  pink: { count: 3, houseCost: 100 },
  orange: { count: 3, houseCost: 100 },
  red: { count: 3, houseCost: 150 },
  yellow: { count: 3, houseCost: 150 },
  green: { count: 3, houseCost: 200 },
  blue: { count: 2, houseCost: 200 },
};

// Get properties by color group
export function getPropertiesByColor(color: string): number[] {
  return BOARD_LAYOUT
    .map((space, index) => ({ space, index }))
    .filter(({ space }) => space.colorGroup === color)
    .map(({ index }) => index);
}

// Get space name by position
export function getSpaceName(position: number): string {
  return BOARD_LAYOUT[position]?.name || `Space ${position}`;
}
