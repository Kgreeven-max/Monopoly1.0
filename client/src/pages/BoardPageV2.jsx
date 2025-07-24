import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, Paper, Avatar, Chip } from '@mui/material';
import { useSocket } from '../contexts/SocketContext';
import { boardPositionCache } from '../utils/BoardPositionCache';
import { usePlayerMovement } from '../hooks/usePlayerMovement';
import '../styles/BoardPage.css';

// Board spaces configuration
const BOARD_SPACES = [
  { id: 0, name: 'GO', type: 'corner', color: '#FFECD6' },
  { id: 1, name: 'MEDITERRANEAN AVE', price: 60, type: 'property', color: '#955436' },
  { id: 2, name: 'COMMUNITY CHEST', type: 'chest', color: '#CBDFF8' },
  { id: 3, name: 'BALTIC AVE', price: 60, type: 'property', color: '#955436' },
  { id: 4, name: 'INCOME TAX', price: 200, type: 'tax', color: '#FFFFFF' },
  { id: 5, name: 'READING RAILROAD', price: 200, type: 'railroad', color: '#000000' },
  { id: 6, name: 'ORIENTAL AVE', price: 100, type: 'property', color: '#AACCF1' },
  { id: 7, name: 'CHANCE', type: 'chance', color: '#FFC663' },
  { id: 8, name: 'VERMONT AVE', price: 100, type: 'property', color: '#AACCF1' },
  { id: 9, name: 'CONNECTICUT AVE', price: 120, type: 'property', color: '#AACCF1' },
  { id: 10, name: 'JAIL', type: 'corner', color: '#FFECD6' },
  { id: 11, name: 'ST. CHARLES PLACE', price: 140, type: 'property', color: '#D93A96' },
  { id: 12, name: 'ELECTRIC COMPANY', price: 150, type: 'utility', color: '#FFFFFF' },
  { id: 13, name: 'STATES AVE', price: 140, type: 'property', color: '#D93A96' },
  { id: 14, name: 'VIRGINIA AVE', price: 160, type: 'property', color: '#D93A96' },
  { id: 15, name: 'PENNSYLVANIA RAILROAD', price: 200, type: 'railroad', color: '#000000' },
  { id: 16, name: 'ST. JAMES PLACE', price: 180, type: 'property', color: '#F7941D' },
  { id: 17, name: 'COMMUNITY CHEST', type: 'chest', color: '#CBDFF8' },
  { id: 18, name: 'TENNESSEE AVE', price: 180, type: 'property', color: '#F7941D' },
  { id: 19, name: 'NEW YORK AVE', price: 200, type: 'property', color: '#F7941D' },
  { id: 20, name: 'FREE PARKING', type: 'corner', color: '#FFECD6' },
  { id: 21, name: 'KENTUCKY AVE', price: 220, type: 'property', color: '#ED1B24' },
  { id: 22, name: 'CHANCE', type: 'chance', color: '#FFC663' },
  { id: 23, name: 'INDIANA AVE', price: 220, type: 'property', color: '#ED1B24' },
  { id: 24, name: 'ILLINOIS AVE', price: 240, type: 'property', color: '#ED1B24' },
  { id: 25, name: 'B & O RAILROAD', price: 200, type: 'railroad', color: '#000000' },
  { id: 26, name: 'ATLANTIC AVE', price: 260, type: 'property', color: '#FEF200' },
  { id: 27, name: 'VENTNOR AVE', price: 260, type: 'property', color: '#FEF200' },
  { id: 28, name: 'WATER WORKS', price: 150, type: 'utility', color: '#FFFFFF' },
  { id: 29, name: 'MARVIN GARDENS', price: 280, type: 'property', color: '#FEF200' },
  { id: 30, name: 'GO TO JAIL', type: 'corner', color: '#FFECD6' },
  { id: 31, name: 'PACIFIC AVE', price: 300, type: 'property', color: '#0D9B4D' },
  { id: 32, name: 'NORTH CAROLINA AVE', price: 300, type: 'property', color: '#0D9B4D' },
  { id: 33, name: 'COMMUNITY CHEST', type: 'chest', color: '#CBDFF8' },
  { id: 34, name: 'PENNSYLVANIA AVE', price: 320, type: 'property', color: '#0D9B4D' },
  { id: 35, name: 'SHORT LINE RAILROAD', price: 200, type: 'railroad', color: '#000000' },
  { id: 36, name: 'CHANCE', type: 'chance', color: '#FFC663' },
  { id: 37, name: 'PARK PLACE', price: 350, type: 'property', color: '#0072BC' },
  { id: 38, name: 'LUXURY TAX', price: 100, type: 'tax', color: '#FFFFFF' },
  { id: 39, name: 'BOARDWALK', price: 400, type: 'property', color: '#0072BC' }
];

