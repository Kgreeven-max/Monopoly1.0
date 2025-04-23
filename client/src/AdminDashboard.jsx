import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Container, Paper, Button, Alert, Stepper,
  Step, StepLabel, TextField, FormControl, FormControlLabel,
  InputLabel, Select, MenuItem, Switch, Divider, Grid, 
  Card, CardContent, List, ListItem, ListItemText, ListItemSecondaryAction,
  IconButton, CircularProgress
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import VideoGameAssetIcon from '@mui/icons-material/VideoGameAsset';
import { useAuth } from './contexts/AuthContext';
import { useGame } from './contexts/GameContext';
import { useSocket } from './contexts/SocketContext';

function AdminDashboard() {
  const { user, adminKey } = useAuth();
  const { gameState, updateGameState } = useGame();
  const { socket, emit } = useSocket();
  
  // State for the stepper
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Game creation state
  const [gameId, setGameId] = useState(null);
  const [gameConfig, setGameConfig] = useState({
    difficulty: 'normal',
    mode: 'classic',
    lap_limit: 0,
    free_parking_fund: true,
    auction_required: true,
    turn_timeout: 60
  });
  
  // Player state
  const [players, setPlayers] = useState([]);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [botConfig, setBotConfig] = useState({
    botType: 'conservative',
    difficulty: 'normal'
  });

  // Steps in our game setup process
  const steps = ['Create New Game', 'Add Players', 'Start Game'];

  // Listen for socket events
  useEffect(() => {
    if (socket) {
      socket.on('game_created', handleGameCreated);
      socket.on('player_added', handlePlayerAdded);
      socket.on('player_removed', handlePlayerRemoved);
      socket.on('game_started', handleGameStarted);
      socket.on('game_error', handleGameError);
      
      return () => {
        socket.off('game_created');
        socket.off('player_added');
        socket.off('player_removed');
        socket.off('game_started');
        socket.off('game_error');
      };
    }
  }, [socket]);

  // Socket event handlers
  const handleGameCreated = (data) => {
    setLoading(false);
    if (data.success) {
      setGameId(data.game_id);
      setSuccess('Game created successfully!');
      setActiveStep(1); // Move to player setup
    } else {
      setError(`Failed to create game: ${data.error}`);
    }
  };

  const handlePlayerAdded = (data) => {
    setLoading(false);
    if (data.success) {
      setPlayers(prevPlayers => [
        ...prevPlayers, 
        { id: data.player_id, name: data.player_name, isBot: data.is_bot }
      ]);
      setNewPlayerName('');
      setSuccess(`Player ${data.player_name} added successfully!`);
    } else {
      setError(`Failed to add player: ${data.error}`);
    }
  };

  const handlePlayerRemoved = (data) => {
    setLoading(false);
    if (data.success) {
      setPlayers(prevPlayers => prevPlayers.filter(p => p.id !== data.player_id));
      setSuccess(`Player removed successfully!`);
    } else {
      setError(`Failed to remove player: ${data.error}`);
    }
  };

  const handleGameStarted = (data) => {
    setLoading(false);
    setSuccess('Game started successfully!');
    // Update game state or redirect to game board
    if (updateGameState) {
      updateGameState(data);
    }
    setActiveStep(3); // Move past the final step
  };

  const handleGameError = (data) => {
    setLoading(false);
    setError(`Game error: ${data.error}`);
  };

  // Action handlers
  const handleCreateGame = () => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    if (!adminKey) {
      setError('Admin key not found. Cannot create game.');
      setLoading(false);
      return;
    }

    // Using socket.io for real-time feedback
    emit('create_game', { 
      admin_key: adminKey,
      ...gameConfig
    });

    // Alternative REST API approach
    /*
    fetch('/api/game/new', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Key': adminKey 
      },
      body: JSON.stringify(gameConfig)
    })
    .then(response => response.json())
    .then(data => {
      setLoading(false);
      if (data.success) {
        setGameId(data.game_id);
        setSuccess('Game created successfully!');
        setActiveStep(1); // Move to player setup
      } else {
        setError(`Failed to create game: ${data.error}`);
      }
    })
    .catch(err => {
      setLoading(false);
      setError(`Error creating game: ${err.message}`);
    });
    */
  };

  const handleAddHumanPlayer = () => {
    if (!newPlayerName.trim()) {
      setError('Please enter a player name');
      return;
    }
    
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    emit('add_player', {
      admin_key: adminKey,
      game_id: gameId,
      username: newPlayerName,
      is_bot: false
    });
  };

  const handleAddBotPlayer = () => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    emit('add_bot', {
      admin_key: adminKey,
      game_id: gameId,
      type: botConfig.botType,
      difficulty: botConfig.difficulty
    });
  };

  const handleRemovePlayer = (playerId) => {
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    emit('remove_player', {
      admin_key: adminKey,
      game_id: gameId,
      player_id: playerId
    });
  };

  const handleStartGame = () => {
    if (players.length < 2) {
      setError('Need at least 2 players to start the game');
      return;
    }
    
    setError(null);
    setSuccess(null);
    setLoading(true);
    
    emit('start_game', { 
      admin_key: adminKey,
      game_id: gameId 
    });
  };

  // Handle form field changes
  const handleConfigChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setGameConfig({ ...gameConfig, [field]: value });
  };

  const handleBotConfigChange = (field) => (event) => {
    setBotConfig({ ...botConfig, [field]: event.target.value });
  };

  // Navigation between steps
  const handleNext = () => {
    if (activeStep === 0) {
      handleCreateGame();
    } else if (activeStep === 2) {
      handleStartGame();
    } else {
      setActiveStep((prevStep) => prevStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  // Check if user has admin role AND the admin key is present
  const isAdmin = user?.role === 'admin' && adminKey;

  if (!isAdmin) {
    return (
      <Container maxWidth="sm" sx={{ mt: 5 }}>
        <Alert severity="error">Access Denied. You must be logged in as an administrator.</Alert>
      </Container>
    );
  }

  // Render content based on current step
  const getStepContent = (step) => {
    switch (step) {
      case 0: // Create New Game
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Game Configuration
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Game Mode</InputLabel>
                  <Select
                    value={gameConfig.mode}
                    onChange={handleConfigChange('mode')}
                    label="Game Mode"
                  >
                    <MenuItem value="classic">Classic Mode</MenuItem>
                    <MenuItem value="speed">Speed Mode</MenuItem>
                    <MenuItem value="tycoon">Tycoon Mode</MenuItem>
                    <MenuItem value="market_crash">Market Crash Mode</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={gameConfig.difficulty}
                    onChange={handleConfigChange('difficulty')}
                    label="Difficulty"
                  >
                    <MenuItem value="easy">Easy</MenuItem>
                    <MenuItem value="normal">Normal</MenuItem>
                    <MenuItem value="hard">Hard</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Lap Limit (0 for unlimited)"
                  type="number"
                  margin="normal"
                  value={gameConfig.lap_limit}
                  onChange={handleConfigChange('lap_limit')}
                  inputProps={{ min: 0 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Turn Timeout (seconds)"
                  type="number"
                  margin="normal"
                  value={gameConfig.turn_timeout}
                  onChange={handleConfigChange('turn_timeout')}
                  inputProps={{ min: 0 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={gameConfig.free_parking_fund}
                      onChange={handleConfigChange('free_parking_fund')}
                    />
                  }
                  label="Free Parking Fund"
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={gameConfig.auction_required}
                      onChange={handleConfigChange('auction_required')}
                    />
                  }
                  label="Require Auctions for Declined Properties"
                  margin="normal"
                />
              </Grid>
            </Grid>
          </Box>
        );
      
      case 1: // Add Players
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Player Management
            </Typography>
            
            <Grid container spacing={3}>
              {/* Add Human Player */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">Add Human Player</Typography>
                    <Box sx={{ display: 'flex', mt: 2 }}>
                      <TextField
                        fullWidth
                        label="Player Name"
                        value={newPlayerName}
                        onChange={(e) => setNewPlayerName(e.target.value)}
                        margin="normal"
                      />
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<PersonAddIcon />}
                        onClick={handleAddHumanPlayer}
                        sx={{ ml: 1, mt: 2 }}
                      >
                        Add
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              
              {/* Add Bot Player */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6">Add Bot Player</Typography>
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Bot Type</InputLabel>
                      <Select
                        value={botConfig.botType}
                        onChange={handleBotConfigChange('botType')}
                        label="Bot Type"
                      >
                        <MenuItem value="conservative">Conservative</MenuItem>
                        <MenuItem value="aggressive">Aggressive</MenuItem>
                        <MenuItem value="strategic">Strategic</MenuItem>
                      </Select>
                    </FormControl>
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Bot Difficulty</InputLabel>
                      <Select
                        value={botConfig.difficulty}
                        onChange={handleBotConfigChange('difficulty')}
                        label="Bot Difficulty"
                      >
                        <MenuItem value="easy">Easy</MenuItem>
                        <MenuItem value="normal">Normal</MenuItem>
                        <MenuItem value="hard">Hard</MenuItem>
                      </Select>
                    </FormControl>
                    <Button
                      fullWidth
                      variant="contained"
                      color="secondary"
                      startIcon={<VideoGameAssetIcon />}
                      onClick={handleAddBotPlayer}
                      sx={{ mt: 2 }}
                    >
                      Add Bot
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6">Current Players ({players.length})</Typography>
              {players.length === 0 ? (
                <Alert severity="info" sx={{ mt: 1 }}>No players added yet. Add at least 2 players to start the game.</Alert>
              ) : (
                <List>
                  {players.map((player) => (
                    <ListItem key={player.id} sx={{ borderBottom: '1px solid #eee' }}>
                      <ListItemText 
                        primary={player.name} 
                        secondary={player.isBot ? 'Bot Player' : 'Human Player'} 
                      />
                      <ListItemSecondaryAction>
                        <IconButton edge="end" onClick={() => handleRemovePlayer(player.id)}>
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </Box>
        );
      
      case 2: // Review & Start
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Game Review
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Game Settings</Typography>
                    <Typography><strong>Game Mode:</strong> {gameConfig.mode}</Typography>
                    <Typography><strong>Difficulty:</strong> {gameConfig.difficulty}</Typography>
                    <Typography><strong>Lap Limit:</strong> {gameConfig.lap_limit > 0 ? gameConfig.lap_limit : 'Unlimited'}</Typography>
                    <Typography><strong>Turn Timeout:</strong> {gameConfig.turn_timeout} seconds</Typography>
                    <Typography><strong>Free Parking Fund:</strong> {gameConfig.free_parking_fund ? 'Enabled' : 'Disabled'}</Typography>
                    <Typography><strong>Required Auctions:</strong> {gameConfig.auction_required ? 'Enabled' : 'Disabled'}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Players ({players.length})</Typography>
                    {players.length === 0 ? (
                      <Alert severity="warning">No players added!</Alert>
                    ) : (
                      <List dense>
                        {players.map((player) => (
                          <ListItem key={player.id}>
                            <ListItemText 
                              primary={player.name} 
                              secondary={player.isBot ? 'Bot Player' : 'Human Player'} 
                            />
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            <Alert severity="info" sx={{ mt: 3 }}>
              Ready to start the game? Make sure you have at least 2 players added.
              Once started, the game will initialize with these settings and players.
            </Alert>
          </Box>
        );
        
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard - Game Setup
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        {activeStep === steps.length ? (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success">
              Game successfully started! Redirecting to game board...
            </Alert>
          </Box>
        ) : (
          <>
            {getStepContent(activeStep)}
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                variant="outlined"
                disabled={activeStep === 0 || loading}
                onClick={handleBack}
              >
                Back
              </Button>
              <Box sx={{ position: 'relative' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleNext}
                  disabled={loading || (activeStep === 1 && players.length < 2)}
                >
                  {activeStep === steps.length - 1 ? 'Start Game' : 'Next'}
                </Button>
                {loading && (
                  <CircularProgress
                    size={24}
                    sx={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      marginTop: '-12px',
                      marginLeft: '-12px',
                    }}
                  />
                )}
              </Box>
            </Box>
          </>
        )}
      </Paper>
    </Container>
  );
}

export default AdminDashboard;
