import React, { useEffect } from 'react';
import { Box, Typography, Tooltip, useTheme, alpha } from '@mui/material';
import { styled } from '@mui/material/styles';
import { useGame } from '../../contexts/GameContext';

// Board layout constants
const BOARD_SPACES = [
  // Bottom row (left to right, 0-10)
  { id: 0, name: 'GO', type: 'corner', color: '#FF0000' }, 
  { id: 1, name: 'Mediterranean Ave', type: 'property', group: 'brown' },
  { id: 2, name: 'Community Chest', type: 'chest', color: '#FFA500' },
  { id: 3, name: 'Baltic Ave', type: 'property', group: 'brown' },
  { id: 4, name: 'Income Tax', type: 'tax', color: '#8B0000' },
  { id: 5, name: 'Reading RR', type: 'railroad', color: '#000000' },
  { id: 6, name: 'Oriental Ave', type: 'property', group: 'lightblue' },
  { id: 7, name: 'Chance', type: 'chance', color: '#0000FF' },
  { id: 8, name: 'Vermont Ave', type: 'property', group: 'lightblue' },
  { id: 9, name: 'Connecticut Ave', type: 'property', group: 'lightblue' },
  { id: 10, name: 'JAIL', type: 'corner', color: '#FFCC00' },
  // Left column (bottom to top, 11-20)
  { id: 11, name: 'St. Charles Place', type: 'property', group: 'pink' },
  { id: 12, name: 'Electric Co.', type: 'utility', color: '#FFFF00' },
  { id: 13, name: 'States Ave', type: 'property', group: 'pink' },
  { id: 14, name: 'Virginia Ave', type: 'property', group: 'pink' },
  { id: 15, name: 'Pennsylvania RR', type: 'railroad', color: '#000000' },
  { id: 16, name: 'St. James Place', type: 'property', group: 'orange' },
  { id: 17, name: 'Community Chest', type: 'chest', color: '#FFA500' },
  { id: 18, name: 'Tennessee Ave', type: 'property', group: 'orange' },
  { id: 19, name: 'New York Ave', type: 'property', group: 'orange' },
  { id: 20, name: 'FREE PARKING', type: 'corner', color: '#00FF00' },
  // Top row (left to right, 21-30)
  { id: 21, name: 'Kentucky Ave', type: 'property', group: 'red' },
  { id: 22, name: 'Chance', type: 'chance', color: '#0000FF' },
  { id: 23, name: 'Indiana Ave', type: 'property', group: 'red' },
  { id: 24, name: 'Illinois Ave', type: 'property', group: 'red' },
  { id: 25, name: 'B&O RR', type: 'railroad', color: '#000000' },
  { id: 26, name: 'Atlantic Ave', type: 'property', group: 'yellow' },
  { id: 27, name: 'Ventnor Ave', type: 'property', group: 'yellow' },
  { id: 28, name: 'Water Works', type: 'utility', color: '#FFFF00' },
  { id: 29, name: 'Marvin Gardens', type: 'property', group: 'yellow' },
  { id: 30, name: 'GO TO JAIL', type: 'corner', color: '#FF0000' },
  // Right column (top to bottom, 31-39)
  { id: 31, name: 'Pacific Ave', type: 'property', group: 'green' },
  { id: 32, name: 'North Carolina Ave', type: 'property', group: 'green' },
  { id: 33, name: 'Community Chest', type: 'chest', color: '#FFA500' },
  { id: 34, name: 'Pennsylvania Ave', type: 'property', group: 'green' },
  { id: 35, name: 'Short Line RR', type: 'railroad', color: '#000000' },
  { id: 36, name: 'Chance', type: 'chance', color: '#0000FF' },
  { id: 37, name: 'Park Place', type: 'property', group: 'blue' },
  { id: 38, name: 'Luxury Tax', type: 'tax', color: '#8B0000' },
  { id: 39, name: 'Boardwalk', type: 'property', group: 'blue' },
];

// Group colors with improved shades
const GROUP_COLORS = {
  brown: '#8B4513',
  lightblue: '#87CEEB',
  pink: '#FF69B4',
  orange: '#FFA500',
  red: '#FF0000',
  yellow: '#FFD700',
  green: '#008000',
  blue: '#0000CD',
  railroad: '#000000',
  utility: '#3CB371',
};