const BoardPageV2 = () => {
  const { socket, isConnected } = useSocket();
  const boardRef = useRef(null);
  
  // Single source of truth - THE game state
  const [gameState, setGameState] = useState(null);
  
  // Derived state for animations only
  const [animatingPlayers, setAnimatingPlayers] = useState(new Set());
  const [playerPositions, setPlayerPositions] = useState(new Map());
  
  // Initialize board position cache
  useEffect(() => {
    const updateBoardSize = () => {
      if (boardRef.current) {
        const rect = boardRef.current.getBoundingClientRect();
        boardPositionCache.initialize(rect.width, rect.height);
      }
    };
    
    updateBoardSize();
    window.addEventListener('resize', updateBoardSize);
    return () => window.removeEventListener('resize', updateBoardSize);
  }, []);
  
  // Socket connection and event handlers
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    // Main game state handler - single source of truth
    const handleGameState = (state) => {
      console.log('[BoardV2] Received game state:', state);
      setGameState(state);
      
      // Update player positions for rendering
      if (state && state.players) {
        const newPositions = new Map();
        state.players.forEach(player => {
          newPositions.set(player.id, player.position);
        });
        setPlayerPositions(newPositions);
      }
    };
    
    // Animation events - separate from state
    const handleAnimateMovement = ({ playerId, from, to, path }) => {
      console.log('[BoardV2] Animate movement:', { playerId, from, to, path });
      
      // Mark player as animating
      setAnimatingPlayers(prev => new Set([...prev, playerId]));
      
      // Animate through each space
      let currentIndex = 0;
      const animateStep = () => {
        if (currentIndex < path.length) {
          setPlayerPositions(prev => {
            const newMap = new Map(prev);
            newMap.set(playerId, path[currentIndex]);
            return newMap;
          });
          currentIndex++;
          setTimeout(animateStep, 300);
        } else {
          // Animation complete
          setAnimatingPlayers(prev => {
            const newSet = new Set(prev);
            newSet.delete(playerId);
            return newSet;
          });
        }
      };
      animateStep();
    };
    
    // Authentication response
    const handleAuthSuccess = (data) => {
      console.log('[BoardV2] Authentication successful:', data);
      if (data.gameState) {
        handleGameState(data.gameState);
      }
    };
    
    const handleAuthError = (error) => {
      console.error('[BoardV2] Authentication error:', error);
    };
    
    // Register event listeners
    socket.on('game_state', handleGameState);
    socket.on('animate_movement', handleAnimateMovement);
    socket.on('auth_success', handleAuthSuccess);
    socket.on('auth_error', handleAuthError);
    
    // Authenticate as display
    console.log('[BoardV2] Authenticating as display...');
    socket.emit('authenticate', { mode: 'display' });
    
    // Cleanup
    return () => {
      socket.off('game_state', handleGameState);
      socket.off('animate_movement', handleAnimateMovement);
      socket.off('auth_success', handleAuthSuccess);
      socket.off('auth_error', handleAuthError);
    };
  }, [socket, isConnected]);
  
  // Helper functions
  const getSpacePosition = (spaceId) => {
    if (spaceId <= 10) {
      return { gridRow: 11, gridColumn: 11 - spaceId };
    } else if (spaceId <= 19) {
      return { gridRow: 11 - (spaceId - 10), gridColumn: 1 };
    } else if (spaceId <= 30) {
      return { gridRow: 1, gridColumn: spaceId - 19 };
    } else {
      return { gridRow: spaceId - 29, gridColumn: 11 };
    }
  };
  
  const renderSpace = (space) => {
    const isCorner = space.id % 10 === 0;
    const playersHere = gameState?.players?.filter(p => 
      playerPositions.get(p.id) === space.id
    ) || [];
    
    return (
      <Box
        key={space.id}
        data-space-id={space.id}
        sx={{
          ...getSpacePosition(space.id),
          backgroundColor: 'white',
          border: '1px solid #333',
          borderRadius: isCorner ? '4px' : '2px',
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}
      >
        {/* Property color bar */}
        {space.type === 'property' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: space.color,
            borderBottom: '2px solid black',
          }} />
        )}
        
        {/* Space name */}
        <Box sx={{ 
          px: 0.7, 
          pt: space.type === 'property' ? 0.7 : 0,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
        }}>
          <Typography 
            variant="caption" 
            sx={{ 
              fontSize: isCorner ? '2.1vmin' : '1.3vmin',
              fontWeight: 'bold',
              lineHeight: 1.1,
              textTransform: 'uppercase',
            }}
          >
            {space.name}
          </Typography>
          
          {space.price && (
            <Typography 
              variant="caption" 
              sx={{ 
                fontSize: '1.4vmin', 
                fontWeight: 'bold',
                mt: 'auto',
              }}
            >
              ${space.price}
            </Typography>
          )}
        </Box>
        
        {/* Player count indicator */}
        {playersHere.length > 1 && (
          <Chip
            label={playersHere.length}
            size="small"
            sx={{
              position: 'absolute',
              bottom: 2,
              right: 2,
              minWidth: 20,
              height: 20,
              fontSize: '0.7rem'
            }}
          />
        )}
      </Box>
    );
  };
  
  const renderPlayer = (player) => {
    const position = playerPositions.get(player.id);
    if (position === undefined || !boardRef.current) return null;
    
    const boardRect = boardRef.current.getBoundingClientRect();
    const pos = boardPositionCache.getPlayerPosition(
      position, 
      gameState.players.filter(p => playerPositions.get(p.id) === position).indexOf(player),
      gameState.players.filter(p => playerPositions.get(p.id) === position).length
    );
    
    if (!pos) return null;
    
    const isAnimating = animatingPlayers.has(player.id);
    const isCurrentPlayer = player.id === gameState.currentPlayer?.id;
    
    return (
      <Box
        key={player.id}
        className={`player-token ${isAnimating ? 'bouncing' : ''}`}
        sx={{
          position: 'absolute',
          left: 0,
          top: 0,
          transform: `translate(${pos.x}px, ${pos.y}px)`,
          transition: isAnimating ? 'none' : 'transform 0.3s ease',
          width: '2.8vmin',
          height: '2.8vmin',
          borderRadius: '50%',
          backgroundColor: player.color,
          border: isCurrentPlayer ? '2px solid gold' : '1px solid rgba(0,0,0,0.5)',
          boxShadow: isCurrentPlayer 
            ? '0 0 8px gold, 0 2px 5px rgba(0,0,0,0.4)' 
            : '0 2px 5px rgba(0,0,0,0.4)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          fontSize: '1.6vmin',
          zIndex: isCurrentPlayer ? 20 : 10,
          pointerEvents: 'none',
        }}
      >
        <span style={{ fontSize: '1.8vmin' }}>{player.token || player.name?.[0] || '?'}</span>
      </Box>
    );
  };
  
  // Loading state
  if (!gameState) {
    return (
      <Box className="board-page" sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Typography variant="h4">Waiting for game...</Typography>
      </Box>
    );
  }
  
  return (
    <Box className="board-page">
      {/* Header */}
      <Box className="board-header">
        <Typography variant="h4">Pi-nopoly Board</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            size="small"
          />
          <Typography variant="body2">
            Game: {gameState.gameId.slice(0, 8)}
          </Typography>
        </Box>
      </Box>
      
      {/* Main content */}
      <Box sx={{ display: 'flex', flex: 1, p: 2, gap: 2 }}>
        {/* Board */}
        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Box
            ref={boardRef}
            className="game-board"
            sx={{
              width: '80vh',
              height: '80vh',
              maxWidth: '90vw',
              maxHeight: '80vh',
              display: 'grid',
              gridTemplateColumns: 'repeat(11, 1fr)',
              gridTemplateRows: 'repeat(11, 1fr)',
              gap: 0,
              position: 'relative',
              backgroundColor: '#C8E6C9',
              border: '3px solid #000',
              boxShadow: '0 4px 8px rgba(0,0,0,0.2)'
            }}
          >
            {/* Render board spaces */}
            {BOARD_SPACES.map(space => renderSpace(space))}
            
            {/* Center area */}
            <Box
              sx={{
                gridColumn: '2 / 11',
                gridRow: '2 / 11',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: '#E8F5E9',
                border: '2px solid #4CAF50',
                borderRadius: '8px',
                p: 2
              }}
            >
              <Typography variant="h3" sx={{ color: '#2E7D32', mb: 2 }}>
                PI-NOPOLY
              </Typography>
              
              {/* Dice display */}
              {gameState.lastRoll && (
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  {gameState.lastRoll.dice.map((die, index) => (
                    <Paper
                      key={index}
                      elevation={3}
                      sx={{
                        width: 60,
                        height: 60,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '2rem',
                        fontWeight: 'bold'
                      }}
                    >
                      {die}
                    </Paper>
                  ))}
                </Box>
              )}
            </Box>
            
            {/* Player tokens layer */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: 'none'
              }}
            >
              {gameState.players.map(player => renderPlayer(player))}
            </Box>
          </Box>
        </Box>
        
        {/* Sidebar */}
        <Box sx={{ width: 300 }}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Players
            </Typography>
            {gameState.players.map(player => {
              const position = playerPositions.get(player.id) || 0;
              const space = BOARD_SPACES[position];
              
              return (
                <Box
                  key={player.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 1,
                    mb: 1,
                    backgroundColor: player.id === gameState.currentPlayer?.id ? 'action.selected' : 'background.paper',
                    borderRadius: 1,
                    border: player.id === gameState.currentPlayer?.id ? '2px solid gold' : 'none'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar
                      sx={{
                        width: 24,
                        height: 24,
                        backgroundColor: player.color,
                        fontSize: '0.8rem'
                      }}
                    >
                      {player.token}
                    </Avatar>
                    <Typography variant="body2">
                      {player.name}
                      {player.isBot && ' 🤖'}
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="caption" color="text.secondary">
                      {space.name}
                    </Typography>
                    <Typography variant="caption" display="block">
                      ${player.money}
                    </Typography>
                  </Box>
                </Box>
              );
            })}
          </Paper>
          
          {/* Game info */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Game Info
            </Typography>
            <Typography variant="body2">
              Status: {gameState.status}
            </Typography>
            <Typography variant="body2">
              Round: {gameState.round}
            </Typography>
            {gameState.currentPlayer && (
              <Typography variant="body2">
                Current: {gameState.players.find(p => p.id === gameState.currentPlayer.id)?.name}
              </Typography>
            )}
            {gameState.currentPlayer?.expectedAction && (
              <Typography variant="body2" color="primary">
                Action: {gameState.currentPlayer.expectedAction}
              </Typography>
            )}
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default BoardPageV2;