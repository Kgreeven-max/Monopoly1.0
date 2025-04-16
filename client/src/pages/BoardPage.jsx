import React, { useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useGame } from '../contexts/GameContext'; // Get game state

// Define board layout structure (could be moved to a constants file)
// Simplified: assumes 40 spaces, 11 per side (corners shared)
const boardLayout = [
  // Bottom row (left to right, 0-10)
  { id: 0, name: 'GO', type: 'corner' }, 
  { id: 1, name: 'Med. Ave', type: 'property', group: 'brown' },
  { id: 2, name: 'Com. Chest', type: 'chest' },
  { id: 3, name: 'Baltic Ave', type: 'property', group: 'brown' },
  { id: 4, name: 'Income Tax', type: 'tax' },
  { id: 5, name: 'Reading RR', type: 'railroad' },
  { id: 6, name: 'Oriental Ave', type: 'property', group: 'lightblue' },
  { id: 7, name: 'Chance', type: 'chance' },
  { id: 8, name: 'Vermont Ave', type: 'property', group: 'lightblue' },
  { id: 9, name: 'Conn. Ave', type: 'property', group: 'lightblue' },
  { id: 10, name: 'Jail', type: 'corner' },
  // Left column (bottom to top, 11-20)
  { id: 11, name: 'St. Charles', type: 'property', group: 'pink' },
  { id: 12, name: 'Electric Co.', type: 'utility' },
  { id: 13, name: 'States Ave', type: 'property', group: 'pink' },
  { id: 14, name: 'Virginia Ave', type: 'property', group: 'pink' },
  { id: 15, name: 'Penn RR', type: 'railroad' },
  { id: 16, name: 'St. James', type: 'property', group: 'orange' },
  { id: 17, name: 'Com. Chest', type: 'chest' },
  { id: 18, name: 'Tenn. Ave', type: 'property', group: 'orange' },
  { id: 19, name: 'New York Ave', type: 'property', group: 'orange' },
  { id: 20, name: 'Free Parking', type: 'corner' },
  // Top row (left to right, 21-30)
  { id: 21, name: 'Kentucky Ave', type: 'property', group: 'red' },
  { id: 22, name: 'Chance', type: 'chance' },
  { id: 23, name: 'Indiana Ave', type: 'property', group: 'red' },
  { id: 24, name: 'Illinois Ave', type: 'property', group: 'red' },
  { id: 25, name: 'B&O RR', type: 'railroad' },
  { id: 26, name: 'Atlantic Ave', type: 'property', group: 'yellow' },
  { id: 27, name: 'Ventnor Ave', type: 'property', group: 'yellow' },
  { id: 28, name: 'Water Works', type: 'utility' },
  { id: 29, name: 'Marvin Gardens', type: 'property', group: 'yellow' },
  { id: 30, name: 'Go To Jail', type: 'corner' },
  // Right column (top to bottom, 31-39)
  { id: 31, name: 'Pacific Ave', type: 'property', group: 'green' },
  { id: 32, name: 'NC Ave', type: 'property', group: 'green' },
  { id: 33, name: 'Com. Chest', type: 'chest' },
  { id: 34, name: 'Penn Ave', type: 'property', group: 'green' },
  { id: 35, name: 'Short Line', type: 'railroad' },
  { id: 36, name: 'Chance', type: 'chance' },
  { id: 37, name: 'Park Place', type: 'property', group: 'blue' },
  { id: 38, name: 'Luxury Tax', type: 'tax' },
  { id: 39, name: 'Boardwalk', type: 'property', group: 'blue' },
];

const playerColors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange'];

// Basic styling (can be significantly enhanced)
const boardStyle = {
  display: 'grid',
  gridTemplateColumns: '1fr repeat(9, 0.7fr) 1fr', // Corner, 9 spaces, Corner
  gridTemplateRows: '1fr repeat(9, 0.7fr) 1fr',    // Corner, 9 spaces, Corner
  width: '80vw',
  height: '80vw',
  maxWidth: '800px',
  maxHeight: '800px',
  margin: '20px auto',
  border: '2px solid black',
  position: 'relative', // For positioning player tokens
};