// Player colors
const PLAYER_COLORS = [
  '#E53935', // Red
  '#1E88E5', // Blue
  '#43A047', // Green
  '#FDD835', // Yellow
  '#8E24AA', // Purple
  '#FB8C00', // Orange
  '#26A69A', // Teal
  '#EC407A', // Pink
];

// Styled components for the board
const BoardContainer = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: '1fr repeat(9, 0.7fr) 1fr',
  gridTemplateRows: '1fr repeat(9, 0.7fr) 1fr',
  width: '95vw',
  height: '95vw',
  maxWidth: '900px',
  maxHeight: '900px',
  margin: '0 auto',
  border: '4px solid #333',
  borderRadius: '16px',
  boxShadow: '0 16px 40px rgba(0,0,0,0.3), inset 0 2px 10px rgba(255,255,255,0.3)',
  position: 'relative',
  backgroundImage: 'linear-gradient(45deg, #E8F5E9 25%, #C8E6C9 25%, #C8E6C9 50%, #E8F5E9 50%, #E8F5E9 75%, #C8E6C9 75%, #C8E6C9 100%)',
  backgroundSize: '40px 40px',
  perspective: '1000px',
  transformStyle: 'preserve-3d',
  transform: 'rotateX(5deg)',
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
}));

// Space component with improved visuals
const BoardSpace = styled(Box)(({ theme, spaceType, color, owned, active }) => {
  const baseStyles = {
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
    backgroundColor: 'white',
    boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.05)',
    transition: 'all 0.3s ease',
    '&:hover': {
      transform: 'scale(1.05) translateZ(5px)',
      zIndex: 10,
      boxShadow: '0 5px 15px rgba(0,0,0,0.15), inset 0 1px 3px rgba(0,0,0,0.05)',
    }
  };

  // Custom styles based on space type
  if (spaceType === 'corner') {
    return {
      ...baseStyles,
      backgroundColor: alpha(color, 0.2),
      fontWeight: 'bold',
      borderWidth: '2px',
    };
  }

  if (spaceType === 'property') {
    return {
      ...baseStyles,
      backgroundColor: owned ? alpha(color, 0.3) : 'white',
      borderTop: active ? `3px solid ${theme.palette.secondary.main}` : undefined,
      animation: active ? 'pulse 1.5s infinite' : 'none',
    };
  }

  if (spaceType === 'railroad') {
    return {
      ...baseStyles,
      backgroundImage: 'repeating-linear-gradient(45deg, #333333, #333333 5px, #ffffff 5px, #ffffff 10px)',
      backgroundSize: '15px 15px',
      color: '#fff',
      textShadow: '0 1px 1px rgba(0,0,0,0.7)',
    };
  }

  if (spaceType === 'utility') {
    return {
      ...baseStyles,
      backgroundImage: 'radial-gradient(circle, #333 1px, transparent 1px)',
      backgroundSize: '8px 8px',
    };
  }

  if (spaceType === 'chest' || spaceType === 'chance') {
    return {
      ...baseStyles,
      backgroundColor: alpha(color, 0.3),
      fontStyle: 'italic',
    };
  }

  if (spaceType === 'tax') {
    return {
      ...baseStyles,
      backgroundColor: '#FFECB3',
    };
  }

  return baseStyles;
});

// Color stripe for properties
const PropertyStripe = styled(Box)(({ color }) => ({
  height: '18%',
  backgroundColor: color,
  width: '100%',
  borderRadius: '3px 3px 0 0',
  boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
}));

