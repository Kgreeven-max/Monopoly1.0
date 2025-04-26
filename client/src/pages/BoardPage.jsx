import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, Paper, Avatar, Chip, Tooltip, CircularProgress, Grid } from '@mui/material';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';
import PlayerList from '../components/PlayerList';
import { GameLog, gameLogStyle } from '../components/GameLog';
import CardDisplay from '../components/CardDisplay';
import NavBar from '../components/NavBar';

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
  width: '30px', // Larger tokens
  height: '30px', // Larger tokens
  backgroundColor: playerColors[playerIndex % playerColors.length],
  borderRadius: '50%',
  border: isCurrentPlayer ? '3px solid gold' : '2px solid #333',
  boxShadow: isCurrentPlayer ? '0 0 15px gold' : '0 3px 8px rgba(0,0,0,0.7)', // More obvious shadow
  zIndex: 100 + playerIndex, // Higher z-index to ensure tokens are always visible
  transition: 'all 1.5s cubic-bezier(0.22, 1, 0.36, 1)', // Slower animation for more visibility
  animation: isCurrentPlayer ? 'pulse 1.5s infinite' : 'none',
  '&:hover': {
    transform: 'translateX(-50%) scale(1.3)', // Scale up on hover
    zIndex: 200 + playerIndex, // Even higher z-index on hover
    boxShadow: '0 0 20px rgba(0, 0, 0, 0.5)' // Stronger shadow on hover
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '-12px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '0',
    height: '0',
    borderLeft: '8px solid transparent',
    borderRight: '8px solid transparent',
    borderBottom: '10px solid #333',
    display: isCurrentPlayer ? 'block' : 'none'
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

function BoardPage() {
  const { gameState } = useGame();
  const { socket, emit, connectSocket, isConnected } = useSocket();
  const [lastPlayerPositions, setLastPlayerPositions] = useState({});
  const [boardState, setBoardState] = useState({
    loading: true,
    error: null,
    retryCount: 0,
    gameData: null  // Store game data directly
  });
  
  // Track the last update timestamp to force re-renders
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  
  // Connect socket and request game state updates
  useEffect(() => {
    if (!isConnected) {
      // Force a specific URL for socket connection
      connectSocket({
        path: '/ws/socket.io', // Path configured in Flask-SocketIO 
        transports: ['websocket', 'polling']
      });
    }

    // Socket-based game state request
    const requestGameStateViaSocket = () => {
      console.log("[BoardPage] Requesting game state update via socket");
      // Send specific authentication info in case it's needed
      emit('authenticate_socket', { mode: 'display' });
      
      // After short delay to ensure auth is processed
      setTimeout(() => {
        emit('request_game_state', { gameId: 1 });
      }, 500);
    };

    // Request game state immediately after connection and periodically
    if (isConnected) {
      requestGameStateViaSocket();
      
      // Set up socket listener for game state updates
      const handleGameStateUpdate = (data) => {
        console.log("[BoardPage] Received game state update via socket:", data);
        setBoardState(prev => ({
          ...prev,
          loading: false,
          gameData: data,
          error: null
        }));
      };

      socket.on('game_state_update', handleGameStateUpdate);
      
      // Periodically refresh game state every 3 seconds
      const refreshInterval = setInterval(() => {
        emit('request_game_state', { gameId: 1 });
      }, 3000);
      
      // Clean up
      return () => {
        clearInterval(refreshInterval);
        socket.off('game_state_update', handleGameStateUpdate);
      };
    }
  }, [isConnected, connectSocket, emit, socket]);
  
  // Update from gameState context if it's available
  useEffect(() => {
    if (gameState && !gameState.loading) {
      setBoardState(prev => ({
        loading: false,
        error: null,
        retryCount: 0,
        gameData: gameState
      }));
    }
  }, [gameState]);
  
  // Track player positions for animation
  useEffect(() => {
    const players = boardState.gameData?.players || gameState?.players;
    if (players) {
      // Store previous positions to enable animation
      const newPositions = {};
      players.forEach(player => {
        if (player.id && player.position !== undefined) {
          newPositions[player.id] = player.position;
        }
      });
      setLastPlayerPositions(newPositions);
    }
  }, [boardState.gameData, gameState?.players]);

  // Update player positions when game state changes
  useEffect(() => {
    if (gameState && gameState.players && gameState.players.length > 0) {
      console.log("[BoardPage] Updating player positions from game state:", gameState.players);
      // Force a re-render to update player token positions
      setLastUpdate(Date.now());
    }
  }, [gameState.players]);

  // Use game data from either boardState or gameState context
  const gameData = boardState.gameData || gameState || {
    status: 'initializing',
    players: [],
    properties: [],
    current_turn: 0,
    current_player_id: null,
    notifications: []
  };

  // If still loading, show loading indicator
  if (!gameData.players && boardState.loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading game board...</Typography>
      </Box>
    );
  }

  // Enrich boardLayout with dynamic data from gameData.properties
  const enrichedBoard = boardLayout.map(space => {
    const propertyData = gameData?.properties?.find(p => p.position === space.id);
    return { 
      ...space, 
      ...propertyData, // Add owner_id, improvement_level, etc.
      gridPos: getGridPosition(space.id) // Calculate grid position
    };
  });
  
  return (
    <>
      <NavBar />
      <Grid container spacing={2} sx={{ height: '100vh', overflow: 'hidden' }}>
        {/* Add global styles for animations */}
        <style>{`
          @keyframes pulse {
            0% { transform: translateX(-50%) scale(1); }
            50% { transform: translateX(-50%) scale(1.2); }
            100% { transform: translateX(-50%) scale(1); }
          }
          
          @keyframes bounce {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(-10px); }
          }
        `}</style>
        
        {/* Player list sidebar */}
        <Grid item xs={12} md={3} sx={{ 
          height: '100%', 
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          p: 2,
          borderRight: '1px solid rgba(0, 0, 0, 0.12)'
        }}>
          <Typography variant="h5" gutterBottom fontWeight="bold" color="primary">
            Players
          </Typography>
          <PlayerList 
            players={gameData.players || []} 
            currentPlayerId={gameData.current_player_id} 
          />
          
          {/* Game log section */}
          <Box sx={gameLogStyle.container}>
            <Typography variant="h5" gutterBottom fontWeight="bold" color="primary" sx={{ mt: 4 }}>
              Game Log
            </Typography>
            <GameLog notifications={gameData.notifications || []} />
          </Box>
        </Grid>
        <Grid item xs={12} md={9}>
          <Box sx={{ 
            p: 2, 
            display: 'flex', 
            flexDirection: { xs: 'column', md: 'row' },
            alignItems: { xs: 'center', md: 'flex-start' },
            gap: 4,
            backgroundColor: '#f9f9f9', // Light background for the whole page
            minHeight: '100vh'
          }}>
            <Box sx={{ flex: 1, maxWidth: '800px' }}>
              <Typography variant="h4" gutterBottom sx={{ 
                textAlign: 'center', 
                fontWeight: 'bold', 
                color: '#2E7D32',
                textShadow: '1px 1px 2px rgba(0,0,0,0.1)'
              }}>
                Pi-nopoly Game Board
              </Typography>
              
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                mb: 2,
                p: 2,
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.08)'
              }}>
                <Typography variant="h6">
                  Status: <Chip label={gameData?.status || 'Unknown'} color={
                    gameData?.status === 'active' ? 'success' : 
                    gameData?.status === 'setup' ? 'info' : 
                    gameData?.status === 'waiting' ? 'warning' : 'default'
                  } size="small" />
                </Typography>
                
                <Typography variant="h6">
                  Turn: {gameData?.current_turn || 0}
                </Typography>
              </Box>
              
              {gameData?.lastDiceRoll && <DiceDisplay diceRoll={gameData.lastDiceRoll} />}

              {/* Add economic info */}
              {gameData?.economic_state && (
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
                  <Chip 
                    label={`Economy: ${gameData.economic_state.state} (Inflation: ${(gameData.economic_state.inflation_rate * 100).toFixed(1)}%, Interest: ${(gameData.economic_state.interest_rate * 100).toFixed(1)}%)`}
                    color={
                      gameData.economic_state.state === 'boom' ? 'success' : 
                      gameData.economic_state.state === 'recession' ? 'error' : 'primary'
                    }
                    variant="outlined"
                  />
                </Box>
              )}

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
                  {gameData?.current_player_id && (
                    <Typography variant="h6">
                      Current Player: {
                        gameData.players?.find(p => p.id === gameData.current_player_id)?.username || 
                        `Player ${gameData.current_player_id}`
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
                      <Tooltip title={`Owned by: ${gameData.players?.find(p => p.id === space.owner_id)?.username || `Player ${space.owner_id}`}`}>
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
                    {gameData?.players
                      ?.filter(p => p.position === space.id)
                      .map((player, index) => (
                        <Tooltip 
                          key={`player-token-${player.id}-${player.position}-${lastUpdate}`} 
                          title={`${player.username || `Player ${player.id}`} ${player.is_bot ? '(Bot)' : ''} - $${player.money || 0}`}
                        >
                          <Box 
                            sx={{
                              ...playerTokenStyle(
                                player.id - 1, // Use player ID directly for consistent colors
                                player.id === gameData.current_player_id
                              ),
                              transition: 'all 1.5s cubic-bezier(0.22, 1, 0.36, 1)', // Ensure smooth transitions
                              animation: player.id === gameData.current_player_id ? 'pulse 1.5s infinite' : 'none',
                            }}
                            data-player-id={player.id}
                            data-position={player.position}
                            data-timestamp={lastUpdate}
                          >
                            <Typography sx={{ 
                              fontSize: '14px', // Bigger text for better visibility
                              fontWeight: 'bold', 
                              color: 'white', 
                              textAlign: 'center',
                              lineHeight: '30px', // Match the new height
                              textShadow: '1px 1px 3px black'
                            }}>
                              {player.id}
                            </Typography>
                          </Box>
                        </Tooltip>
                      ))}
                  </Box>
                ))}
              </Box>
            </Box>
          </Box>
        </Grid>
        
        {/* Add CardDisplay component */}
        <CardDisplay />
      </Grid>
    </>
  );
}

export default BoardPage; 