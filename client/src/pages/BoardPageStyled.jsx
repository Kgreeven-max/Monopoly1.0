import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Typography, Button, Divider, Paper, Avatar, Chip } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import { useSocket } from '../contexts/SocketContext';
import PlayerToken from '../components/PlayerToken';
import { boardPositionCache } from '../utils/BoardPositionCache';
import { usePlayerPositions } from '../hooks/usePlayerPositions';
import { usePlayerMovement } from '../hooks/usePlayerMovement';
import '../styles/BoardPage.css';

// Board spaces with proper Monopoly colors
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
  { id: 39, name: 'BOARDWALK', price: 400, type: 'property', color: '#0072BC' },
];

// Token options
const tokenOptions = {
  car: { icon: '🚗', name: 'Car' },
  ship: { icon: '🚢', name: 'Ship' },
  hat: { icon: '🎩', name: 'Top Hat' },
  dog: { icon: '🐕', name: 'Dog' },
  cat: { icon: '🐈', name: 'Cat' },
  plane: { icon: '✈️', name: 'Airplane' },
  money: { icon: '💰', name: 'Money Bag' },
  crown: { icon: '👑', name: 'Crown' },
  boot: { icon: '👢', name: 'Boot' },
  robot: { icon: '🤖', name: 'Robot' }
};

