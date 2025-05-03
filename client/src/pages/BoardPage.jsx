import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Divider, Paper, Avatar, Chip } from '@mui/material';

function BoardPage() {
  // Define board spaces with property info
  const boardSpaces = [
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

  // Function to get position for each space
  const getPosition = (index) => {
    const side = Math.floor(index / 10); // 0=bottom, 1=left, 2=top, 3=right
    const pos = index % 10;
    
    // Different positioning based on which side of the board
    if (side === 0) return { gridRow: 11, gridColumn: 11 - pos }; // bottom row
    if (side === 1) return { gridRow: 11 - pos, gridColumn: 1 }; // left column
    if (side === 2) return { gridRow: 1, gridColumn: pos + 1 }; // top row
    if (side === 3) return { gridRow: pos + 1, gridColumn: 11 }; // right column
    
    return {}; // fallback
  };

  // Space content based on type
  const getSpaceContent = (space) => {
    const isCorner = space.type === 'corner';
    
    // Format property name to fit better
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
    
    // Generic content for all spaces
    const genericContent = (
      <>
        {/* Space header/color bar */}
        {space.type === 'property' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: space.color,
            borderBottom: '2px solid black',
          }} />
        )}
        
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
        
        {/* Space name */}
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
              ...(space.type === 'chest' && {display: 'none'}) // Hide duplicate text for chest spaces
            }}
          >
            {space.type === 'property' || space.type === 'railroad' ? formatPropertyName(space.name) : space.name}
          </Typography>
          
          {/* Price (if applicable) */}
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
              }}
            >
              ${space.price}
            </Typography>
          )}
        </Box>
      </>
    );
    
    // Special corner spaces
    if (isCorner) {
      switch(space.id) {
        case 0: // GO
          return (
            <Box sx={{ transform: 'rotate(45deg)', textAlign: 'center', padding: '5px' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.6vmin' : '2.4vmin', fontWeight: 'bold', color: 'red' }}>
                GO
              </Typography>
              <Typography sx={{ fontSize: isFullScreen ? '1.7vmin' : '1.5vmin', fontWeight: 'bold' }}>
                COLLECT $200
              </Typography>
              <Box sx={{ 
                position: 'absolute', 
                bottom: '8px', 
                right: '8px', 
                transform: 'rotate(-45deg)',
                fontSize: isFullScreen ? '1.5vmin' : '1.3vmin',
                fontWeight: 'bold',
                backgroundColor: 'rgba(255,255,255,0.7)',
                padding: '2px 5px',
                borderRadius: '2px',
              }}>
                $200
              </Box>
            </Box>
          );
        case 10: // JAIL
          return (
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.8vmin' : '2.6vmin', fontWeight: 'bold' }}>
                JAIL
              </Typography>
            </Box>
          );
        case 20: // FREE PARKING
          return (
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                FREE
              </Typography>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                PARKING
              </Typography>
            </Box>
          );
        case 30: // GO TO JAIL
          return (
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                GO TO
              </Typography>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                JAIL
              </Typography>
            </Box>
          );
        default:
          return genericContent;
      }
    }
    
    return genericContent;
  };

  // Function to handle full screen
  const [isFullScreen, setIsFullScreen] = useState(false);
  const containerRef = React.useRef(null);

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullScreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullScreenChange);
  }, []);

  // Mock player data (replace with actual data later)
  const players = [
    { id: 1, name: 'Player 1', cash: 1500, position: 0, color: '#E53935' },
    { id: 2, name: 'Player 2', cash: 1200, position: 5, color: '#1E88E5' },
    { id: 3, name: 'Player 3', cash: 950, position: 12, color: '#43A047' },
    { id: 4, name: 'Player 4', cash: 800, position: 24, color: '#FDD835' },
  ];
  
  const currentPlayer = players[0]; // First player is current

  return (
    <Box 
      ref={containerRef}
      sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', md: 'row' },
        height: '100vh', 
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#C5E8D2', // Add Monopoly green background
      }}
    >
      {/* Board Container (left/top) */}
      <Box sx={{ 
        flex: { xs: '1', md: '3' }, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        p: isFullScreen ? 0 : 2,
        overflow: 'hidden',
        backgroundColor: '#C5E8D2', // Match Monopoly green
      }}>
        <Box 
          onClick={toggleFullScreen}
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(11, 1fr)',
            gridTemplateRows: 'repeat(11, 1fr)',
            width: isFullScreen ? '99vmin' : '92vmin',
            height: isFullScreen ? '99vmin' : '92vmin',
            maxWidth: isFullScreen ? 'none' : '900px',
            maxHeight: isFullScreen ? 'none' : '900px',
            gap: 0.7, // Increased gap between spaces
            border: '4px solid #333',
            backgroundColor: '#C5E8D2', // Classic Monopoly green
            padding: 0.7, // Increased padding
            boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
            borderRadius: 3,
            position: 'relative',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
        >
          {/* Center area */}
          <Box sx={{ 
            gridRow: '2 / 11', 
            gridColumn: '2 / 11',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            <Box sx={{ 
              transform: 'rotate(-45deg)',
              fontSize: '6vmin',
              fontWeight: 'bold',
              color: '#CC0000', // Monopoly red
              textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
              letterSpacing: '-0.05em',
              fontFamily: 'Arial, sans-serif'
            }}>
              MONOPOLY
            </Box>
          </Box>
          
          {/* Board spaces */}
          {boardSpaces.map(space => {
            const pos = getPosition(space.id);
            const isCorner = space.id % 10 === 0;
            
            // Players on this space
            const playersHere = players.filter(p => p.position === space.id);
            
            return (
              <Box 
                key={space.id}
                sx={{
                  ...pos,
                  backgroundColor: 'white',
                  border: '1px solid #333',
                  borderRadius: '2px',
                  ...(isCorner && {
                    gridRow: pos.gridRow,
                    gridColumn: pos.gridColumn,
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
                  // Make the corner spaces a bit larger
                  ...(isCorner && isFullScreen && {
                    transform: 'scale(1.05)',
                    zIndex: 5
                  }),
                  // Make all spaces slightly larger
                  transform: isFullScreen ? 'scale(1.04)' : 'scale(1.02)', // Increased scale for better visibility
                  zIndex: 1
                }}
              >
                {getSpaceContent(space)}
                
                {/* Player tokens */}
                {playersHere.length > 0 && (
                  <Box sx={{ 
                    position: 'absolute',
                    bottom: '3px',
                    left: 0,
                    right: 0,
                    display: 'flex', 
                    flexWrap: 'wrap',
                    gap: '3px',
                    justifyContent: 'center',
                    zIndex: 10
                  }}>
                    {playersHere.map(player => (
                      <Box 
                        key={player.id}
                        sx={{
                          width: isFullScreen ? '2.6vmin' : '2.3vmin',
                          height: isFullScreen ? '2.6vmin' : '2.3vmin',
                          borderRadius: '50%',
                          backgroundColor: player.color,
                          border: player.id === currentPlayer.id ? '2px solid gold' : '1px solid #333',
                          boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          color: '#fff',
                          fontSize: isFullScreen ? '1.6vmin' : '1.4vmin',
                          fontWeight: 'bold'
                        }}
                      >
                        {player.id}
                      </Box>
                    ))}
                  </Box>
                )}
              </Box>
            );
          })}
        </Box>
      </Box>
      
      {/* Player Dashboard (right/bottom) */}
      <Box 
        sx={{ 
          flex: { xs: 'auto', md: '0 0 320px' },
          height: { xs: 'auto', md: '100%' },
          borderLeft: { xs: 'none', md: '2px solid #ccc' },
          borderTop: { xs: '2px solid #ccc', md: 'none' },
          overflow: 'auto',
          backgroundColor: '#f9f9f9',
          boxShadow: '-2px 0 10px rgba(0,0,0,0.1)'
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2, textAlign: 'center', color: '#333' }}>
            Game Dashboard
          </Typography>
          
          {/* Current player */}
          <Paper elevation={3} sx={{ p: 2, mb: 3, backgroundColor: alpha(currentPlayer.color, 0.15), borderRadius: '10px' }}>
            <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', borderBottom: '1px solid rgba(0,0,0,0.1)', pb: 1 }}>
              Current Turn
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'center' }}>
              <Avatar sx={{ bgcolor: currentPlayer.color, mr: 2, width: 40, height: 40, boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}>
                {currentPlayer.name.charAt(0)}
              </Avatar>
              <Typography variant="body1" fontWeight="bold" fontSize="1.1rem">
                {currentPlayer.name}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, px: 1 }}>
              <Typography variant="body2" fontWeight="medium">Cash:</Typography>
              <Typography variant="body2" fontWeight="bold" fontSize="1rem">${currentPlayer.cash}</Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', px: 1 }}>
              <Typography variant="body2" fontWeight="medium">Position:</Typography>
              <Typography variant="body2" fontWeight="bold" fontSize="1rem">Space {currentPlayer.position}</Typography>
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="contained" 
                fullWidth 
                sx={{ 
                  mb: 1, 
                  bgcolor: '#4CAF50', 
                  '&:hover': { bgcolor: '#388E3C' },
                  fontWeight: 'bold',
                  py: 1,
                  boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
                }}
              >
                Roll Dice
              </Button>
              <Button 
                variant="outlined" 
                fullWidth
                sx={{
                  borderColor: '#4CAF50',
                  color: '#4CAF50',
                  '&:hover': { borderColor: '#388E3C', bgcolor: 'rgba(76, 175, 80, 0.05)' },
                  fontWeight: 'medium'
                }}
              >
                End Turn
              </Button>
            </Box>
          </Paper>
          
          {/* All players */}
          <Paper elevation={2} sx={{ mb: 3, borderRadius: '10px', overflow: 'hidden' }}>
            <Typography variant="h6" sx={{ p: 1.5, fontWeight: 'bold', bgcolor: '#f5f5f5', borderBottom: '1px solid #eee' }}>
              Players
            </Typography>
            <Box>
              {players.map(player => (
                <Box 
                  key={player.id}
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    p: 1.5,
                    borderBottom: '1px solid #eee',
                    bgcolor: player.id === currentPlayer.id ? alpha(player.color, 0.1) : 'transparent',
                    transition: 'background-color 0.3s ease'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box 
                      sx={{ 
                        width: 16, 
                        height: 16, 
                        borderRadius: '50%', 
                        bgcolor: player.color,
                        mr: 1.5,
                        border: '1px solid rgba(0,0,0,0.2)',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                      }} 
                    />
                    <Typography variant="body2" fontWeight={player.id === currentPlayer.id ? 'bold' : 'medium'}>
                      {player.name}
                    </Typography>
                  </Box>
                  <Typography variant="body2" fontWeight="bold" fontSize="0.95rem">${player.cash}</Typography>
                </Box>
              ))}
            </Box>
          </Paper>
          
          {/* Game controls */}
          <Paper elevation={2} sx={{ borderRadius: '10px', overflow: 'hidden' }}>
            <Typography variant="h6" sx={{ p: 1.5, fontWeight: 'bold', bgcolor: '#f5f5f5', borderBottom: '1px solid #eee' }}>
              Game Controls
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, p: 1.5 }}>
              <Button 
                variant="outlined" 
                size="medium" 
                onClick={toggleFullScreen}
                startIcon={isFullScreen ? <span>⤧</span> : <span>⤢</span>}
                sx={{ 
                  fontWeight: 'medium',
                  borderColor: '#2196F3',
                  color: '#2196F3',
                  '&:hover': { borderColor: '#1976D2', bgcolor: 'rgba(33, 150, 243, 0.05)' }
                }}
              >
                {isFullScreen ? 'Exit Fullscreen' : 'Fullscreen'}
              </Button>
              <Button 
                variant="outlined" 
                size="medium" 
                color="error"
                sx={{ fontWeight: 'medium' }}
              >
                Leave Game
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}

// Helper function to create alpha colors
function alpha(color, value) {
  // Simple alpha function for web colors
  return color + Math.round(value * 255).toString(16).padStart(2, '0');
}

export default BoardPage; 