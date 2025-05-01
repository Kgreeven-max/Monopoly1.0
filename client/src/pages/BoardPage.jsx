import React, { useEffect, useState, useRef } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Avatar, 
  Chip, 
  Tooltip, 
  CircularProgress, 
  Grid, 
  Container,
  Button,
  IconButton,
  Card,
  CardContent,
  useTheme
} from '@mui/material';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';
import PlayerList from '../components/PlayerList';
import { GameLog, gameLogStyle } from '../components/GameLog';
import CardDisplay from '../components/CardDisplay';
import NavBar from '../components/NavBar';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';
import RefreshIcon from '@mui/icons-material/Refresh';
import CasinoIcon from '@mui/icons-material/Casino';

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

// Enhanced board styling
const boardStyle = {
  display: 'grid',
  gridTemplateColumns: '1fr repeat(9, 0.7fr) 1fr',
  gridTemplateRows: '1fr repeat(9, 0.7fr) 1fr',
  width: '95vw',
  height: '95vw',
  maxWidth: '850px',
  maxHeight: '850px',
  margin: '0 auto',
  border: '3px solid #333',
  borderRadius: '16px',
  boxShadow: '0 12px 35px rgba(0,0,0,0.15), inset 0 2px 10px rgba(255,255,255,0.5)',
  position: 'relative',
  backgroundColor: '#EFFFEF',
  backgroundImage: 'radial-gradient(circle at center, #E8F5E9 0%, #C8E6C9 100%)',
  '@media (display-mode: fullscreen)': {
    maxWidth: 'min(95vh, 1200px)',
    maxHeight: 'min(95vh, 1200px)',
    width: 'min(95vw, 95vh)',
    height: 'min(95vw, 95vh)',
  },
  '@media (min-width: 1600px)': {
    maxWidth: '1000px',
    maxHeight: '1000px',
  }
};

// Improved space styling
const spaceStyle = (space) => ({
  border: '1px solid #bbb',
  borderRadius: '4px',
  padding: '5px',
  fontSize: '0.75em',
  textAlign: 'center',
  position: 'relative',
  minWidth: '60px',
  minHeight: '60px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  backgroundColor: space.owner_id ? `${playerColors[space.owner_id % playerColors.length]}20` : 'white', 
  gridColumn: space.col,
  gridRow: space.row,
  transition: 'all 0.3s ease',
  boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.05)',
  '&:hover': {
    backgroundColor: '#f8f8f8',
    transform: 'scale(1.05)',
    zIndex: 10,
    boxShadow: '0 0 15px rgba(0,0,0,0.1), inset 0 1px 3px rgba(0,0,0,0.05)',
  }
});