// Helper to darken colors
const darkenColor = (color, percent) => {
  const num = parseInt(color.replace("#", ""), 16);
  const amt = Math.round(2.55 * percent);
  const R = (num >> 16) - amt;
  const G = (num >> 8 & 0x00FF) - amt;
  const B = (num & 0x0000FF) - amt;
  return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
    (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
    (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
};

const BoardPage = () => {
  const { socket, isConnected } = useSocket();
  const boardRef = useRef(null);
  
  // Game state
  const [gameId, setGameId] = useState(null);
  const [players, setPlayers] = useState([]);
  const [currentPlayerId, setCurrentPlayerId] = useState(null);
  const [gameStatus, setGameStatus] = useState('waiting');
  const [lastDiceRoll, setLastDiceRoll] = useState(null);
  const [isRolling, setIsRolling] = useState(false);
  const [inflation, setInflation] = useState(1.0);
  
  // UI state
  const [animationEnabled, setAnimationEnabled] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [boardSize, setBoardSize] = useState(80);
  const [isFullScreen, setIsFullScreen] = useState(false);
  
  // Player position management
  const {
    logicalPositions,
    visualPositions,
    initializePlayer,
    updateLogicalPosition,
    updateVisualPosition,
    getAnimationState,
    setAnimationState,
    isAnimating,
    batchUpdatePlayers,
    clearAllPositions
  } = usePlayerPositions();
  
  // Movement animation
  const {
    animateMovement,
    moveInstantly,
    cancelAllAnimations,
    isAnyPlayerAnimating
  } = usePlayerMovement({
    updateVisualPosition,
    updateLogicalPosition,
    getAnimationState,
    setAnimationState,
    onMovementComplete: (playerId, position) => {
      console.log(`[Movement Complete] Player ${playerId} landed on space ${position}`);
    }
  });
  
  // Initialize board position cache when board mounts
  useEffect(() => {
    const updateBoardSize = () => {
      if (boardRef.current) {
        const rect = boardRef.current.getBoundingClientRect();
        boardPositionCache.initialize(rect.width, rect.height);
      }
    };
    
    updateBoardSize();
    window.addEventListener('resize', updateBoardSize);
    
    return () => {
      window.removeEventListener('resize', updateBoardSize);
    };
  }, []);
  
  // Socket event handlers
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    const handleDiceRolled = (data) => {
      console.log('[Dice Rolled]', data);
      setLastDiceRoll(data.dice);
      setIsRolling(true);
    };
    
    const handlePlayerMoved = async (data) => {
      console.log('[Player Moved]', data);
      
      const { playerId, newPosition, diceTotal } = data;
      const currentPosition = logicalPositions.get(playerId) || 0;
      
      if (animationEnabled && !isAnimating(playerId)) {
        await animateMovement(playerId, currentPosition, newPosition, diceTotal || 1);
      } else {
        moveInstantly(playerId, newPosition);
      }
      
      setIsRolling(false);
    };
    
    const handlePlayersUpdate = (data) => {
      console.log('[Players Update]', data);
      if (data.players) {
        setPlayers(data.players);
        
        const updates = data.players.map(player => ({
          playerId: player.id,
          position: player.position || 0
        }));
        batchUpdatePlayers(updates);
      }
    };
    
    const handleGameStateUpdate = (data) => {
      console.log('[Game State Update]', data);
      if (data.gameId) setGameId(data.gameId);
      if (data.currentPlayerId) setCurrentPlayerId(data.currentPlayerId);
      if (data.status) setGameStatus(data.status);
    };
    
    socket.on('dice_rolled', handleDiceRolled);
    socket.on('player_moved', handlePlayerMoved);
    socket.on('players_updated', handlePlayersUpdate);
    socket.on('game_state_updated', handleGameStateUpdate);
    
    socket.emit('authenticate_socket', { mode: 'display' });
    
    return () => {
      socket.off('dice_rolled', handleDiceRolled);
      socket.off('player_moved', handlePlayerMoved);
      socket.off('players_updated', handlePlayersUpdate);
      socket.off('game_state_updated', handleGameStateUpdate);
    };
  }, [socket, isConnected, animationEnabled, logicalPositions, animateMovement, moveInstantly, isAnimating, batchUpdatePlayers]);
  
  // Format property name
  const formatPropertyName = (name) => {
    if (name.includes(' AVE')) {
      return name.replace(' AVE', '').trim();
    }
    if (name.includes(' RAILROAD')) {
      return name.replace(' RAILROAD', '').trim();
    }
    if (name.includes(' PLACE')) {
      return name.replace(' PLACE', '').trim();
    }
    return name;
  };
  
  // Format money
  const formatMoney = (amount) => {
    return `$${amount}`;
  };
  
  // Get position for board spaces
  const getPosition = (index) => {
    const side = Math.floor(index / 10);
    const pos = index % 10;
    
    if (side === 0) return { gridRow: 11, gridColumn: 11 - pos };
    if (side === 1) return { gridRow: 11 - pos, gridColumn: 1 };
    if (side === 2) return { gridRow: 1, gridColumn: pos + 1 };
    if (side === 3) return { gridRow: pos + 1, gridColumn: 11 };
    
    return {};
  };
  
  // Get space content based on type
  const getSpaceContent = (space) => {
    const isCorner = space.type === 'corner';
    
    const genericContent = (
      <>
        {/* Property color bar */}
        {space.type === 'property' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: space.color,
            borderBottom: '2px solid black',
            position: 'relative',
          }} />
        )}
        
        {/* Railroad header */}
        {space.type === 'railroad' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: '#000000',
            color: 'white',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.4vmin' : '1.3vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            RAILROAD
          </Box>
        )}
        
        {/* Utility header */}
        {space.type === 'utility' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: '#CCCCCC',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.4vmin' : '1.3vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            UTILITY
          </Box>
        )}
        
        {/* Chance header */}
        {space.type === 'chance' && (
          <Box sx={{ 
            width: '100%', 
            height: '30%', 
            backgroundColor: space.color,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '2.2vmin' : '2.0vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            ?
          </Box>
        )}
        
        {/* Community Chest header */}
        {space.type === 'chest' && (
          <Box sx={{ 
            width: '100%', 
            height: '30%', 
            backgroundColor: space.color,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.3vmin' : '1.2vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
            textTransform: 'uppercase',
          }}>
            COMMUNITY
          </Box>
        )}
        
        {/* Tax header */}
        {space.type === 'tax' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: '#FFE5B4',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.5vmin' : '1.3vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            TAX
          </Box>
        )}
        
        {/* Space name and price */}
        <Box sx={{ 
          px: 0.7, 
          pt: space.type !== 'corner' ? 0.7 : 0,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: isCorner ? 'center' : 'space-between',
          alignItems: 'center',
          textAlign: 'center',
        }}>
          {space.type === 'chest' && (
            <Typography 
              variant="caption" 
              sx={{ 
                fontSize: isFullScreen ? '1.3vmin' : '1.2vmin',
                fontWeight: 'bold',
                mb: 0.3,
                textTransform: 'uppercase',
              }}
            >
              CHEST
            </Typography>
          )}
          
          <Typography 
            variant="caption" 
            sx={{ 
              fontSize: isCorner 
                ? (isFullScreen ? '2.3vmin' : '2.1vmin') 
                : (isFullScreen ? '1.5vmin' : '1.3vmin'),
              fontWeight: 'bold',
              lineHeight: 1.1,
              wordBreak: 'break-word',
              width: '100%',
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
              ...(space.type === 'chest' && {display: 'none'})
            }}
          >
            {space.type === 'property' || space.type === 'railroad' ? formatPropertyName(space.name) : space.name}
          </Typography>
          
          {space.price && (
            <Typography 
              variant="caption" 
              sx={{ 
                fontSize: isFullScreen ? '1.6vmin' : '1.4vmin', 
                fontWeight: 'bold',
                mt: 'auto',
                padding: '2px 0',
                width: '100%',
                textAlign: 'center',
                borderTop: '1px solid #ddd',
                color: inflation > 1.5 ? '#d32f2f' : 
                       inflation > 1.2 ? '#f57c00' : 'inherit',
              }}
            >
              {formatMoney(space.price)}
            </Typography>
          )}
        </Box>
      </>
    );
    
    return genericContent;
  };
  
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
          <Button
            variant="outlined"
            size="small"
            onClick={() => setAnimationEnabled(!animationEnabled)}
          >
            Animations: {animationEnabled ? 'ON' : 'OFF'}
          </Button>
          <Button
            variant="outlined"
            size="small"
            onClick={() => setDebugMode(!debugMode)}
          >
            Debug: {debugMode ? 'ON' : 'OFF'}
          </Button>
          <Button
            variant="outlined"
            size="small"
            onClick={() => setIsFullScreen(!isFullScreen)}
          >
            {isFullScreen ? 'Normal' : 'Full Screen'}
          </Button>
        </Box>
      </Box>
      
      {/* Main content */}
      <Box sx={{ display: 'flex', flex: 1, p: 2, gap: 2 }}>
        {/* Board container */}
        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Box
            ref={boardRef}
            className="game-board"
            sx={{
              width: `${boardSize}vh`,
              height: `${boardSize}vh`,
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
            {BOARD_SPACES.map(space => {
              const pos = getPosition(space.id);
              const isCorner = space.id % 10 === 0;
              const playersHere = players.filter(p => logicalPositions.get(p.id) === space.id);
              
              return (
                <Box 
                  key={space.id}
                  data-space-id={space.id}
                  sx={{
                    ...pos,
                    backgroundColor: 'white',
                    border: '1px solid #333',
                    borderRadius: '2px',
                    ...(isCorner && {
                      backgroundColor: space.color,
                      position: 'relative',
                      borderRadius: '4px',
                    }),
                    display: 'flex',
                    flexDirection: 'column',
                    padding: 0,
                    position: 'relative',
                    overflow: 'hidden', 
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    ...(isCorner && isFullScreen && {
                      transform: 'scale(1.05)',
                      zIndex: 5
                    }),
                    transform: isFullScreen ? 'scale(1.04)' : 'scale(1.02)',
                    zIndex: 1
                  }}
                >
                  {getSpaceContent(space)}
                  
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
            })}
            
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
              {lastDiceRoll && (
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  {lastDiceRoll.map((die, index) => (
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
              
              {/* Test buttons */}
              {debugMode && (
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => {
                      const testPlayer = players[0];
                      if (testPlayer) {
                        const currentPos = logicalPositions.get(testPlayer.id) || 0;
                        const newPos = (currentPos + 6) % 40;
                        animateMovement(testPlayer.id, currentPos, newPos, 6);
                      }
                    }}
                    disabled={isAnyPlayerAnimating()}
                  >
                    Test Move (6 spaces)
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => {
                      setLastDiceRoll([3, 4]);
                      setTimeout(() => setLastDiceRoll(null), 3000);
                    }}
                  >
                    Test Dice
                  </Button>
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
              {players.map(player => {
                const visualPos = visualPositions.get(player.id);
                const isCurrentPlayer = player.id === currentPlayerId;
                const isPlayerAnimating = isAnimating(player.id);
                
                return visualPos ? (
                  <Box 
                    key={player.id}
                    data-player-id={player.id}
                    className={`player-token ${isPlayerAnimating ? 'animating' : ''}`}
                    sx={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      transform: `translate(${visualPos.x}px, ${visualPos.y}px)`,
                      transition: 'none',
                      willChange: isPlayerAnimating ? 'transform' : 'auto',
                      width: isFullScreen ? '3.2vmin' : '2.8vmin',
                      height: isFullScreen ? '3.2vmin' : '2.8vmin',
                      borderRadius: '50%',
                      background: `radial-gradient(circle at 30% 30%, ${player.color || '#cccccc'}, ${darkenColor(player.color || '#cccccc', 30)})`,
                      border: isCurrentPlayer ? '2px solid gold' : '1px solid rgba(0,0,0,0.5)',
                      boxShadow: isCurrentPlayer 
                        ? '0 0 8px gold, 0 2px 5px rgba(0,0,0,0.4), inset 0 -2px 5px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5)' 
                        : '0 2px 5px rgba(0,0,0,0.4), inset 0 -2px 5px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5)',
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      fontSize: isFullScreen ? '1.8vmin' : '1.6vmin',
                      zIndex: isCurrentPlayer ? 20 : 10,
                      '&:hover': {
                        transform: `${visualPos ? `translate(${visualPos.x}px, ${visualPos.y}px)` : ''} scale(1.15)`,
                        boxShadow: isCurrentPlayer 
                          ? '0 0 12px gold, 0 8px 16px rgba(0,0,0,0.4)'
                          : '0 8px 16px rgba(0,0,0,0.4)',
                        zIndex: 30
                      },
                      pointerEvents: 'auto',
                      cursor: 'pointer'
                    }}
                  >
                    <Box sx={{
                      fontSize: isFullScreen ? '2.2vmin' : '2vmin',
                      filter: 'drop-shadow(0 1px 1px rgba(0,0,0,0.5))',
                      transform: 'translateZ(5px)',
                    }}>
                      {(tokenOptions[player.token] && tokenOptions[player.token].icon) || player.id || '?'}
                    </Box>
                  </Box>
                ) : null;
              })}
            </Box>
          </Box>
        </Box>
        
        {/* Sidebar */}
        <Box sx={{ width: 300 }}>
          {/* Players list */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Players
            </Typography>
            {players.map(player => {
              const position = logicalPositions.get(player.id) || 0;
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
                    backgroundColor: player.id === currentPlayerId ? alpha(player.color || '#ccc', 0.2) : 'background.paper',
                    borderRadius: 1,
                    border: player.id === currentPlayerId ? '2px solid gold' : 'none'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar
                      sx={{
                        width: 24,
                        height: 24,
                        backgroundColor: player.color || '#999',
                        fontSize: '0.8rem'
                      }}
                    >
                      {(tokenOptions[player.token] && tokenOptions[player.token].icon) || player.name?.[0] || 'P'}
                    </Avatar>
                    <Typography variant="body2">
                      {player.name || `Player ${player.id}`}
                      {player.is_bot && ' 🤖'}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {space.name}
                  </Typography>
                </Box>
              );
            })}
          </Paper>
          
          {/* Debug info */}
          {debugMode && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Debug Info
              </Typography>
              <Typography variant="body2">
                Board initialized: {boardPositionCache.isInitialized() ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2">
                Players tracked: {logicalPositions.size}
              </Typography>
              <Typography variant="body2">
                Animations active: {isAnyPlayerAnimating() ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2">
                Rolling: {isRolling ? 'Yes' : 'No'}
              </Typography>
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default BoardPage;