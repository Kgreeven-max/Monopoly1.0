import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Import MUI components
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import FormHelperText from '@mui/material/FormHelperText';

// Helper component for Tab Panels
function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const HomePage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [username, setUsername] = useState('');
  const [pin, setPin] = useState('');
  const [adminKeyInput, setAdminKeyInput] = useState(''); // New state for admin key input
  const [playerId, setPlayerId] = useState(''); // For login
  const [displayKey, setDisplayKey] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  const { registerPlayer, loginPlayer, loginAdmin, initializeDisplay, error, loading, user } = useAuth();
  const navigate = useNavigate();

  // Clear messages when tab changes
  useEffect(() => {
    setLocalError(null);
    setSuccessMessage(null);
  }, [tabValue]);

  // Redirect if user is already logged in (from AuthContext state)
  useEffect(() => {
    if (user?.role === 'player') {
      navigate(`/player/${user.id}`);
    } else if (user?.role === 'admin') {
      navigate('/admin');
    }
  }, [user, navigate]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleJoinGame = async (e) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);
    if (!username || !pin) {
        setLocalError('Username and PIN are required to join.');
        return;
    }
    const result = await registerPlayer(username, pin); 
    if (result.success) {
      setSuccessMessage('Registration successful! Redirecting...');
      // Navigation is handled by useEffect watching `user` state
    } else {
      setLocalError(result.error || 'Registration failed.');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);
    if (!username || !pin) {
        setLocalError('Username and PIN are required to log in.');
        return;
    }
    const result = await loginPlayer(username, pin);
    if (result.success) {
        setSuccessMessage('Login successful! Redirecting...');
       // Navigation is handled by useEffect watching `user` state
    } else {
        setLocalError(result.error || 'Login failed.');
    }
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);
    if (!adminKeyInput) {
        setLocalError('Admin Key is required.');
        return;
    }
    const result = await loginAdmin(adminKeyInput);
    if (result.success) {
        setSuccessMessage('Admin login successful! Redirecting...');
        // Navigation is handled by useEffect watching `user` state
    } else {
        setLocalError(result.error || 'Admin login failed.');
    }
  };

  const handleInitializeDisplay = async (e) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);
    if (!displayKey) {
        setLocalError('Display Key is required.');
        return;
    }
    const result = await initializeDisplay(displayKey);
    if (result.success) {
        setSuccessMessage('Display initialized! Redirecting...');
    } else {
        setLocalError(result.error || 'Display initialization failed.');
    }
  };

  // Prioritize localError over context error for immediate feedback
  const displayError = localError || error;

  return (
    <Container component="main" maxWidth="xs" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: '100vh', justifyContent: 'center', py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h4" gutterBottom sx={{ mb: 1 }}>
          Pi-nopoly
        </Typography>
        <Typography component="p" variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
          A modern take on the classic board game
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider', width: '100%', mb: 2 }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Login/Register Tabs" centered variant="fullWidth">
            <Tab label="Join / Register" />
            <Tab label="Return" />
            <Tab label="Admin" />
            <Tab label="Display" />
          </Tabs>
        </Box>

        {/* Display error or success messages */} 
        {displayError && <Alert severity="error" sx={{ width: '100%', mb: 2 }}>{displayError}</Alert>}
        {successMessage && <Alert severity="success" sx={{ width: '100%', mb: 2 }}>{successMessage}</Alert>}

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <Typography component="h1" variant="h5" align="center">Join New Game</Typography>
          <Box component="form" onSubmit={handleJoinGame} noValidate sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="join-username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="pin"
              label="PIN (4-digits)"
              type="password"
              id="join-pin"
              autoComplete="current-password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              inputProps={{ maxLength: 4, pattern: "[0-9]*" }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Join Game'}
            </Button>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography component="h1" variant="h5" align="center">Player Login</Typography>
          <Box component="form" onSubmit={handleLogin} noValidate sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="login-username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="pin"
              label="PIN"
              type="password"
              id="login-pin"
              autoComplete="current-password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Login'}
            </Button>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography component="h1" variant="h5" align="center">Admin Login</Typography>
          <Box component="form" onSubmit={handleAdminLogin} noValidate sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              name="adminKey"
              label="Admin Key"
              type="password"
              id="admin-key"
              value={adminKeyInput}
              onChange={(e) => setAdminKeyInput(e.target.value)}
              autoFocus
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="secondary"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Admin Login'}
            </Button>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography component="h1" variant="h5" align="center">TV Display</Typography>
          <Box component="form" onSubmit={handleInitializeDisplay} noValidate sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="display-key"
              label="Display Key"
              name="displayKey"
              type="password"
              value={displayKey}
              onChange={(e) => setDisplayKey(e.target.value)}
              autoFocus
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Initialize Display'}
            </Button>
          </Box>
        </TabPanel>

      </Paper>
       <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 5 }}>
         Pi-nopoly &copy; {new Date().getFullYear()}
       </Typography>
    </Container>
  );
};

export default HomePage; 