// Enhanced color stripe for properties
const propertyColorStripe = (group) => ({
  height: '16%', 
  backgroundColor: groupColors[group] || 'transparent',
  width: '100%',
  borderRadius: '3px 3px 0 0',
  boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
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

// Enhanced player token style
const playerTokenStyle = (playerIndex, isCurrentPlayer) => ({
  position: 'absolute',
  bottom: `${5 + playerIndex * 16}%`,
  left: '50%',
  transform: 'translateX(-50%)',
  width: '36px',
  height: '36px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: playerColors[playerIndex % playerColors.length],
  borderRadius: '50%',
  border: isCurrentPlayer ? '3px solid gold' : '2px solid #333',
  boxShadow: isCurrentPlayer 
    ? '0 0 18px gold, 0 0 8px rgba(255,215,0,0.8)' 
    : '0 3px 8px rgba(0,0,0,0.3)',
  zIndex: 100 + playerIndex,
  transition: 'all 1.5s cubic-bezier(0.22, 1, 0.36, 1)',
  animation: isCurrentPlayer ? 'pulse 1.5s infinite' : 'none',
  '&:hover': {
    transform: 'translateX(-50%) scale(1.3)',
    zIndex: 200 + playerIndex,
    boxShadow: '0 0 20px rgba(0, 0, 0, 0.4)'
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '-14px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '0',
    height: '0',
    borderLeft: '8px solid transparent',
    borderRight: '8px solid transparent',
    borderBottom: '12px solid gold',
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

// Enhanced dice display
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
          width: 50,
          height: 50,
          backgroundColor: 'white',
          border: '2px solid #333',
          borderRadius: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.75rem',
          fontWeight: 'bold',
          boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 50%)',
            borderRadius: 'inherit',
          }
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
    gameData: null
  });
  
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const [isFullScreenActive, setIsFullScreenActive] = useState(false);
  const theme = useTheme();
  const boardRef = useRef(null);
  
  // Connect socket and request game state updates
  useEffect(() => {
    if (!isConnected) {
      connectSocket({
        path: '/ws/socket.io',
        transports: ['websocket', 'polling']
      });
    }

    const requestGameStateViaSocket = () => {
      console.log("[BoardPage] Requesting game state update via socket");
      emit('authenticate_socket', { mode: 'display' });
      
      setTimeout(() => {
        emit('request_game_state', { gameId: 1 });
      }, 500);
    };

    if (isConnected) {
      requestGameStateViaSocket();
      const stateRefreshInterval = setInterval(() => {
        requestGameStateViaSocket();
      }, 5000);

      return () => clearInterval(stateRefreshInterval);
    }
  }, [isConnected, emit]);

  // Toggle fullscreen mode
  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      if (boardRef.current?.requestFullscreen) {
        boardRef.current.requestFullscreen().catch(err => {
          console.error(`Error attempting to enable fullscreen: ${err.message}`);
        });
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  // Handler for fullscreen change events
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreenActive(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullScreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullScreenChange);
  }, []);

  // Handler for game state updates
  useEffect(() => {
    const handleGameStateUpdate = (data) => {
      console.log("[BoardPage] Game State Update Received:", data);
      
      // Store previous player positions for animation
      const newPlayerPositions = {};
      gameState?.players?.forEach(player => {
        newPlayerPositions[player.id] = player.position;
      });
      
      setLastPlayerPositions(prevPositions => ({
        ...prevPositions,
        ...newPlayerPositions
      }));
      
      // Force re-render when game state updates
      setLastUpdate(Date.now());
    };

    if (gameState) {
      handleGameStateUpdate(gameState);
    }
  }, [gameState]);

  // Refresh game state manually
  const refreshGameState = () => {
    emit('request_game_state', { gameId: 1 });
  };

  // Prepare board spaces with grid positions
  const boardSpaces = boardLayout.map(space => ({
    ...space,
    ...getGridPosition(space.id),
    // Check if any player owns this property from gameState
    owner_id: gameState?.properties?.find(prop => prop.position === space.id)?.owner_id
  }));

  // Loading state
  if (!gameState || !gameState.players) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          backgroundColor: '#f5f5f5'
        }}
      >
        <CircularProgress size={60} thickness={4} />
        <Typography variant="h6" sx={{ mt: 3, fontWeight: 500 }}>
          Loading game board...
        </Typography>
      </Box>
    );
  }

  return (
    <Box 
      ref={boardRef}
      sx={{ 
        backgroundColor: '#EEFAF3',
        minHeight: '100vh',
        pt: 2,
        pb: 4
      }}
    >
      <Container maxWidth="xl">
        {/* Header with game info and controls */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" fontWeight="600" sx={{ color: theme.palette.primary.main }}>
            Pi-nopoly
          </Typography>
          
          <Box>
            <IconButton 
              onClick={refreshGameState} 
              color="primary"
              sx={{ mr: 1 }}
            >
              <RefreshIcon />
            </IconButton>
            
            <IconButton 
              onClick={toggleFullScreen}
              color="primary"
            >
              {isFullScreenActive ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Box>
        </Box>
        
        {/* Game status display */}
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 3 }}>
          <Chip 
            label={`Game Status: ${gameState?.status || 'Unknown'}`}
            color={gameState?.status === 'In Progress' ? 'success' : 'default'}
            variant="outlined"
            sx={{ mr: 2 }}
          />
          
          {gameState?.current_player_id != null && (
            <Chip 
              label={`Current Player: ${gameState.players.find(p => p.id === gameState.current_player_id)?.username || `Player ${gameState.current_player_id}`}`}
              color="primary"
              variant="outlined"
              sx={{ mr: 2 }}
              avatar={
                <Avatar 
                  sx={{ 
                    bgcolor: playerColors[gameState.current_player_id % playerColors.length]
                  }}
                >
                  {gameState.players.find(p => p.id === gameState.current_player_id)?.username.charAt(0).toUpperCase() || '#'}
                </Avatar>
              }
            />
          )}
          
          {gameState?.last_dice_roll && (
            <Card variant="outlined" sx={{ display: 'inline-flex', alignItems: 'center', borderRadius: 2 }}>
              <CardContent sx={{ p: 1, '&:last-child': { pb: 1 }, display: 'flex', alignItems: 'center' }}>
                <CasinoIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <DiceDisplay diceRoll={gameState.last_dice_roll} />
              </CardContent>
            </Card>
          )}
        </Box>

        {/* Game board and players list */}
        <Grid container spacing={3}>
          {/* Game board */}
          <Grid item xs={12} md={9}>
            <Box sx={boardStyle}>
              {/* Render board spaces */}
              {boardSpaces.map(space => (
                <Tooltip 
                  key={space.id} 
                  title={`${space.name} (${space.id})`}
                  arrow
                >
                  <Box sx={spaceStyle(space)}>
                    {space.type === 'property' && (
                      <Box sx={propertyColorStripe(space.group)} />
                    )}
                    <Typography variant="caption" sx={{ fontWeight: 500 }}>
                      {space.name}
                    </Typography>
                    
                    {/* Render player tokens on this space */}
                    {gameState.players
                      .filter(player => player.position === space.id)
                      .map((player, index) => (
                        <Tooltip key={player.id} title={player.username} arrow>
                          <Box sx={playerTokenStyle(index, gameState.current_player_id === player.id)}>
                            <Typography sx={{ fontSize: '0.7rem', color: 'white', fontWeight: 'bold' }}>
                              {player.username.charAt(0).toUpperCase()}
                            </Typography>
                          </Box>
                        </Tooltip>
                      ))
                    }
                  </Box>
                </Tooltip>
              ))}
            </Box>
          </Grid>
          
          {/* Players list and game log */}
          <Grid item xs={12} md={3}>
            <Card 
              elevation={0} 
              sx={{ 
                mb: 3, 
                borderRadius: 3,
                boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
              }}
            >
              <CardContent>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Players
                </Typography>
                
                {gameState.players.map((player) => (
                  <Box 
                    key={player.id}
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      p: 1, 
                      mb: 1,
                      borderRadius: 2,
                      backgroundColor: gameState.current_player_id === player.id ? 'rgba(46, 125, 50, 0.1)' : 'transparent',
                      border: '1px solid',
                      borderColor: gameState.current_player_id === player.id ? 'primary.light' : 'divider',
                    }}
                  >
                    <Avatar 
                      sx={{ 
                        bgcolor: playerColors[player.id % playerColors.length],
                        width: 36,
                        height: 36,
                        mr: 1.5
                      }}
                    >
                      {player.username.charAt(0).toUpperCase()}
                    </Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight="500">
                        {player.username}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ${player.money} • Space {player.position}
                      </Typography>
                    </Box>
                    {gameState.current_player_id === player.id && (
                      <Chip 
                        label="Turn" 
                        color="success" 
                        size="small"
                        sx={{ ml: 'auto', height: 24 }}
                      />
                    )}
                  </Box>
                ))}
              </CardContent>
            </Card>
            
            <Card 
              elevation={0} 
              sx={{ 
                borderRadius: 3,
                boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
              }}
            >
              <CardContent>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Game Log
                </Typography>
                
                <Box 
                  sx={{ 
                    borderRadius: 2,
                    bgcolor: '#f9f9f9',
                    p: 2,
                    height: 200,
                    overflowY: 'auto',
                  }}
                >
                  {gameState.log && gameState.log.length > 0 ? (
                    <Box component="ul" sx={{ pl: 2, m: 0 }}>
                      {gameState.log.slice().reverse().map((entry, index) => (
                        <Typography 
                          key={index} 
                          component="li" 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ mb: 0.5 }}
                        >
                          {entry}
                        </Typography>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.disabled" align="center">
                      No game events yet
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default BoardPage; 