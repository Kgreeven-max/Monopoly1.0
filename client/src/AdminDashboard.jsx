import React from 'react';
import { Box, Typography, Container, Paper, Button, Alert } from '@mui/material';
import { useAuth } from './contexts/AuthContext'; // To check if user is admin
import { useGame } from './contexts/GameContext'; // To check game status
import { useSocket } from './contexts/SocketContext'; // To emit start_game

function AdminDashboard() {
  const { user, adminKey } = useAuth(); // Assuming adminKey is added to AuthContext
  const { gameState } = useGame();
  const { emit } = useSocket();
  const [error, setError] = React.useState(null);
  const [success, setSuccess] = React.useState(null);

  const handleStartGame = () => {
    setError(null);
    setSuccess(null);
    console.log("[AdminDashboard] Attempting to start game with key...");
    if (!adminKey) {
        setError('Admin key not found. Cannot start game.');
        console.error('[AdminDashboard] Admin key missing in AuthContext.');
        return;
    }
    emit('start_game', { admin_key: adminKey });
    // Listen for 'start_game_initiated' or 'game_error' to provide feedback?
    // For now, just assume it works or rely on game state update.
    setSuccess('Start game command sent.'); // Basic feedback
  };

  // Check if user has admin role AND the admin key is present
  const isAdmin = user?.role === 'admin' && adminKey;

  if (!isAdmin) {
    // Optional: Could redirect using useNavigate() instead of just showing an error
    return (
      <Container maxWidth="sm" sx={{ mt: 5 }}>
        <Alert severity="error">Access Denied. You must be logged in as an administrator.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6">Game Control</Typography>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
        <Box sx={{ mt: 2 }}>
          <Typography>Current Game Status: <strong>{gameState?.status || 'Loading...'}</strong></Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleStartGame}
            disabled={gameState?.status !== 'Waiting'} // Only allow starting if game is Waiting
            sx={{ mt: 2 }}
          >
            Start Game
          </Button>
          {gameState?.status !== 'Waiting' && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Game can only be started when its status is 'Waiting'.
            </Typography>
          )}
        </Box>

        {/* Add other admin controls here later */}
        <Typography variant="h6" sx={{ mt: 4 }}>Player Management</Typography>
        <Typography>Player list and management features coming soon...</Typography>

        <Typography variant="h6" sx={{ mt: 4 }}>Game Settings</Typography>
        <Typography>Game configuration options coming soon...</Typography>

      </Paper>
    </Container>
  );
}

export default AdminDashboard;
