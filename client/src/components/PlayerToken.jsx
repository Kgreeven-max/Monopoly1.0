import React, { memo } from 'react';
import { Box } from '@mui/material';

/**
 * Optimized PlayerToken component using CSS transforms for positioning
 */
const PlayerToken = memo(({ 
  player, 
  position,
  isAnimating = false,
  isCurrentPlayer = false,
  boardSize
}) => {
  // Convert position to percentage for responsive sizing
  const positionStyle = position ? {
    position: 'absolute',
    left: 0,
    top: 0,
    transform: `translate(${position.x}px, ${position.y}px)`,
    transition: 'none', // Animation handled by hook
    zIndex: isCurrentPlayer ? 20 : 10,
    willChange: isAnimating ? 'transform' : 'auto'
  } : {};

  return (
    <Box
      data-player-id={player.id}
      className={`player-token ${isAnimating ? 'animating' : ''} ${isCurrentPlayer ? 'current' : ''}`}
      sx={{
        ...positionStyle,
        width: '2.5%',
        height: '2.5%',
        minWidth: '20px',
        minHeight: '20px',
        maxWidth: '35px',
        maxHeight: '35px',
        borderRadius: '50%',
        backgroundColor: player.color || '#999',
        border: isCurrentPlayer ? '3px solid gold' : '2px solid rgba(0,0,0,0.3)',
        boxShadow: isCurrentPlayer 
          ? '0 0 15px rgba(255, 215, 0, 0.6), 0 2px 4px rgba(0,0,0,0.3)' 
          : '0 2px 4px rgba(0,0,0,0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '0.7em',
        fontWeight: 'bold',
        color: 'white',
        textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
        cursor: 'pointer',
        '&:hover': {
          transform: `${positionStyle.transform} scale(1.1)`,
          boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
          zIndex: 30
        },
        '&.animating': {
          animation: 'none' // Remove old animation, using transform instead
        }
      }}
    >
      {player.token || player.name?.[0] || 'P'}
    </Box>
  );
});

PlayerToken.displayName = 'PlayerToken';

export default PlayerToken;