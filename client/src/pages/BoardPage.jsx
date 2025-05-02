import React, { useState, useEffect } from 'react';
import { Box } from '@mui/material';

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
  const boardRef = React.useRef(null);

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      boardRef.current.requestFullscreen().catch(err => {
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

  return (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh', 
      width: '100vw',
      p: 2,
      overflow: 'hidden'
    }}>
      <Box 
        ref={boardRef}
        onClick={toggleFullScreen}
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(11, 1fr)',
          gridTemplateRows: 'repeat(11, 1fr)',
          width: '90vmin',
          height: '90vmin',
          maxWidth: '900px',
          maxHeight: '900px',
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
                justifyContent: 'center',
                alignItems: 'center',
                fontSize: isCorner ? '1.2vmin' : '1vmin',
                fontWeight: 'bold'
              }}
            >
              {i}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}

export default BoardPage; 