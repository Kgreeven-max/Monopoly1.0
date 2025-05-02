import React, { useEffect } from 'react';
import { Box, Typography, Tooltip, useTheme, alpha } from '@mui/material';
import { styled } from '@mui/material/styles';
import { useGame } from '../../contexts/GameContext';

// Classic Monopoly color palette
const GROUP_COLORS = {
  brown: '#8B4513',     // Brown
  lightblue: '#ADD8E6', // Light blue
  pink: '#FF69B4',      // Pink
  orange: '#FFA500',    // Orange
  red: '#FF0000',       // Red
  yellow: '#FFFF00',    // Yellow
  green: '#008000',     // Green
  blue: '#00008B',      // Dark blue
  railroad: '#000000',  // Black for railroads
  utility: '#AAAAAA',   // Gray for utilities
};

// Special tile colors
const SPECIAL_COLORS = {
  corner: '#FFFFFF',      // White background for corners
  chance: '#C58BF1',      // Purple for chance
  chest: '#C8E6FF',       // Light blue for community chest
  tax: '#FFE699',         // Light yellow for taxes
};

// Player colors with better contrast
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

// Board layout constants
const BOARD_SPACES = [
  // Bottom row (left to right, 0-10)
  { id: 0, name: 'GO', type: 'corner', color: SPECIAL_COLORS.corner, isDouble: true }, 
  { id: 1, name: 'MEDITERRANEAN AVE', type: 'property', group: 'brown' },
  { id: 2, name: 'COMMUNITY CHEST', type: 'chest', color: SPECIAL_COLORS.chest },
  { id: 3, name: 'BALTIC AVE', type: 'property', group: 'brown' },
  { id: 4, name: 'INCOME TAX', type: 'tax', color: SPECIAL_COLORS.tax, value: 200 },
  { id: 5, name: 'READING RAILROAD', type: 'railroad', color: GROUP_COLORS.railroad },
  { id: 6, name: 'ORIENTAL AVE', type: 'property', group: 'lightblue' },
  { id: 7, name: 'CHANCE', type: 'chance', color: SPECIAL_COLORS.chance },
  { id: 8, name: 'VERMONT AVE', type: 'property', group: 'lightblue' },
  { id: 9, name: 'CONNECTICUT AVE', type: 'property', group: 'lightblue' },
  { id: 10, name: 'JAIL', type: 'corner', color: SPECIAL_COLORS.corner, isDouble: true },
  // Left column (bottom to top, 11-20)
  { id: 11, name: 'ST. CHARLES PLACE', type: 'property', group: 'pink' },
  { id: 12, name: 'ELECTRIC COMPANY', type: 'utility', color: GROUP_COLORS.utility },
  { id: 13, name: 'STATES AVE', type: 'property', group: 'pink' },
  { id: 14, name: 'VIRGINIA AVE', type: 'property', group: 'pink' },
  { id: 15, name: 'PENNSYLVANIA RAILROAD', type: 'railroad', color: GROUP_COLORS.railroad },
  { id: 16, name: 'ST. JAMES PLACE', type: 'property', group: 'orange' },
  { id: 17, name: 'COMMUNITY CHEST', type: 'chest', color: SPECIAL_COLORS.chest },
  { id: 18, name: 'TENNESSEE AVE', type: 'property', group: 'orange' },
  { id: 19, name: 'NEW YORK AVE', type: 'property', group: 'orange' },
  { id: 20, name: 'FREE PARKING', type: 'corner', color: SPECIAL_COLORS.corner, isDouble: true },
  // Top row (left to right, 21-30)
  { id: 21, name: 'KENTUCKY AVE', type: 'property', group: 'red' },
  { id: 22, name: 'CHANCE', type: 'chance', color: SPECIAL_COLORS.chance },
  { id: 23, name: 'INDIANA AVE', type: 'property', group: 'red' },
  { id: 24, name: 'ILLINOIS AVE', type: 'property', group: 'red' },
  { id: 25, name: 'B & O RAILROAD', type: 'railroad', color: GROUP_COLORS.railroad },
  { id: 26, name: 'ATLANTIC AVE', type: 'property', group: 'yellow' },
  { id: 27, name: 'VENTNOR AVE', type: 'property', group: 'yellow' },
  { id: 28, name: 'WATER WORKS', type: 'utility', color: GROUP_COLORS.utility },
  { id: 29, name: 'MARVIN GARDENS', type: 'property', group: 'yellow' },
  { id: 30, name: 'GO TO JAIL', type: 'corner', color: SPECIAL_COLORS.corner, isDouble: true },
  // Right column (top to bottom, 31-39)
  { id: 31, name: 'PACIFIC AVE', type: 'property', group: 'green' },
  { id: 32, name: 'NORTH CAROLINA AVE', type: 'property', group: 'green' },
  { id: 33, name: 'COMMUNITY CHEST', type: 'chest', color: SPECIAL_COLORS.chest },
  { id: 34, name: 'PENNSYLVANIA AVE', type: 'property', group: 'green' },
  { id: 35, name: 'SHORT LINE RAILROAD', type: 'railroad', color: GROUP_COLORS.railroad },
  { id: 36, name: 'CHANCE', type: 'chance', color: SPECIAL_COLORS.chance },
  { id: 37, name: 'PARK PLACE', type: 'property', group: 'blue' },
  { id: 38, name: 'LUXURY TAX', type: 'tax', color: SPECIAL_COLORS.tax, value: 100 },
  { id: 39, name: 'BOARDWALK', type: 'property', group: 'blue' },
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
  backgroundColor: '#FAFAF8',
  border: '2px solid #000000',
  borderRadius: '8px',
  boxShadow: '0 5px 15px rgba(0,0,0,0.2)',
  position: 'relative',
  gap: '2px', // Consistent gap between tiles
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
const BoardSpace = styled(Box)(({ theme, spaceType, color, owned, isDouble }) => {
  // Base styles for all tiles
  const baseStyles = {
    border: '2px solid #000000',
    borderRadius: '4px',
    padding: 0,
    textAlign: 'center',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'flex-start',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    overflow: 'hidden',
    minHeight: '100%',
    boxSizing: 'border-box',
  };

  // Corner tiles (GO, JAIL, FREE PARKING, GO TO JAIL)
  if (spaceType === 'corner') {
    return {
      ...baseStyles,
      backgroundColor: '#FFFFFF',
      fontWeight: 'bold',
    };
  }

  // Property tiles with colored top stripe
  if (spaceType === 'property') {
    return {
      ...baseStyles,
      backgroundColor: owned ? '#F8F8F8' : '#FFFFFF',
    };
  }

  // Railroad tiles
  if (spaceType === 'railroad') {
    return {
      ...baseStyles,
      backgroundColor: '#FFFFFF',
    };
  }

  // Utility tiles
  if (spaceType === 'utility') {
    return {
      ...baseStyles,
      backgroundColor: '#FFFFFF',
    };
  }

  // Chance tiles
  if (spaceType === 'chance') {
    return {
      ...baseStyles,
      backgroundColor: '#FFFFFF',
    };
  }

  // Community chest tiles
  if (spaceType === 'chest') {
    return {
      ...baseStyles,
      backgroundColor: '#FFFFFF',
    };
  }

  // Tax tiles
  if (spaceType === 'tax') {
    return {
      ...baseStyles,
      backgroundColor: '#FFFFFF',
    };
  }

  return baseStyles;
});

// Classic Monopoly property stripe
const PropertyStripe = styled(Box)(({ color }) => ({
  height: '25%',
  backgroundColor: color,
  width: '100%',
  borderBottom: '2px solid #000000',
}));

// Railroad icon container
const RailroadIconContainer = styled(Box)({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '25%',
  width: '100%',
  backgroundColor: '#000000',
  borderBottom: '2px solid #000000',
});

// Utility pattern overlay
const UtilityContainer = styled(Box)({
  height: '25%',
  width: '100%',
  backgroundColor: '#AAAAAA',
  borderBottom: '2px solid #000000',
});

// Chance/community chest decoration
const CardContainer = styled(Box)(({ color }) => ({
  height: '25%',
  width: '100%',
  backgroundColor: color,
  borderBottom: '2px solid #000000',
}));

// Tax decoration
const TaxContainer = styled(Box)({
  height: '25%',
  width: '100%',
  backgroundColor: '#FFE699',
  borderBottom: '2px solid #000000',
});

// Player token styling
const PlayerToken = styled(Box)(({ color, isCurrentPlayer }) => ({
  position: 'absolute',
  bottom: '8px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '24px',
  height: '24px',
  backgroundColor: color,
  borderRadius: '50%',
  border: isCurrentPlayer ? '2px solid gold' : '1px solid #333',
  boxShadow: isCurrentPlayer 
    ? '0 0 8px gold' 
    : '0 2px 4px rgba(0,0,0,0.2)',
  zIndex: isCurrentPlayer ? 101 : 100,
  fontFamily: 'Arial, sans-serif',
  fontWeight: 'bold',
  color: '#FFF',
  fontSize: '0.7rem',
}));

// Center area of the board
const BoardCenter = styled(Box)(({ theme }) => ({
  gridColumn: '2 / 11',
  gridRow: '2 / 11',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: '#FAFAF8',
  backgroundImage: `
    linear-gradient(45deg, #FAFAF8 25%, transparent 25%, transparent 75%, #FAFAF8 75%, #FAFAF8),
    linear-gradient(45deg, #FAFAF8 25%, transparent 25%, transparent 75%, #FAFAF8 75%, #FAFAF8)
  `,
  backgroundSize: '60px 60px',
  backgroundPosition: '0 0, 30px 30px',
  padding: '20px',
  textAlign: 'center',
  border: '2px solid #000000',
  borderRadius: '4px',
  margin: '2px',
}));

// Function to get grid position for a space
const getGridPosition = (index) => {
  if (index >= 0 && index <= 10) return { row: 11, col: 11 - index }; // Bottom row
  if (index >= 11 && index <= 20) return { row: 21 - index, col: 1 }; // Left column
  if (index >= 21 && index <= 30) return { row: 1, col: index - 20 }; // Top row
  if (index >= 31 && index <= 39) return { row: index - 30, col: 11 }; // Right column
  return { row: 1, col: 1 }; // Default fallback
};

const Board = ({ players = [], currentPlayerId, properties = [] }) => {
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

  // Function to stagger player tokens when multiple players are on the same space
  const getPlayerPosition = (playerIndex, totalPlayers) => {
    if (totalPlayers === 1) return { left: '50%' };
    
    // Calculate position based on number of players on the space
    const angleStep = Math.min(30, 90 / (totalPlayers - 1));
    const radius = 15; // px from center
    const angle = -45 + playerIndex * angleStep;
    const x = 50 + radius * Math.cos(angle * Math.PI / 180);
    const y = 50 + radius * Math.sin(angle * Math.PI / 180);
    
    return { left: `${x}%`, bottom: `${y}%` };
  };

  // Render railroad icon
  const RailroadIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 15.5L20 15.5M7 18.5L17 18.5M12 5.5V15.5M8 5.5H16M7 8.5H17M6 11.5H18" stroke="white" strokeWidth="1.5"/>
      <rect x="9" y="8.5" width="6" height="3" fill="white"/>
    </svg>
  );

  // Render utility icon
  const UtilityIcon = ({ type }) => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      {type === 'electric' ? (
        <path d="M13 2L5 12H12L11 22L19 11H12L13 2Z" fill="white" stroke="black" strokeWidth="1"/>
      ) : (
        <path d="M7,7 C9.5,4.5 14.5,4.5 17,7 C19.5,9.5 19.5,14.5 17,17 C14.5,19.5 9.5,19.5 7,17 C4.5,14.5 4.5,9.5 7,7 Z" fill="white" stroke="black" strokeWidth="1"/>
      )}
    </svg>
  );

  // Render chance icon
  const ChanceIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="white"/>
      <path d="M12 6C9.79 6 8 7.79 8 10H10C10 8.9 10.9 8 12 8C13.1 8 14 8.9 14 10C14 12 11 12.5 11 15H13C13 13.5 16 13 16 10C16 7.79 14.21 6 12 6ZM11 16H13V18H11V16Z" fill="#C58BF1"/>
    </svg>
  );

  // Render community chest icon
  const ChestIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="5" y="8" width="14" height="10" fill="white" stroke="#C8E6FF" strokeWidth="2"/>
      <rect x="8" y="6" width="8" height="2" fill="#C8E6FF"/>
      <rect x="7" y="12" width="10" height="2" fill="#C8E6FF"/>
    </svg>
  );

  return (
    <BoardContainer>
      {/* Center area with logo and game info */}
      <BoardCenter>
        <Typography 
          variant="h2" 
          fontWeight="700" 
          color="primary"
          sx={{ 
            fontFamily: '"Arial", sans-serif',
            textShadow: '1px 1px 5px rgba(0,0,0,0.1)', 
            mb: 2,
            letterSpacing: '-1px' 
          }}
        >
          Pi-nopoly
        </Typography>
        
        <Typography 
          variant="body1" 
          sx={{ 
            maxWidth: '70%', 
            mb: 3,
            fontFamily: '"Arial", sans-serif',
          }}
        >
          A modern take on the classic board game
        </Typography>
        
        {gameState?.notifications?.length > 0 && (
          <Typography 
            variant="h6" 
            fontWeight="500" 
            sx={{ 
              color: theme.palette.secondary.main,
              fontFamily: '"Arial", sans-serif',
            }}
          >
            {gameState.notifications[gameState.notifications.length - 1]}
          </Typography>
        )}
      </BoardCenter>

      {/* Render board spaces */}
      {boardSpaces.map(space => {
        // Get players on this space
        const playersOnSpace = players.filter(player => player.position === space.id);
        
        return (
          <Tooltip 
            key={space.id} 
            title={`${space.name}`}
            arrow
            placement="center"
          >
            <BoardSpace 
              spaceType={space.type} 
              color={space.type === 'property' ? GROUP_COLORS[space.group] : space.color}
              owned={space.owner_id !== undefined}
              isDouble={space.isDouble}
              sx={{ 
                gridRow: space.gridRow, 
                gridColumn: space.gridColumn,
                boxShadow: space.isActive ? '0 0 8px 2px rgba(255, 215, 0, 0.5)' : undefined,
              }}
            >
              {/* Property color stripe */}
              {space.type === 'property' && (
                <PropertyStripe color={GROUP_COLORS[space.group]} />
              )}
              
              {/* Railroad header */}
              {space.type === 'railroad' && (
                <RailroadIconContainer>
                  <RailroadIcon />
                </RailroadIconContainer>
              )}
              
              {/* Utility header */}
              {space.type === 'utility' && (
                <UtilityContainer>
                  <UtilityIcon type={space.name.includes('ELECTRIC') ? 'electric' : 'water'} />
                </UtilityContainer>
              )}
              
              {/* Chance header */}
              {space.type === 'chance' && (
                <CardContainer color={SPECIAL_COLORS.chance}>
                  <ChanceIcon />
                </CardContainer>
              )}
              
              {/* Community chest header */}
              {space.type === 'chest' && (
                <CardContainer color={SPECIAL_COLORS.chest}>
                  <ChestIcon />
                </CardContainer>
              )}
              
              {/* Tax header */}
              {space.type === 'tax' && (
                <TaxContainer>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontFamily: '"Arial", sans-serif',
                      fontWeight: 'bold',
                      fontSize: '10px',
                      color: '#000000',
                    }}
                  >
                    TAX
                  </Typography>
                </TaxContainer>
              )}
              
              {/* Corner spaces */}
              {space.type === 'corner' && (
                <Box sx={{ 
                  width: '100%', 
                  height: '100%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  padding: '4px',
                  boxSizing: 'border-box',
                }}>
                  {space.id === 0 && ( // GO
                    <Typography 
                      variant="h6" 
                      sx={{ 
                        fontFamily: '"Arial Black", sans-serif',
                        fontWeight: 'bold',
                        transform: 'rotate(-45deg)',
                        color: '#FF0000',
                      }}
                    >
                      GO
                    </Typography>
                  )}
                  
                  {space.id === 10 && ( // JAIL
                    <Box sx={{ 
                      width: '100%',
                      height: '100%',
                      position: 'relative',
                      border: 'none',
                    }}>
                      <Box sx={{ 
                        position: 'absolute',
                        top: 0,
                        right: 0,
                        width: '60%',
                        height: '60%',
                        backgroundColor: '#FF9800',
                        borderBottomLeftRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: '10px',
                      }}>
                        JUST
                      </Box>
                      <Box sx={{ 
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: '12px',
                      }}>
                        JAIL
                      </Box>
                    </Box>
                  )}
                  
                  {space.id === 20 && ( // FREE PARKING
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontFamily: '"Arial Black", sans-serif',
                        fontWeight: 'bold',
                        textAlign: 'center',
                        color: '#FF0000',
                        fontSize: '10px',
                        lineHeight: 1,
                      }}
                    >
                      FREE<br/>PARKING
                    </Typography>
                  )}
                  
                  {space.id === 30 && ( // GO TO JAIL
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontFamily: '"Arial Black", sans-serif',
                        fontWeight: 'bold',
                        textAlign: 'center',
                        color: '#FF0000',
                        fontSize: '10px',
                        lineHeight: 1,
                      }}
                    >
                      GO TO<br/>JAIL
                    </Typography>
                  )}
                </Box>
              )}
              
              {/* Space name with proper Monopoly typography */}
              {space.type !== 'corner' && (
                <Typography 
                  variant="caption" 
                  className="board-space-name"
                  sx={{ 
                    fontFamily: '"Arial", sans-serif',
                    fontWeight: 'bold',
                    fontSize: '10px',
                    lineHeight: 1.2,
                    margin: '5px 2px',
                    color: '#000000',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    textTransform: 'uppercase',
                  }}
                >
                  {space.name}
                </Typography>
              )}
              
              {/* Tax value */}
              {space.type === 'tax' && (
                <Typography 
                  variant="caption" 
                  sx={{ 
                    fontFamily: '"Arial", sans-serif',
                    fontWeight: 'bold',
                    fontSize: '10px',
                    mt: 1,
                    color: '#000000',
                  }}
                >
                  ${space.value}
                </Typography>
              )}
              
              {/* Render player tokens on this space */}
              {playersOnSpace.map((player, index) => {
                const position = getPlayerPosition(index, playersOnSpace.length);
                
                return (
                  <Tooltip key={player.id} title={player.username} arrow>
                    <PlayerToken 
                      color={PLAYER_COLORS[player.id % PLAYER_COLORS.length]}
                      isCurrentPlayer={player.id === currentPlayerId}
                      className="player-token"
                      sx={{ 
                        ...position,
                        transform: 'translateX(-50%)',
                      }}
                    >
                      {player.username.charAt(0).toUpperCase()}
                    </PlayerToken>
                  </Tooltip>
                );
              })}
            </BoardSpace>
          </Tooltip>
        );
      })}
    </BoardContainer>
  );
};

export default Board; 