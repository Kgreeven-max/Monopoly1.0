import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  CircularProgress, 
  Alert, 
  Paper, 
  Grid, 
  Container, 
  Button, 
  Card, 
  CardContent, 
  Divider,
  Avatar,
  Chip,
  Stack,
  IconButton
} from '@mui/material';
import { useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';
import CasinoIcon from '@mui/icons-material/Casino';
import HomeIcon from '@mui/icons-material/Home';
import DoNotDisturbOnIcon from '@mui/icons-material/DoNotDisturbOn';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import MapIcon from '@mui/icons-material/Map';
import NotificationsIcon from '@mui/icons-material/Notifications';

function PlayerPage() {
  const { playerId } = useParams();
  const { gameState } = useGame();
  const { emit } = useSocket(); 
  const [error, setError] = useState('');
  const [notification, setNotification] = useState(null);

  // Log game state updates
  useEffect(() => {
    console.log('[PlayerPage] Game State Updated:', gameState);
  }, [gameState]);

  // Show notification when it's player's turn
  useEffect(() => {
    if (gameState?.current_player_id === parseInt(playerId, 10) && gameState?.status === 'In Progress') {
      setNotification("It's your turn to play!");
      
      // Clear notification after 5 seconds
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [gameState?.current_player_id, playerId, gameState?.status]);

  const handleStartGame = () => {
    console.log("Attempting to start game...");
    emit('start_game', {});
  };

  // Game state helpers
  const currentPlayerIdInt = parseInt(playerId, 10);
  const isCurrentPlayer = gameState?.current_player_id === currentPlayerIdInt;
  const isGameInProgress = gameState?.status === 'In Progress';
  const canPerformActions = isCurrentPlayer && isGameInProgress;

  // Get player data
  const currentPlayerDisplayData = gameState?.players?.find(p => p.id === currentPlayerIdInt);

  // Loading state
  if (!currentPlayerDisplayData) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          backgroundColor: '#f5f5f5'
        }}
      >
        <CircularProgress size={60} thickness={4} />
        <Typography variant="h6" sx={{ mt: 3, fontWeight: 500 }}>
          Connecting to game...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="sm" sx={{ mt: 4 }}>
         <Alert severity="error" variant="filled">{error}</Alert>
      </Container>
    );
  }

  const displayData = currentPlayerDisplayData;
  
  return (
    <Box sx={{ 
      minHeight: '100vh', 
      backgroundColor: '#f5f5f5',
      pt: 3,
      pb: 6
    }}>
      <Container maxWidth="lg">
        {/* Notification area */}
        {notification && (
          <Alert 
            severity="info" 
            variant="filled"
            sx={{ 
              mb: 3, 
              borderRadius: 2,
              boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
            }}
            action={
              <IconButton color="inherit" size="small" onClick={() => setNotification(null)}>
                <NotificationsIcon fontSize="small" />
              </IconButton>
            }
          >
            {notification}
          </Alert>
        )}
        
        {/* Player header */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar 
            sx={{ 
              width: 64, 
              height: 64, 
              bgcolor: 'primary.main',
              fontSize: '1.5rem',
              fontWeight: 'bold',
              mr: 2
            }}
          >
            {displayData.username.charAt(0).toUpperCase()}
          </Avatar>
          <Box>
            <Typography variant="h4" fontWeight="600">
              {displayData.username}
            </Typography>
            <Chip 
              label={isCurrentPlayer ? "Your Turn" : "Waiting"} 
              color={isCurrentPlayer ? "success" : "default"}
              size="small"
              sx={{ mt: 0.5 }}
            />
          </Box>
        </Box>

        <Grid container spacing={3}>
          {/* Player stats card */}
          <Grid item xs={12} md={4}>
            <Card 
              elevation={0} 
              sx={{ 
                borderRadius: 3,
                height: '100%',
                boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Player Stats
                </Typography>
                
                <Stack spacing={2} sx={{ mt: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AccountBalanceWalletIcon sx={{ color: 'success.main', mr: 2 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">Balance</Typography>
                      <Typography variant="h6" fontWeight="600">${displayData.money}</Typography>
                    </Box>
                  </Box>
                  
                  <Divider />
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <MapIcon sx={{ color: 'info.main', mr: 2 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">Position</Typography>
                      <Typography variant="h6">Space {displayData.position}</Typography>
                    </Box>
                  </Box>
                  
                  <Divider />
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <HomeIcon sx={{ color: displayData.in_jail ? 'error.main' : 'text.disabled', mr: 2 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">Jail Status</Typography>
                      <Typography variant="h6">{displayData.in_jail ? 'In Jail' : 'Free'}</Typography>
                    </Box>
                  </Box>
                </Stack>
                
                <Box sx={{ mt: 4 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Game Status
                  </Typography>
                  <Chip 
                    label={gameState?.status || 'Unknown'} 
                    color={isGameInProgress ? "primary" : "default"}
                    variant="outlined"
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Actions card */}
          <Grid item xs={12} md={4}>
            <Card 
              elevation={0} 
              sx={{ 
                borderRadius: 3,
                height: '100%',
                boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Game Actions
                </Typography>
                
                <Stack spacing={2} sx={{ mt: 3 }}>
                  <Button 
                    variant="contained" 
                    size="large"
                    startIcon={<CasinoIcon />}
                    onClick={() => emit('roll_dice', { playerId: parseInt(playerId) })} 
                    disabled={!canPerformActions}
                    fullWidth
                    disableElevation
                    sx={{ py: 1.5 }}
                  >
                    Roll Dice
                  </Button>
                  
                  <Button 
                    variant="outlined" 
                    size="large"
                    startIcon={<HomeIcon />}
                    onClick={() => emit('buy_property', { playerId: parseInt(playerId) })} 
                    disabled={!canPerformActions}
                    fullWidth
                    sx={{ py: 1.5 }}
                  >
                    Buy Property
                  </Button>
                  
                  <Button 
                    variant="outlined" 
                    color="secondary"
                    size="large"
                    startIcon={<DoNotDisturbOnIcon />}
                    onClick={() => emit('end_turn', { playerId: parseInt(playerId) })} 
                    disabled={!canPerformActions}
                    fullWidth
                    sx={{ py: 1.5 }}
                  >
                    End Turn
                  </Button>
                </Stack>
                
                <Box sx={{ mt: 4, opacity: canPerformActions ? 1 : 0.5 }}>
                  <Alert severity={canPerformActions ? "success" : "info"} variant="outlined">
                    {canPerformActions 
                      ? "It's your turn! Make your move."
                      : "Please wait for your turn."}
                  </Alert>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Properties card */}
          <Grid item xs={12} md={4}>
            <Card 
              elevation={0} 
              sx={{ 
                borderRadius: 3,
                height: '100%',
                boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Your Properties
                </Typography>
                
                {/* Placeholder for properties */}
                <Box 
                  sx={{ 
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: 250,
                    border: '1px dashed',
                    borderColor: 'divider',
                    borderRadius: 2,
                    p: 3,
                    mt: 3
                  }}
                >
                  <HomeIcon sx={{ fontSize: 40, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="body1" align="center" color="text.secondary">
                    No properties owned yet
                  </Typography>
                  <Typography variant="body2" align="center" color="text.disabled" sx={{ mt: 1 }}>
                    Properties you purchase will appear here
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Game log (full width) */}
          <Grid item xs={12}>
            <Card 
              elevation={0} 
              sx={{ 
                borderRadius: 3,
                boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Game Log
                </Typography>
                
                <Box 
                  sx={{ 
                    borderRadius: 2,
                    bgcolor: '#f9f9f9',
                    p: 2,
                    maxHeight: 150,
                    overflowY: 'auto',
                    mt: 2
                  }}
                >
                  <Typography variant="body2" color="text.secondary" fontFamily="monospace">
                    Waiting for game events...
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default PlayerPage; 