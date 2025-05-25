import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, Paper, Avatar, Chip, Tooltip, CircularProgress, Grid } from '@mui/material';
import { useGame } from '../../game-state/contexts/GameContext';
import { useSocket } from '../../game-state/contexts/SocketContext';
import PlayerList from '../../components/ui/PlayerList';
import { GameLog, gameLogStyle } from '../../components/ui/GameLog';
import CardDisplay from '../../components/cards/CardDisplay';
import NavBar from '../../components/ui/NavBar';
import AnimatedPlayerToken from '../../game-board/components/PlayerToken/AnimatedPlayerToken';
import DiceAnimation from '../../game-board/components/DiceAnimation/DiceAnimation';

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
  width: '95vw',
  height: '95vw',
  maxWidth: '900px',
  maxHeight: '900px',
  margin: '10px auto',
  border: '3px solid #333',
  borderRadius: '10px',
  boxShadow: '0 6px 25px rgba(0,0,0,0.2)',
  position: 'relative', // For positioning player tokens
  backgroundColor: '#E8F5E9',
  // Make board responsive in fullscreen
  '@media (display-mode: fullscreen)': {
    maxWidth: 'min(95vh, 1200px)',
    maxHeight: 'min(95vh, 1200px)',
    width: 'min(95vw, 95vh)',
    height: 'min(95vw, 95vh)',
  },
  // Make board larger for larger screens
  '@media (min-width: 1600px)': {
    maxWidth: '1000px',
    maxHeight: '1000px',
  }
};

