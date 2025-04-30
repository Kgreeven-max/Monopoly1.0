import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert, Paper, Grid, Container, Button } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';

function PlayerPage() {
  const { playerId } = useParams();
  // const { playerInfo } = useAuth(); // playerInfo from Auth might be stale, prefer gameState
  const { gameState } = useGame();
  const { emit } = useSocket(); 
  // Removed local playerData and loading state, rely directly on gameState
  const [error, setError] = useState(''); // Keep error state for potential future use

  // Removed useEffect that managed loading state based on gameState.players.length
  useEffect(() => {
    console.log('[PlayerPage] Game State Updated:', gameState);
  }, [gameState]);

  const handleStartGame = () => {
      console.log("Attempting to start game...");
      emit('start_game', {});
  };

  // Determine if the current player is the active player
  // Ensure playerId is parsed correctly for comparison
  const currentPlayerIdInt = parseInt(playerId, 10);
  const isCurrentPlayer = gameState?.current_player_id === currentPlayerIdInt;
  const isGameInProgress = gameState?.status === 'In Progress';
  const canPerformActions = isCurrentPlayer && isGameInProgress;

  // Get player-specific data from gameState for display
  const currentPlayerDisplayData = gameState?.players?.find(p => p.id === currentPlayerIdInt);

  // --- Conditional Rendering --- 

  // 1. Show loading indicator if the specific player's data isn't available yet
  if (!currentPlayerDisplayData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Waiting for player data...</Typography> 
      </Box>
    );
  }

  // 2. Show error if error state is set (currently not used much, but good practice)
  if (error) {
    return (
      <Container maxWidth="sm" sx={{ mt: 4 }}>
         <Alert severity="error">{error}</Alert>
      </Container>
    );
  }

  // 3. Render the main content now that we know currentPlayerDisplayData exists
  const displayData = currentPlayerDisplayData; // No need for fallback anymore
  
  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Player Dashboard - {displayData.username} (ID: {playerId})
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {/* Status Panel */}
          <Grid item xs={12} md={6}>
            <Typography variant="h6">Status</Typography>
            <Typography><strong>Game Status:</strong> {gameState?.status || 'Loading...'}</Typography>
            <Typography><strong>Current Turn:</strong> Player {gameState?.current_player_id ?? 'N/A'}</Typography>
            <Typography><strong>Cash:</strong> ${displayData.money}</Typography>
            <Typography><strong>Position:</strong> Space {displayData.position}</Typography>
            <Typography><strong>In Jail?:</strong> {displayData.in_jail ? 'Yes' : 'No'}</Typography>
            {/* Add more status fields as needed */}
          </Grid>
          
          {/* Actions Panel */}
          <Grid item xs={12} md={6}>
             <Typography variant="h6">Actions</Typography>
             <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
                {/* REMOVED Start Game button - only admin can start */}
                {/* {gameState?.status === 'Waiting' && (
                    <Button
                        variant="contained"
                        color="success"
                        onClick={handleStartGame}
                    >
                        Start Game
                    </Button>
                )} */}

                {/* Standard game actions */}
                <Button 
                  variant="contained" 
                  onClick={() => emit('roll_dice', { playerId: parseInt(playerId) })} 
                  disabled={!canPerformActions} // Disable based on turn and status
                >
                  Roll Dice
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => emit('buy_property', { playerId: parseInt(playerId) })} 
                  disabled={!canPerformActions} // TODO: Add more specific logic (e.g., !isOnBuyableProperty)
                >
                  Buy Property
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => emit('end_turn', { playerId: parseInt(playerId) })} 
                  disabled={!canPerformActions} // Disable based on turn and status
                >
                  End Turn
                </Button>
             </Box>
          </Grid>

          {/* Properties Panel */}
          <Grid item xs={12}>
             <Typography variant="h6" sx={{ mt: 2 }}>Properties</Typography>
             {/* TODO: Fetch and display player properties from gameState */}
             <Typography>Property display coming soon...</Typography>
          </Grid>
        </Grid>
      </Paper>
       {/* TODO: Add Game Log / Notifications Area */}
    </Container>
  );
}

export default PlayerPage; 