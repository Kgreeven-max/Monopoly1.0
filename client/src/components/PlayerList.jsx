import React from 'react';
import { Box, Typography, Avatar, Paper, Chip, Table, TableBody, TableCell, TableContainer, TableRow } from '@mui/material';
import { styled } from '@mui/material/styles';

// Create styled components for better visuals
const PlayerRow = styled(TableRow)(({ theme, isCurrentPlayer }) => ({
  backgroundColor: isCurrentPlayer ? 'rgba(46, 125, 50, 0.08)' : 'transparent',
  '&:nth-of-type(odd)': {
    backgroundColor: isCurrentPlayer ? 'rgba(46, 125, 50, 0.12)' : theme.palette.action.hover,
  },
  '&:last-child td, &:last-child th': {
    border: 0,
  },
  transition: 'background-color 0.3s',
  '&:hover': {
    backgroundColor: isCurrentPlayer ? 'rgba(46, 125, 50, 0.2)' : theme.palette.action.selected,
  }
}));

const PlayerAvatar = styled(Avatar)(({ theme, color }) => ({
  backgroundColor: color || theme.palette.primary.main,
  width: 32,
  height: 32,
  fontSize: '1rem',
  fontWeight: 'bold',
  border: '2px solid white',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
}));

// Color mapping for player avatars
const playerColors = [
  '#D32F2F', // Red
  '#1976D2', // Blue
  '#388E3C', // Green
  '#FFA000', // Amber
  '#7B1FA2', // Purple
  '#C2185B', // Pink
  '#0288D1', // Light Blue
  '#F57C00', // Orange
];

const PlayerList = ({ players, currentPlayerId }) => {
  if (!players || players.length === 0) {
    return (
      <Typography variant="body1" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
        No players in the game yet.
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper} elevation={0} sx={{ backgroundColor: 'transparent' }}>
      <Table size="small">
        <TableBody>
          {players.map((player, index) => {
            const isCurrentPlayer = player.id === currentPlayerId;
            const avatarColor = playerColors[index % playerColors.length];
            const initial = player.username ? player.username.charAt(0).toUpperCase() : 'P';
            
            return (
              <PlayerRow key={player.id} isCurrentPlayer={isCurrentPlayer}>
                <TableCell sx={{ width: '40px', pr: 0 }}>
                  <PlayerAvatar color={avatarColor}>
                    {initial}
                  </PlayerAvatar>
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1" fontWeight={isCurrentPlayer ? 'bold' : 'normal'}>
                        {player.username || `Player ${player.id}`}
                      </Typography>
                      {isCurrentPlayer && (
                        <Chip
                          label="Current Turn"
                          size="small"
                          color="success"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>
                    
                    <Box sx={{ display: 'flex', gap: 2, mt: 1, fontSize: '0.85rem' }}>
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" color="text.secondary">Money</Typography>
                        <Typography variant="body2" fontWeight="medium" color={player.money < 100 ? 'error.main' : 'success.main'}>
                          ${player.money || 0}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" color="text.secondary">Position</Typography>
                        <Typography variant="body2">
                          {player.position !== undefined ? player.position : 'N/A'}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="caption" color="text.secondary">Properties</Typography>
                        <Typography variant="body2">
                          {player.properties ? player.properties.length : 0}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </TableCell>
              </PlayerRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default PlayerList; 