const spaceStyle = (space) => ({
  border: '1px solid #ccc',
  padding: '2px',
  fontSize: '0.6em',
  textAlign: 'center',
  position: 'relative', // For player tokens within space
  minWidth: '50px', // Ensure minimum size
  minHeight: '50px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  backgroundColor: space.owner_id ? playerColors[space.owner_id % playerColors.length] + '30' : 'white', // Basic ownership indication
  gridColumn: space.col,
  gridRow: space.row,
});

const propertyColorStripe = (group) => ({
  height: '15%', 
  backgroundColor: groupColors[group] || 'transparent',
  width: '100%',
});

const groupColors = {
    brown: '#A0522D',
    lightblue: '#ADD8E6',
    pink: '#FFC0CB',
    orange: '#FFA500',
    red: '#FF0000',
    yellow: '#FFFF00',
    green: '#008000',
    blue: '#0000FF',
    railroad: '#808080',
    utility: '#D3D3D3',
};

const playerTokenStyle = (playerIndex) => ({
  position: 'absolute',
  bottom: `${5 + playerIndex * 15}%`,
  left: '50%',
  transform: 'translateX(-50%)',
  width: '10px',
  height: '10px',
  backgroundColor: playerColors[playerIndex % playerColors.length],
  borderRadius: '50%',
  border: '1px solid black',
  zIndex: 10 + playerIndex, // Ensure tokens are visible
});

// Function to get grid position for each board space index
const getGridPosition = (index) => {
  if (index >= 0 && index <= 10) return { row: 11, col: index + 1 }; // Bottom row (adjusting for 1-based grid index)
  if (index >= 11 && index <= 20) return { row: 11 - (index - 10), col: 1 }; // Left column
  if (index >= 21 && index <= 30) return { row: 1, col: index - 20 + 1 }; // Top row
  if (index >= 31 && index <= 39) return { row: index - 30 + 1, col: 11 }; // Right column
  return { row: 1, col: 1 }; // Default fallback (shouldn't happen)
};

function BoardPage() {
  const { gameState } = useGame();
  
  useEffect(() => {
      console.log("[BoardPage] Game State Updated:", gameState);
  }, [gameState]);

  // Enrich boardLayout with dynamic data from gameState.properties
  const enrichedBoard = boardLayout.map(space => {
      const propertyData = gameState?.properties?.find(p => p.position === space.id);
      return { 
          ...space, 
          ...propertyData, // Add owner_id, improvement_level, etc.
          gridPos: getGridPosition(space.id) // Calculate grid position
      };
  });
  
  return (
    <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h4" gutterBottom>Game Board</Typography>
      <Typography variant="subtitle1" gutterBottom>
        Status: {gameState?.status || 'Loading...'} | Current Turn: Player {gameState?.current_player_id ?? 'N/A'}
      </Typography>

      <Box sx={boardStyle}>
        {/* Center area (placeholder) */}
        <Paper elevation={1} sx={{ gridColumn: '2 / 11', gridRow: '2 / 11', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="h6">Pi-nopoly</Typography>
        </Paper>
        
        {/* Render Board Spaces */}
        {enrichedBoard.map((space) => (
          <Box key={space.id} sx={spaceStyle({ ...space, col: space.gridPos.col, row: space.gridPos.row })}>
            {space.type === 'property' && <Box sx={propertyColorStripe(space.group)} />} 
            <Typography variant="caption" sx={{ flexGrow: 1 }}>{space.name}</Typography>
            {/* Display owner/price/level? */}
            {space.owner_id && <Typography variant="caption" sx={{ fontSize: '0.5em' }}>Owner: {space.owner_id}</Typography>}
            {/* Render Player Tokens within this space */}
            {gameState?.players
              ?.filter(p => p.position === space.id)
              .map((player, index) => (
                <Box key={player.id} sx={playerTokenStyle(index)} title={player.username} />
              ))}
          </Box>
        ))}
      </Box>
    </Box>
  );
}

export default BoardPage; 