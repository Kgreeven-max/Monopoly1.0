import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Button, Grid, List, ListItem, ListItemText, Divider, Alert } from '@mui/material';
import { useGame } from '../contexts/GameContext';
import { useSocket } from '../contexts/SocketContext';
import NavBar from '../components/NavBar';

export default function DebugPage() {
  const { gameState } = useGame();
  const { socket, emit, isConnected, connectionError, reconnectAttempts } = useSocket();
  const [playerHistory, setPlayerHistory] = useState({});
  const [cardHistory, setCardHistory] = useState([]);
  const [socketEvents, setSocketEvents] = useState([]);
  
  // Track the real-time player positions and movement history
  useEffect(() => {
    if (gameState.players && gameState.players.length > 0) {
      // Update our player history with the new positions
      const newHistory = { ...playerHistory };
      
      gameState.players.forEach(player => {
        if (!newHistory[player.id]) {
          newHistory[player.id] = {
            positions: [player.position],
            timestamps: [new Date().toISOString()],
            lastUpdate: new Date(),
          };
        } else if (newHistory[player.id].positions[newHistory[player.id].positions.length - 1] !== player.position) {
          // Position changed, record the new position
          newHistory[player.id].positions.push(player.position);
          newHistory[player.id].timestamps.push(new Date().toISOString());
          newHistory[player.id].lastUpdate = new Date();
        }
      });
      
      setPlayerHistory(newHistory);
    }
  }, [gameState.players]);
  
  // Track card draws
  useEffect(() => {
    if (gameState.lastCardDrawn && 
        (!cardHistory.length || 
         cardHistory[0].timestamp !== gameState.lastCardDrawn.timestamp)) {
      
      setCardHistory([
        {
          ...gameState.lastCardDrawn,
          timestamp: new Date().toISOString()
        },
        ...cardHistory.slice(0, 9) // Keep last 10 cards
      ]);
    }
  }, [gameState.lastCardDrawn]);

  // Track socket events
  useEffect(() => {
    if (socket) {
      const logEvent = (event, data) => {
        console.log(`[DebugPage] Socket event: ${event}`, data);
        setSocketEvents(prev => [{
          event,
          data: JSON.stringify(data || {}),
          timestamp: new Date().toISOString()
        }, ...prev.slice(0, 9)]);
      };

      const events = [
        'game_state_update', 
        'player_moved', 
        'dice_rolled',
        'turn_changed',
        'card_drawn',
        'community_chest_card_drawn',
        'chance_card_drawn'
      ];

      // Set up listeners for debugging
      events.forEach(event => {
        socket.on(event, (data) => logEvent(event, data));
      });

      return () => {
        // Clean up listeners
        events.forEach(event => {
          socket.off(event);
        });
      };
    }
  }, [socket]);
  
  // Request game state on component mount
  useEffect(() => {
    if (isConnected) {
      console.log('[DebugPage] Requesting game state');
      emit('request_game_state');
    }
  }, [isConnected, emit]);
  
  // Force refresh game state on button click
  const handleRefresh = () => {
    if (isConnected) {
      console.log('[DebugPage] Manually refreshing game state');
      emit('request_game_state');
    }
  };

  // Force reconnect socket
  const handleReconnect = () => {
    // Import the connectSocket function directly to avoid circular dependencies
    const { connectSocket } = useSocket();
    console.log('[DebugPage] Forcing socket reconnection');
    connectSocket({
      path: '/ws/socket.io',
      transports: ['websocket', 'polling'],
      forceNew: true
    });
  };
  
  return (
    <>
      <NavBar />
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Game State Debug Page
        </Typography>
        
        {/* Socket connection status */}
        {isConnected ? (
          <Alert severity="success" sx={{ mb: 2 }}>
            Socket connected successfully
          </Alert>
        ) : (
          <Alert severity="error" sx={{ mb: 2 }}>
            Socket disconnected: {connectionError || 'Unknown error'} (Reconnect attempts: {reconnectAttempts})
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button 
            variant="contained" 
            onClick={handleRefresh}
            disabled={!isConnected}
          >
            Refresh Game State
          </Button>
          
          <Button 
            variant="outlined"
            onClick={handleReconnect}
            color="warning"
          >
            Force Reconnect Socket
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Current Game State
              </Typography>
              <Typography variant="body2">
                Game ID: {gameState.gameId || 'Not available'}
              </Typography>
              <Typography variant="body2">
                Status: {gameState.status || 'Not available'}
              </Typography>
              <Typography variant="body2">
                Current Player: {gameState.players?.find(p => p.id === gameState.currentPlayerId)?.username || 'None'} (ID: {gameState.currentPlayerId || 'None'})
              </Typography>
              <Typography variant="body2">
                Turn: {gameState.currentTurn || 0}
              </Typography>
            </Paper>
            
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Player Positions
              </Typography>
              {gameState.players?.length > 0 ? (
                <List>
                  {gameState.players?.map(player => (
                    <ListItem key={player.id} divider>
                      <ListItemText
                        primary={`${player.username || `Player ${player.id}`} ${player.is_bot ? '(Bot)' : ''}`}
                        secondary={`Position: ${player.position} | Money: $${player.money}`}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2">No players available</Typography>
              )}
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Socket Events
              </Typography>
              {socketEvents.length === 0 ? (
                <Typography variant="body2">No socket events captured yet</Typography>
              ) : (
                <List sx={{ maxHeight: '200px', overflow: 'auto' }}>
                  {socketEvents.map((event, index) => (
                    <ListItem key={index} divider>
                      <ListItemText
                        primary={event.event}
                        secondary={`${new Date(event.timestamp).toLocaleTimeString()} - ${event.data.substring(0, 100)}${event.data.length > 100 ? '...' : ''}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Player Movement History
              </Typography>
              {Object.entries(playerHistory).length > 0 ? (
                Object.entries(playerHistory).map(([playerId, history]) => (
                  <Box key={playerId} sx={{ mb: 2 }}>
                    <Typography variant="subtitle1">
                      {gameState.players?.find(p => p.id === parseInt(playerId))?.username || `Player ${playerId}`}
                    </Typography>
                    <Typography variant="body2">
                      Last update: {new Date(history.lastUpdate).toLocaleTimeString()}
                    </Typography>
                    <Typography variant="body2">
                      Moves: {history.positions.length - 1}
                    </Typography>
                    <Typography variant="body2">
                      Position history: {history.positions.join(' → ')}
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                  </Box>
                ))
              ) : (
                <Typography variant="body2">No movement history available</Typography>
              )}
            </Paper>
            
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Card Draw History
              </Typography>
              {cardHistory.length === 0 ? (
                <Typography variant="body2">No cards drawn yet</Typography>
              ) : (
                <List>
                  {cardHistory.map((card, index) => (
                    <ListItem key={index} divider>
                      <ListItemText
                        primary={`${card.cardType || 'Card'}: ${card.card?.title || card.card?.description || 'Unknown Card'}`}
                        secondary={`Drawn by: ${gameState.players?.find(p => p.id === card.player_id)?.username || `Player ${card.player_id}`} at ${new Date(card.timestamp).toLocaleTimeString()}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </>
  );
} 