// Player token styling
const PlayerToken = styled(Box)(({ color, isCurrentPlayer }) => ({
  position: 'absolute',
  bottom: '10%',
  left: '50%',
  transform: 'translateX(-50%)',
  width: '36px',
  height: '36px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: color,
  borderRadius: '50%',
  border: isCurrentPlayer ? '3px solid gold' : '2px solid #333',
  boxShadow: isCurrentPlayer 
    ? '0 0 18px gold, 0 0 8px rgba(255,215,0,0.8)' 
    : '0 3px 8px rgba(0,0,0,0.3)',
  zIndex: 100,
  transition: 'all 0.8s cubic-bezier(0.22, 1, 0.36, 1)',
  animation: isCurrentPlayer ? 'pulse 1.5s infinite' : 'none',
  '&:hover': {
    transform: 'translateX(-50%) scale(1.3)',
    zIndex: 200,
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
}));

// Center area of the board
const BoardCenter = styled(Box)(({ theme }) => ({
  gridColumn: '2 / 11',
  gridRow: '2 / 11',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundImage: 'radial-gradient(circle, #C8E6C9, #81C784)',
  borderRadius: '8px',
  boxShadow: 'inset 0 0 30px rgba(0,0,0,0.1)',
  padding: '20px',
  textAlign: 'center',
}));

// Function to get grid position for a space
const getGridPosition = (index) => {
  if (index >= 0 && index <= 10) return { row: 11, col: 11 - index }; // Bottom row
  if (index >= 11 && index <= 20) return { row: 21 - index, col: 1 }; // Left column
  if (index >= 21 && index <= 30) return { row: 1, col: index - 20 }; // Top row
  if (index >= 31 && index <= 39) return { row: index - 30, col: 11 }; // Right column
  return { row: 1, col: 1 }; // Default fallback
};

const Board = ({ players, currentPlayerId, properties = [] }) => {
  const theme = useTheme();
  const { gameState } = useGame();

  // Enhance board spaces with positions and ownership data
  const boardSpaces = BOARD_SPACES.map(space => {
    const position = getGridPosition(space.id);
    const property = properties.find(p => p.position === space.id);
    
    return {
      ...space,
      gridRow: position.row,
      gridColumn: position.col,
      owner_id: property?.owner_id,
      isActive: gameState?.currentSpace === space.id
    };
  });

  return (
    <BoardContainer>
      {/* Center area with logo and game info */}
      <BoardCenter>
        <Typography variant="h2" fontWeight="700" color="primary" 
          sx={{ textShadow: '1px 1px 5px rgba(0,0,0,0.1)', mb: 2, letterSpacing: '-1px' }}>
          Pi-nopoly
        </Typography>
        
        <Typography variant="body1" sx={{ maxWidth: '70%', mb: 3 }}>
          A modern take on the classic board game
        </Typography>
        
        {gameState?.notifications?.length > 0 && (
          <Typography variant="h6" fontWeight="500" sx={{ color: theme.palette.secondary.main }}>
            {gameState.notifications[gameState.notifications.length - 1]}
          </Typography>
        )}
      </BoardCenter>

      {/* Render board spaces */}
      {boardSpaces.map(space => (
        <Tooltip 
          key={space.id} 
          title={`${space.name} (${space.id})`}
          arrow
          placement="center"
        >
          <BoardSpace 
            spaceType={space.type} 
            color={space.type === 'property' ? GROUP_COLORS[space.group] : space.color}
            owned={space.owner_id !== undefined}
            active={space.isActive}
            sx={{ gridRow: space.gridRow, gridColumn: space.gridColumn }}
          >
            {space.type === 'property' && (
              <PropertyStripe color={GROUP_COLORS[space.group]} />
            )}
            
            <Typography variant="caption" sx={{ fontWeight: 500, mt: space.type === 'property' ? 1 : 0 }}>
              {space.name}
            </Typography>
            
            {/* Render player tokens on this space */}
            {players
              .filter(player => player.position === space.id)
              .map((player, index) => (
                <Tooltip key={player.id} title={player.username} arrow>
                  <PlayerToken 
                    color={PLAYER_COLORS[player.id % PLAYER_COLORS.length]}
                    isCurrentPlayer={player.id === currentPlayerId}
                    sx={{ 
                      bottom: `${5 + index * 16}%`,
                      left: '50%'
                    }}
                  >
                    <Typography sx={{ fontSize: '0.7rem', color: 'white', fontWeight: 'bold' }}>
                      {player.username.charAt(0).toUpperCase()}
                    </Typography>
                  </PlayerToken>
                </Tooltip>
              ))
            }
          </BoardSpace>
        </Tooltip>
      ))}
    </BoardContainer>
  );
};

export default Board; 