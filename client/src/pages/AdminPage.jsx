import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  TextField, 
  Grid, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemAvatar, 
  Avatar, 
  IconButton, 
  Divider,
  Snackbar,
  Alert,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import io from 'socket.io-client';

function AdminPage() {
  const [adminPin, setAdminPin] = useState('');
  const [authenticated, setAuthenticated] = useState(false);
  const [players, setPlayers] = useState([]);
  const [socket, setSocket] = useState(null);
  const [gameState, setGameState] = useState({
    gameId: null,
    gameStarted: false,
    economicState: 'normal',
    inflation: 1.0,
    currentPlayerId: null
  });
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [newBotName, setNewBotName] = useState('');
  const [botType, setBotType] = useState('conservative');
  const [difficulty, setDifficulty] = useState('medium');
  
  const navigate = useNavigate();

  // Connect to socket
  useEffect(() => {
    const newSocket = io(import.meta.env.VITE_API_URL || 'http://localhost:5001', {
      path: "/ws",
      reconnectionDelayMax: 10000,
      transports: ['websocket']
    });
    
    setSocket(newSocket);

    // Connection events
    newSocket.on('connect', () => {
      console.log('Admin connected to game server');
      // If already authenticated, request player list
      if (authenticated) {
        requestPlayerList();
      }
    });

    newSocket.on('disconnect', () => {
      console.log('Admin disconnected from game server');
      showNotification('Disconnected from server', 'error');
    });

    newSocket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      showNotification(`Connection error: ${error.message}`, 'error');
    });

    // Event handlers
    newSocket.on('all_players_list', handlePlayerListUpdate);
    newSocket.on('game_started', handleGameStarted);
    newSocket.on('game_state', handleGameState);
    newSocket.on('bot_event', handleBotEvent);
    newSocket.on('player_removed', handlePlayerRemoved);
    newSocket.on('player_update', handlePlayerUpdate);
    newSocket.on('auth_error', handleAuthError);

    return () => {
      if (newSocket) {
        newSocket.off('all_players_list', handlePlayerListUpdate);
        newSocket.off('game_started', handleGameStarted);
        newSocket.off('game_state', handleGameState);
        newSocket.off('bot_event', handleBotEvent);
        newSocket.off('player_removed', handlePlayerRemoved);
        newSocket.off('player_update', handlePlayerUpdate);
        newSocket.off('auth_error', handleAuthError);
        newSocket.disconnect();
      }
    };
  }, [authenticated]);

  // Event handlers
  const handlePlayerListUpdate = (data) => {
    if (data.success && data.players) {
      console.log('Received player list:', data.players);
      setPlayers(data.players);
    } else {
      console.error('Failed to get player list:', data.error);
      showNotification(`Failed to get player list: ${data.error}`, 'error');
    }
  };

  const handleGameStarted = (data) => {
    console.log('Game started:', data);
    if (data.success) {
      setGameState(prevState => ({
        ...prevState,
        gameId: data.game_id || data.gameId,
        gameStarted: true
      }));
      showNotification('Game started successfully!', 'success');
    } else {
      showNotification(`Failed to start game: ${data.error}`, 'error');
    }
  };

  const handleGameState = (data) => {
    console.log('Game state update:', data);
    setGameState({
      gameId: data.gameId || gameState.gameId,
      gameStarted: data.gameStarted !== undefined ? data.gameStarted : gameState.gameStarted,
      economicState: data.economicState || gameState.economicState,
      inflation: data.inflation || gameState.inflation,
      currentPlayerId: data.currentPlayerId || gameState.currentPlayerId
    });
  };

  const handleBotEvent = (data) => {
    console.log('Bot event:', data);
    if (data.success) {
      showNotification(`Bot ${data.bot.name} created successfully!`, 'success');
      // Request updated player list
      requestPlayerList();
    } else {
      showNotification(`Error creating bot: ${data.error}`, 'error');
    }
  };

  const handlePlayerRemoved = (data) => {
    console.log('Player removed:', data);
    showNotification(`Player ${data.name} removed from the game`, 'info');
    // Update player list
    requestPlayerList();
  };

  const handlePlayerUpdate = (data) => {
    console.log('Player updated:', data);
    // Request updated player list to get the latest state
    requestPlayerList();
  };

  const handleAuthError = (data) => {
    console.error('Authentication error:', data);
    showNotification(`Authentication error: ${data.error}`, 'error');
    setAuthenticated(false);
  };

  // Utility functions
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  // Admin actions
  const authenticate = () => {
    if (!adminPin.trim()) {
      showNotification('Please enter an admin PIN', 'warning');
      return;
    }

    // Store the pin for future use
    localStorage.setItem('adminPin', adminPin);
    setAuthenticated(true);
    requestPlayerList();
    requestGameState();
  };

  const requestPlayerList = () => {
    if (!socket) return;
    
    socket.emit('get_all_players', { admin_pin: adminPin });
    console.log('Requested player list');
  };

  const requestGameState = () => {
    if (!socket) return;
    
    socket.emit('admin_request_game_state', { admin_pin: adminPin });
    console.log('Requested game state');
  };

  const startGame = () => {
    if (!socket) return;
    
    socket.emit('start_game', { admin_pin: adminPin });
    console.log('Requested game start');
  };

  const resetGame = () => {
    if (!socket) return;
    
    socket.emit('reset_game', { admin_pin: adminPin });
    console.log('Requested game reset');
    showNotification('Game reset requested', 'info');
  };

  const removePlayer = (playerId) => {
    if (!socket) return;
    
    socket.emit('remove_player', { 
      admin_pin: adminPin,
      player_id: playerId
    });
    console.log('Requested player removal:', playerId);
  };

  const createBot = () => {
    if (!socket || !newBotName.trim()) return;
    
    socket.emit('create_bot', {
      admin_pin: adminPin,
      name: newBotName,
      type: botType,
      difficulty: difficulty
    });
    
    console.log('Requested bot creation:', { name: newBotName, type: botType, difficulty });
    // Clear the form
    setNewBotName('');
  };

  const viewBoard = () => {
    // Navigate to the board page
    navigate('/board');
  };

  // Render content based on authentication
  if (!authenticated) {
    return (
      <Box sx={{ p: 4, maxWidth: '500px', mx: 'auto', mt: 4 }}>
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
          <Typography variant="h4" gutterBottom align="center">
            Admin Login
          </Typography>
          <Typography variant="body2" gutterBottom align="center" color="text.secondary">
            Enter your admin PIN to access the game controls
          </Typography>
          <Box sx={{ mt: 3 }}>
            <TextField
              fullWidth
              label="Admin PIN"
              type="password"
              variant="outlined"
              value={adminPin}
              onChange={(e) => setAdminPin(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button
              fullWidth
              variant="contained"
              color="primary"
              onClick={authenticate}
              sx={{ py: 1.5 }}
            >
              Login
            </Button>
          </Box>
        </Paper>
        <Snackbar
          open={notification.open}
          autoHideDuration={6000}
          onClose={handleCloseNotification}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseNotification} severity={notification.severity}>
            {notification.message}
          </Alert>
        </Snackbar>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Admin Panel
      </Typography>
      
      <Grid container spacing={3}>
        {/* Game Control Panel */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Game Controls
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={startGame}
                disabled={gameState.gameStarted}
              >
                {gameState.gameStarted ? 'Game Already Started' : 'Start Game'}
              </Button>
              
              <Button 
                variant="contained"
                color="secondary"
                onClick={viewBoard}
              >
                View Game Board
              </Button>
              
              <Button 
                variant="outlined" 
                color="error" 
                onClick={resetGame}
              >
                Reset Game
              </Button>
            </Box>
            
            {/* Game State Display */}
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Current Game State
              </Typography>
              <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
                <Typography variant="body2">
                  <strong>Game ID:</strong> {gameState.gameId || 'No active game'}
                </Typography>
                <Typography variant="body2">
                  <strong>Status:</strong> {gameState.gameStarted ? 'Running' : 'Not Started'}
                </Typography>
                <Typography variant="body2">
                  <strong>Economy:</strong> {gameState.economicState.charAt(0).toUpperCase() + gameState.economicState.slice(1)}
                </Typography>
                <Typography variant="body2">
                  <strong>Inflation:</strong> {(gameState.inflation * 100).toFixed(1)}%
                </Typography>
                <Typography variant="body2">
                  <strong>Current Player:</strong> {gameState.currentPlayerId || 'None'}
                </Typography>
              </Box>
            </Box>
          </Paper>
          
          {/* Bot Creation */}
          <Paper elevation={2} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Create Bot
            </Typography>
            <TextField
              fullWidth
              label="Bot Name"
              variant="outlined"
              value={newBotName}
              onChange={(e) => setNewBotName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <TextField
                  select
                  fullWidth
                  label="Bot Type"
                  value={botType}
                  onChange={(e) => setBotType(e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="conservative">Conservative</option>
                  <option value="aggressive">Aggressive</option>
                  <option value="strategic">Strategic</option>
                  <option value="opportunistic">Opportunistic</option>
                </TextField>
              </Grid>
              <Grid item xs={6}>
                <TextField
                  select
                  fullWidth
                  label="Difficulty"
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  SelectProps={{
                    native: true,
                  }}
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </TextField>
              </Grid>
            </Grid>
            <Button 
              fullWidth 
              variant="contained" 
              color="success" 
              onClick={createBot}
            >
              Create Bot
            </Button>
          </Paper>
        </Grid>
        
        {/* Player List */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Players {players.length > 0 ? `(${players.length})` : ''}
              </Typography>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={requestPlayerList}
              >
                Refresh
              </Button>
            </Box>
            
            {players.length > 0 ? (
              <List sx={{ maxHeight: '500px', overflow: 'auto' }}>
                {players.map((player, index) => (
                  <React.Fragment key={player.id}>
                    {index > 0 && <Divider component="li" />}
                    <ListItem
                      secondaryAction={
                        <Button 
                          size="small" 
                          color="error" 
                          variant="outlined"
                          onClick={() => removePlayer(player.id)}
                        >
                          Remove
                        </Button>
                      }
                    >
                      <ListItemAvatar>
                        <Avatar 
                          sx={{ 
                            bgcolor: player.is_bot ? '#90CAF9' : '#81C784',
                            color: '#fff'
                          }}
                        >
                          {player.is_bot ? 'B' : 'P'}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText 
                        primary={
                          <Typography variant="body1">
                            {player.name} 
                            {player.is_bot && <Typography component="span" variant="caption" sx={{ ml: 1, bgcolor: '#E3F2FD', px: 1, py: 0.5, borderRadius: 1 }}>Bot</Typography>}
                            {player.id === gameState.currentPlayerId && (
                              <Typography component="span" variant="caption" sx={{ ml: 1, bgcolor: '#FFF9C4', px: 1, py: 0.5, borderRadius: 1 }}>Current</Typography>
                            )}
                          </Typography>
                        }
                        secondary={
                          <React.Fragment>
                            <Typography component="span" variant="body2" color="text.primary">
                              ${player.money}
                            </Typography>
                            {' — '}
                            <Typography component="span" variant="body2">
                              Position: {player.position}
                              {player.in_jail && ' (In Jail)'}
                            </Typography>
                          </React.Fragment>
                        }
                      />
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No players found
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default AdminPage; 