import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Divider, Paper, Avatar, Chip } from '@mui/material';

function BoardPage() {
  // Define board spaces - 40 spaces total (10 per side)
  const spaces = Array.from({ length: 40 }, (_, i) => i);
  
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
            width: isFullScreen ? '99vmin' : '85vmin',
            height: isFullScreen ? '99vmin' : '85vmin',
            maxWidth: isFullScreen ? 'none' : '800px',
            maxHeight: isFullScreen ? 'none' : '800px',
            gap: 1,
            border: '3px solid black',
            backgroundColor: '#C5E8D2', // Classic Monopoly green
            padding: 1,
            boxShadow: '0 10px 20px rgba(0,0,0,0.3)',
            borderRadius: 2,
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
              fontSize: '5vmin',
              fontWeight: 'bold',
              color: '#CC0000', // Monopoly red
              textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
            }}>
              MONOPOLY
            </Box>
          </Box>
          
          {/* Board spaces */}
          {spaces.map(i => {
            const pos = getPosition(i);
            const isCorner = i % 10 === 0;
            
            // Players on this space
            const playersHere = players.filter(p => p.position === i);
            
            return (
              <Box 
                key={i}
                sx={{
                  ...pos,
                  backgroundColor: 'white',
                  border: '1px solid black',
                  ...(isCorner && {
                    gridRow: pos.gridRow,
                    gridColumn: pos.gridColumn,
                    backgroundColor: '#FFECD6', // Cream color for corners
                    position: 'relative'
                  }),
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  padding: '2px',
                  fontSize: isCorner ? '1.2vmin' : '1vmin',
                  fontWeight: 'bold',
                  position: 'relative'
                }}
              >
                <Typography variant="caption" sx={{ fontSize: 'inherit' }}>{i}</Typography>
                
                {/* Player tokens */}
                {playersHere.length > 0 && (
                  <Box sx={{ 
                    display: 'flex', 
                    flexWrap: 'wrap',
                    gap: '2px',
                    justifyContent: 'center'
                  }}>
                    {playersHere.map(player => (
                      <Box 
                        key={player.id}
                        sx={{
                          width: '1.5vmin',
                          height: '1.5vmin',
                          borderRadius: '50%',
                          backgroundColor: player.color,
                          border: player.id === currentPlayer.id ? '2px solid gold' : '1px solid #333'
                        }}
                      />
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
          flex: { xs: 'auto', md: '0 0 300px' },
          height: { xs: 'auto', md: '100%' },
          borderLeft: { xs: 'none', md: '1px solid #ccc' },
          borderTop: { xs: '1px solid #ccc', md: 'none' },
          overflow: 'auto',
          backgroundColor: '#f8f8f8'
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
            Game Dashboard
          </Typography>
          
          {/* Current player */}
          <Paper elevation={2} sx={{ p: 2, mb: 3, backgroundColor: alpha(currentPlayer.color, 0.1) }}>
            <Typography variant="h6" gutterBottom>
              Current Turn
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar sx={{ bgcolor: currentPlayer.color, mr: 2 }}>
                {currentPlayer.name.charAt(0)}
              </Avatar>
              <Typography variant="body1" fontWeight="bold">
                {currentPlayer.name}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Cash:</Typography>
              <Typography variant="body2" fontWeight="bold">${currentPlayer.cash}</Typography>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2">Position:</Typography>
              <Typography variant="body2" fontWeight="bold">Space {currentPlayer.position}</Typography>
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Button variant="contained" fullWidth sx={{ mb: 1 }}>
                Roll Dice
              </Button>
              <Button variant="outlined" fullWidth>
                End Turn
              </Button>
            </Box>
          </Paper>
          
          {/* All players */}
          <Typography variant="h6" gutterBottom>
            Players
          </Typography>
          <Box sx={{ mb: 3 }}>
            {players.map(player => (
              <Box 
                key={player.id}
                sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  p: 1,
                  borderBottom: '1px solid #eee',
                  bgcolor: player.id === currentPlayer.id ? alpha(player.color, 0.1) : 'transparent'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box 
                    sx={{ 
                      width: 12, 
                      height: 12, 
                      borderRadius: '50%', 
                      bgcolor: player.color,
                      mr: 1 
                    }} 
                  />
                  <Typography variant="body2">{player.name}</Typography>
                </Box>
                <Typography variant="body2" fontWeight="bold">${player.cash}</Typography>
              </Box>
            ))}
          </Box>
          
          {/* Game controls */}
          <Typography variant="h6" gutterBottom>
            Game Controls
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button variant="outlined" size="small" onClick={toggleFullScreen}>
              {isFullScreen ? 'Exit Fullscreen' : 'Fullscreen'}
            </Button>
            <Button variant="outlined" size="small" color="error">
              Leave Game
            </Button>
          </Box>
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