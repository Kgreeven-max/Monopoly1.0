import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Avatar, Chip, Tooltip, CircularProgress } from '@mui/material';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';

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

const playerColors = ['#E53935', '#1E88E5', '#43A047', '#FDD835', '#8E24AA', '#FB8C00', '#26A69A', '#EC407A'];

// Basic styling for the board
const boardStyle = {
  display: 'grid',
  gridTemplateColumns: '1fr repeat(9, 0.7fr) 1fr', // Corner, 9 spaces, Corner
  gridTemplateRows: '1fr repeat(9, 0.7fr) 1fr',    // Corner, 9 spaces, Corner
  width: '90vw',
  height: '90vw',
  maxWidth: '800px',
  maxHeight: '800px',
  margin: '20px auto',
  border: '2px solid #333',
  borderRadius: '8px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
  position: 'relative', // For positioning player tokens
  backgroundColor: '#E8F5E9',
};

const spaceStyle = (space) => ({
  border: '1px solid #bbb',
  padding: '4px',
  fontSize: '0.65em',
  textAlign: 'center',
  position: 'relative', // For player tokens within space
  minWidth: '50px', // Ensure minimum size
  minHeight: '50px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  backgroundColor: space.owner_id ? `${playerColors[space.owner_id % playerColors.length]}20` : 'white', 
  gridColumn: space.col,
  gridRow: space.row,
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: '#f5f5f5',
    transform: 'scale(1.02)',
    zIndex: 5,
  }
});

const propertyColorStripe = (group) => ({
  height: '15%', 
  backgroundColor: groupColors[group] || 'transparent',
  width: '100%',
  borderRadius: '2px 2px 0 0',
});

const groupColors = {
    brown: '#795548',
    lightblue: '#03A9F4',
    pink: '#E91E63',
    orange: '#FF9800',
    red: '#F44336',
    yellow: '#FFEB3B',
    green: '#4CAF50',
    blue: '#2196F3',
    railroad: '#757575',
    utility: '#607D8B',
};

// New animated player token style
const playerTokenStyle = (playerIndex, isCurrentPlayer) => ({
  position: 'absolute',
  bottom: `${5 + playerIndex * 15}%`,
  left: '50%',
  transform: 'translateX(-50%)',
  width: '20px',
  height: '20px',
  backgroundColor: playerColors[playerIndex % playerColors.length],
  borderRadius: '50%',
  border: isCurrentPlayer ? '2px solid gold' : '1px solid #333',
  boxShadow: isCurrentPlayer ? '0 0 8px gold' : '0 1px 3px rgba(0,0,0,0.3)',
  zIndex: 10 + playerIndex, // Ensure tokens are visible
  transition: 'all 0.8s cubic-bezier(0.22, 1, 0.36, 1)', // Smooth animation for movement
  animation: isCurrentPlayer ? 'pulse 1.5s infinite' : 'none',
  '@keyframes pulse': {
    '0%': { boxShadow: '0 0 0 0 rgba(255, 215, 0, 0.7)' },
    '70%': { boxShadow: '0 0 0 8px rgba(255, 215, 0, 0)' },
    '100%': { boxShadow: '0 0 0 0 rgba(255, 215, 0, 0)' }
  }
});

// Function to get grid position for each board space index
const getGridPosition = (index) => {
  if (index >= 0 && index <= 10) return { row: 11, col: index + 1 }; // Bottom row (adjusting for 1-based grid index)
  if (index >= 11 && index <= 20) return { row: 11 - (index - 10), col: 1 }; // Left column
  if (index >= 21 && index <= 30) return { row: 1, col: index - 20 + 1 }; // Top row
  if (index >= 31 && index <= 39) return { row: index - 30 + 1, col: 11 }; // Right column
  return { row: 1, col: 1 }; // Default fallback (shouldn't happen)
};

// Component for dice display
const DiceDisplay = ({ diceRoll }) => {
  if (!diceRoll || !Array.isArray(diceRoll) || diceRoll.length !== 2) return null;
  
  return (
    <Box sx={{
      display: 'flex',
      gap: 2,
      justifyContent: 'center',
      mt: 2,
      mb: 2
    }}>
      {diceRoll.map((value, index) => (
        <Box key={index} sx={{
          width: 40,
          height: 40,
          backgroundColor: 'white',
          border: '1px solid #333',
          borderRadius: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          fontWeight: 'bold',
          boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
        }}>
          {value}
        </Box>
      ))}
    </Box>
  );
};

// Component for the player list sidebar
const PlayerList = ({ players, currentPlayerId }) => {
  if (!players || players.length === 0) return <Typography>No players</Typography>;
  
  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      gap: 1,
      maxHeight: '400px',
      overflowY: 'auto',
      p: 1
    }}>
      {players.map((player, index) => (
        <Tooltip key={player.id} title={`Position: ${player.position || 'N/A'}, Money: $${player.money || 0}`}>
          <Chip
            avatar={
              <Avatar 
                sx={{ 
                  bgcolor: playerColors[index % playerColors.length],
                  border: player.id === currentPlayerId ? '2px solid gold' : 'none'
                }}
              >
                {player.username ? player.username.charAt(0).toUpperCase() : '?'}
              </Avatar>
            }
            label={`${player.username || `Player ${player.id}`} ${player.is_bot ? '(Bot)' : ''}`}
            variant={player.id === currentPlayerId ? "filled" : "outlined"}
            sx={{ 
              fontWeight: player.id === currentPlayerId ? 'bold' : 'normal',
              boxShadow: player.id === currentPlayerId ? '0 0 5px rgba(255,215,0,0.5)' : 'none',
              transition: 'all 0.3s ease'
            }}
          />
        </Tooltip>
      ))}
    </Box>
  );
};