const spaceStyle = (space) => ({
  border: '1px solid #bbb',
  padding: '5px',
  fontSize: '0.75em', // Slightly larger text
  textAlign: 'center',
  position: 'relative', // For player tokens within space
  minWidth: '55px', // Ensure minimum size
  minHeight: '55px',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  backgroundColor: space.owner_id ? `${playerColors[space.owner_id % playerColors.length]}20` : 'white', 
  gridColumn: space.col,
  gridRow: space.row,
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: '#f5f5f5',
    transform: 'scale(1.05)',
    zIndex: 10,
    boxShadow: '0 0 15px rgba(0,0,0,0.2)',
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
  width: '35px', // Larger tokens
  height: '35px', // Larger tokens
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
  
  // Check for fullscreen state changes
  const [isFullScreenActive, setIsFullScreenActive] = useState(false);
  
  // Add board reference and size tracking
  const boardRef = useRef(null);
  const [boardSize, setBoardSize] = useState(900);
  
  // Dice animation state
  const [showDiceAnimation, setShowDiceAnimation] = useState(false);
  const [animatedDiceRoll, setAnimatedDiceRoll] = useState(null);
  
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

      // Listen for player movement events
      const handlePlayerMoved = (data) => {
        console.log("[BoardPage] Player moved:", data);
        setBoardState(prev => {
          if (!prev.gameData) return prev;
          
          const updatedPlayers = prev.gameData.players?.map(player => 
            player.id === data.playerId 
              ? { ...player, position: data.newPosition }
              : player
          ) || [];
          
          return {
            ...prev,
            gameData: {
              ...prev.gameData,
              players: updatedPlayers
            }
          };
        });
      };

      // Listen for dice roll events
      const handleDiceRolled = (data) => {
        console.log("[BoardPage] Dice rolled:", data);
        setBoardState(prev => ({
          ...prev,
          gameData: {
            ...prev.gameData,
            lastDiceRoll: data.roll
          }
        }));
        
        // Show dice animation
        if (data.roll && Array.isArray(data.roll)) {
          setAnimatedDiceRoll(data.roll);
          setShowDiceAnimation(true);
        }
      };

      socket.on('game_state_update', handleGameStateUpdate);
      socket.on('player_moved', handlePlayerMoved);
      socket.on('dice_rolled', handleDiceRolled);
      
      // Periodically refresh game state every 3 seconds
      const refreshInterval = setInterval(() => {
        emit('request_game_state', { gameId: 1 });
      }, 3000);
      
      // Clean up
      return () => {
        clearInterval(refreshInterval);
        socket.off('game_state_update', handleGameStateUpdate);
        socket.off('player_moved', handlePlayerMoved);
        socket.off('dice_rolled', handleDiceRolled);
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

  // Check for fullscreen state changes
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreenActive(!!(
        document.fullscreenElement || 
        document.webkitFullscreenElement || 
        document.mozFullScreenElement || 
        document.msFullscreenElement
      ));
    };
    
    document.addEventListener('fullscreenchange', handleFullScreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
    document.addEventListener('mozfullscreenchange', handleFullScreenChange);
    document.addEventListener('MSFullscreenChange', handleFullScreenChange);
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullScreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullScreenChange);
    };
  }, []);

  // Track board size for responsive token positioning
  useEffect(() => {
    const updateBoardSize = () => {
      if (boardRef.current) {
        const width = boardRef.current.offsetWidth;
        setBoardSize(width);
      }
    };

    // Initial size
    updateBoardSize();

    // Update on resize
    window.addEventListener('resize', updateBoardSize);
    
    // Use ResizeObserver for more accurate tracking
    const resizeObserver = new ResizeObserver(updateBoardSize);
    if (boardRef.current) {
      resizeObserver.observe(boardRef.current);
    }

    return () => {
      window.removeEventListener('resize', updateBoardSize);
      resizeObserver.disconnect();
    };
  }, []);

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
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column',
      minHeight: '100vh',
      ...(isFullScreenActive && {
        padding: '0.5rem',
        backgroundColor: '#f5f5f5',
      })
    }}>
      <NavBar />
      
      <Box sx={{
        display: 'flex',
        flexDirection: { xs: 'column', lg: 'row' },
        alignItems: { xs: 'center', lg: 'flex-start' },
        justifyContent: 'center',
        gap: 2,
        p: 1,
        ...(isFullScreenActive && {
          height: 'calc(100vh - 64px)', // Adjust for the NavBar height
          overflow: 'auto'
        })
      }}>
        {/* Player list sidebar - make narrower to allow more space for board */}
        <Grid item xs={12} lg={2} sx={{ 
          height: { xs: 'auto', lg: '100%' },
          maxHeight: { xs: '300px', lg: '100vh' },
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          p: 1,
          borderRight: '1px solid rgba(0, 0, 0, 0.12)',
          width: { xs: '100%', lg: '250px' },
          flexShrink: 0
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

        {/* Board section - make it take more space */}
        <Grid item xs={12} lg={8} sx={{ 
          display: 'flex',
          justifyContent: 'center',
          flexGrow: 1,
          p: 1
        }}>
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%'
          }}>
            <Typography variant="h4" gutterBottom sx={{ 
              textAlign: 'center', 
              fontWeight: 'bold', 
              color: '#2E7D32',
              textShadow: '1px 1px 2px rgba(0,0,0,0.1)'
            }}>
              Pi-nopoly Game Board
            </Typography>
            
            {/* Debug button for testing movement */}
            <Box sx={{ mb: 2, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <button 
                onClick={() => {
                  console.log("[DEBUG] Simulating dice roll movement");
                  emit('dice_rolled', { roll: [5, 5], playerId: 1 });
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                Test Roll Dice (5,5)
              </button>
              <button 
                onClick={() => {
                  console.log("[DEBUG] Simulating player move");
                  const currentPlayer = gameData?.players?.find(p => p.id === 1);
                  if (currentPlayer) {
                    const newPos = (currentPlayer.position + 10) % 40;
                    emit('player_moved', { playerId: 1, newPosition: newPos });
                  }
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                Move Player 1 (+10)
              </button>
            </Box>
            
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              width: '100%',
              maxWidth: boardStyle.maxWidth,
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

            <Box sx={boardStyle} ref={boardRef}>
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
                </Box>
              ))}
              
              {/* Render Player Tokens as absolute positioned elements */}
              {gameData?.players?.map((player, index) => {
                // Find other players on the same space for stacking
                const playersOnSameSpace = gameData.players.filter(p => p.position === player.position);
                
                return (
                  <AnimatedPlayerToken
                    key={`player-${player.id}`}
                    player={player}
                    boardSize={boardSize}
                    isCurrentPlayer={player.id === gameData.current_player_id}
                    playerIndex={player.id - 1}
                    otherPlayersOnSpace={playersOnSameSpace.map(p => p.id)}
                  />
                );
              })}
            </Box>
          </Box>
        </Grid>
        
        {/* Card display and actions - make narrower */}
        <Grid item xs={12} lg={2} sx={{ 
          height: { xs: 'auto', lg: '100%' },
          maxHeight: { xs: '300px', lg: '100vh' },
          overflowY: 'auto',
          p: 1,
          width: { xs: '100%', lg: '250px' },
          flexShrink: 0
        }}>
          <CardDisplay />
        </Grid>
      </Box>
      
      {/* Dice Animation Overlay */}
      {showDiceAnimation && animatedDiceRoll && (
        <DiceAnimation
          diceRoll={animatedDiceRoll}
          onComplete={() => {
            setShowDiceAnimation(false);
            setAnimatedDiceRoll(null);
          }}
        />
      )}
    </Box>
  );
}

export default BoardPage; 