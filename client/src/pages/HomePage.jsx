import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Container,
  Box,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Fade,
  Grid,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import MonitorIcon from '@mui/icons-material/Monitor';

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
        <Fade in={value === index}>
          <Box sx={{ p: 3 }}>
            {children}
          </Box>
        </Fade>
      )}
    </div>
  );
}

const HomePage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [username, setUsername] = useState('');
  const [pin, setPin] = useState('');
  const [adminKeyInput, setAdminKeyInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  const { registerPlayer, loginPlayer, loginAdmin, initializeDisplay, error, loading, user } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Clear messages when tab changes
  useEffect(() => {
    setLocalError(null);
    setSuccessMessage(null);
  }, [tabValue]);

  // Redirect if user is already logged in
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
    setIsLoading(true);
    const result = await registerPlayer(username, pin); 
    setIsLoading(false);
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
    setIsLoading(true);
    const result = await loginPlayer(username, pin);
    setIsLoading(false);
    if (result.success) {
        setSuccessMessage('Login successful! Redirecting...');
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
    setIsLoading(true);
    const result = await loginAdmin(adminKeyInput);
    setIsLoading(false);
    if (result.success) {
        setSuccessMessage('Admin login successful! Redirecting...');
    } else {
        setLocalError(result.error || 'Admin login failed.');
    }
  };

  const handleInitializeDisplay = async (e) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);
    setIsLoading(true);
    const result = await initializeDisplay();
    setIsLoading(false);
    if (result.success) {
        setSuccessMessage('Display initialized! Redirecting...');
    } else {
        setLocalError(result.error || 'Display initialization failed.');
    }
  };

  // Prioritize localError over context error for immediate feedback
  const displayError = localError || error;

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(45deg, rgba(46,125,50,0.05) 0%, rgba(198,40,40,0.05) 100%)',
        py: 4
      }}
    >
      <Container maxWidth="sm">
        <Grid container spacing={2} justifyContent="center" alignItems="center" sx={{ minHeight: '90vh' }}>
          <Grid item xs={12}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Typography 
                component="h1" 
                variant="h3"
                sx={{ 
                  fontWeight: 700,
                  color: theme.palette.primary.main,
                  letterSpacing: '-0.5px',
                  mb: 1
                }}
              >
                Pi-nopoly
              </Typography>
              <Typography 
                variant="subtitle1" 
                color="text.secondary"
                sx={{ fontWeight: 400 }}
              >
                A modern take on the classic board game
              </Typography>
            </Box>
          
            <Paper 
              elevation={2} 
              sx={{ 
                borderRadius: 2,
                overflow: 'hidden',
                boxShadow: '0 8px 40px rgba(0,0,0,0.12)'
              }}
            >
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs 
                  value={tabValue} 
                  onChange={handleTabChange} 
                  variant="fullWidth"
                  indicatorColor="primary"
                  textColor="primary"
                  aria-label="Game options"
                >
                  <Tab icon={<PersonAddIcon />} label={isMobile ? "" : "Join"} iconPosition="start" />
                  <Tab icon={<PersonIcon />} label={isMobile ? "" : "Return"} iconPosition="start" />
                  <Tab icon={<AdminPanelSettingsIcon />} label={isMobile ? "" : "Admin"} iconPosition="start" />
                  <Tab icon={<MonitorIcon />} label={isMobile ? "" : "Display"} iconPosition="start" />
                </Tabs>
              </Box>

              {/* Display error or success messages */} 
              {displayError && (
                <Alert severity="error" sx={{ mx: 3, mt: 2 }}>
                  {displayError}
                </Alert>
              )}
              {successMessage && (
                <Alert severity="success" sx={{ mx: 3, mt: 2 }}>
                  {successMessage}
                </Alert>
              )}

              {/* Tab Panels */}
              <TabPanel value={tabValue} index={0}>
                <Typography variant="h6" align="center" gutterBottom>
                  Join New Game
                </Typography>
                <Box component="form" onSubmit={handleJoinGame} noValidate>
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
                    variant="outlined"
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
                    variant="outlined"
                  />
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    sx={{ mt: 3, mb: 1, py: 1.5 }}
                    disabled={isLoading}
                    disableElevation
                  >
                    {isLoading ? <CircularProgress size={24} /> : 'Join Game'}
                  </Button>
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Typography variant="h6" align="center" gutterBottom>
                  Player Login
                </Typography>
                <Box component="form" onSubmit={handleLogin} noValidate>
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
                    variant="outlined"
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
                    variant="outlined"
                  />
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    sx={{ mt: 3, mb: 1, py: 1.5 }}
                    disabled={isLoading}
                    disableElevation
                  >
                    {isLoading ? <CircularProgress size={24} /> : 'Login'}
                  </Button>
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                <Typography variant="h6" align="center" gutterBottom>
                  Admin Login
                </Typography>
                <Box component="form" onSubmit={handleAdminLogin} noValidate>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    name="adminKey"
                    label="Admin Key"
                    type="password"
                    id="admin-key"
                    autoFocus
                    value={adminKeyInput}
                    onChange={(e) => setAdminKeyInput(e.target.value)}
                    variant="outlined"
                  />
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    sx={{ mt: 3, mb: 1, py: 1.5 }}
                    disabled={isLoading}
                    disableElevation
                  >
                    {isLoading ? <CircularProgress size={24} /> : 'Login as Admin'}
                  </Button>
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={3}>
                <Typography variant="h6" align="center" gutterBottom>
                  Initialize Display
                </Typography>
                <Box component="form" onSubmit={handleInitializeDisplay} noValidate sx={{ mt: 1 }}>
                  <Typography variant="body2" align="center" color="text.secondary" paragraph>
                    This will initialize the game board for display on a shared screen or TV.
                  </Typography>
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    sx={{ mt: 3, mb: 1, py: 1.5 }}
                    disabled={isLoading}
                    disableElevation
                  >
                    {isLoading ? <CircularProgress size={24} /> : 'Initialize Display'}
                  </Button>
                </Box>
              </TabPanel>
            </Paper>
            
            <Typography variant="body2" align="center" sx={{ mt: 4, color: 'text.secondary' }}>
              © {new Date().getFullYear()} Pi-nopoly
            </Typography>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default HomePage; 