// Game activity log component
const GameLog = ({ notifications }) => {
  if (!notifications || notifications.length === 0) return null;
  
  return (
    <Box sx={{ 
      maxHeight: '150px', 
      overflowY: 'auto',
      p: 1,
      border: '1px solid #ddd',
      borderRadius: 1,
      mt: 2,
      fontSize: '0.85rem'
    }}>
      {notifications.map((notification, index) => (
        <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
          {notification.message || notification}
        </Typography>
      ))}
    </Box>
  );
};

function BoardPage() {
  const { gameState } = useGame();
  const { socket, emit, connectSocket, isConnected } = useSocket();
  const [lastPlayerPositions, setLastPlayerPositions] = useState({});
  
  // Connect socket when component mounts
  useEffect(() => {
    if (!isConnected) {
      connectSocket();
    }
  }, [isConnected, connectSocket]);
  
  // Track player positions for animation
  useEffect(() => {
    if (gameState?.players) {
      // Store previous positions to enable animation
      const newPositions = {};
      gameState.players.forEach(player => {
        if (player.id && player.position !== undefined) {
          newPositions[player.id] = player.position;
        }
      });
      setLastPlayerPositions(newPositions);
    }
  }, [gameState?.players]);
  
  useEffect(() => {
    console.log("[BoardPage] Game State Updated:", gameState);
  }, [gameState]);

  if (!gameState || gameState.loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading game board...</Typography>
      </Box>
    );
  }

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
    <Box sx={{ 
      p: 2, 
      display: 'flex', 
      flexDirection: { xs: 'column', md: 'row' },
      alignItems: { xs: 'center', md: 'flex-start' },
      gap: 4
    }}>
      <Box sx={{ flex: 1, maxWidth: '800px' }}>
        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', fontWeight: 'bold', color: '#2E7D32' }}>
          Pi-nopoly Game Board
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">
            Status: <Chip label={gameState?.status || 'Unknown'} color={
              gameState?.status === 'active' ? 'success' : 
              gameState?.status === 'setup' ? 'info' : 
              gameState?.status === 'waiting' ? 'warning' : 'default'
            } size="small" />
          </Typography>
          
          <Typography variant="h6">
            Turn: {gameState?.current_turn || 0}
          </Typography>
        </Box>
        
        {gameState?.lastDiceRoll && <DiceDisplay diceRoll={gameState.lastDiceRoll} />}

        <Box sx={boardStyle}>
          {/* Center area */}
          <Paper elevation={3} sx={{ 
            gridColumn: '2 / 11', 
            gridRow: '2 / 11', 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center', 
            justifyContent: 'center',
            backgroundImage: 'linear-gradient(to bottom right, #E8F5E9, #C8E6C9)',
            borderRadius: '8px',
          }}>
            <Typography variant="h3" sx={{ fontWeight: 'bold', color: '#1B5E20', mb: 2, textShadow: '1px 1px 2px rgba(0,0,0,0.1)' }}>
              Pi-nopoly
            </Typography>
            {gameState?.current_player_id && (
              <Typography variant="h6">
                Current Player: {
                  gameState.players?.find(p => p.id === gameState.current_player_id)?.username || 
                  `Player ${gameState.current_player_id}`
                }
              </Typography>
            )}
          </Paper>
          
          {/* Render Board Spaces */}
          {enrichedBoard.map((space) => (
            <Box key={space.id} sx={spaceStyle({ ...space, col: space.gridPos.col, row: space.gridPos.row })}>
              {space.type === 'property' && <Box sx={propertyColorStripe(space.group)} />} 
              <Typography variant="caption" sx={{ fontWeight: 'bold', flexGrow: 1 }}>{space.name}</Typography>
              
              {space.owner_id && 
                <Tooltip title={`Owned by: ${gameState.players?.find(p => p.id === space.owner_id)?.username || `Player ${space.owner_id}`}`}>
                  <Box sx={{ 
                    height: '4px', 
                    width: '80%', 
                    margin: '0 auto',
                    backgroundColor: playerColors[space.owner_id % playerColors.length],
                    borderRadius: '2px'
                  }} />
                </Tooltip>
              }
              
              {/* Render Player Tokens within this space */}
              {gameState?.players
                ?.filter(p => p.position === space.id)
                .map((player, index) => (
                  <Tooltip 
                    key={player.id} 
                    title={`${player.username || `Player ${player.id}`} ${player.is_bot ? '(Bot)' : ''}`}
                  >
                    <Box 
                      sx={playerTokenStyle(
                        index, 
                        player.id === gameState.current_player_id
                      )} 
                    />
                  </Tooltip>
                ))}
            </Box>
          ))}
        </Box>
        
        <GameLog notifications={gameState.notifications} />
      </Box>
      
      <Box sx={{ 
        width: { xs: '100%', md: '250px' }, 
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        p: 2,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Typography variant="h6" gutterBottom>Players</Typography>
        <PlayerList 
          players={gameState.players || []} 
          currentPlayerId={gameState.current_player_id} 
        />
      </Box>
    </Box>
  );
}

export default BoardPage; 