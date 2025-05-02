import React from 'react';
import { useParams } from 'react-router-dom';
import { Box } from '@mui/material';
import PlayerDashboard from '../features/player/PlayerDashboard';

function PlayerPage() {
  const { playerId } = useParams();
  return (
    <Box sx={{ pt: 2 }}>
      <PlayerDashboard playerId={playerId} />
    </Box>
  );
}

export default PlayerPage; 