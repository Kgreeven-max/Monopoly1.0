import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Grid, 
  Typography, 
  Paper,
  Button,
  IconButton,
  Drawer,
  AppBar,
  Toolbar,
  Tabs,
  Tab,
  useMediaQuery,
  useTheme,
  CircularProgress,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useGame } from '../../contexts/GameContext';
import { useSocket } from '../../contexts/SocketContext';

// Import components
import Board from '../board/Board';

// Import icons
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import PersonIcon from '@mui/icons-material/Person';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';
import RefreshIcon from '@mui/icons-material/Refresh';
import CasinoIcon from '@mui/icons-material/Casino';
import DashboardIcon from '@mui/icons-material/Dashboard';
import MapIcon from '@mui/icons-material/Map';
import InfoIcon from '@mui/icons-material/Info';
import GroupIcon from '@mui/icons-material/Group';
import SettingsIcon from '@mui/icons-material/Settings';

// Player colors
const PLAYER_COLORS = [
  '#E53935', // Red
  '#1E88E5', // Blue
  '#43A047', // Green
  '#FDD835', // Yellow
  '#8E24AA', // Purple
  '#FB8C00', // Orange
  '#26A69A', // Teal
  '#EC407A', // Pink
];

// Styled components
const GameAppBar = styled(AppBar)(({ theme }) => ({
  backgroundImage: `linear-gradient(to right, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
  boxShadow: 'none',
  borderBottom: `1px solid ${theme.palette.divider}`,
}));

const MainContent = styled(Box)(({ theme, isSidebarOpen, isMobile }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  transition: theme.transitions.create('margin', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: isMobile ? 0 : isSidebarOpen ? 240 : 0,
  [theme.breakpoints.down('md')]: {
    padding: theme.spacing(2),
  },
}));

const SidebarDrawer = styled(Drawer)(({ theme }) => ({
  width: 240,
  flexShrink: 0,
  '& .MuiDrawer-paper': {
    width: 240,
    boxSizing: 'border-box',
    borderRight: `1px solid ${theme.palette.divider}`,
  },
}));

const DiceDisplay = styled(Box)(({ theme }) => ({
  display: 'flex',
  gap: theme.spacing(1),
  justifyContent: 'center',
  alignItems: 'center',
}));

const Die = styled(Box)(({ theme, value }) => ({
  width: 40,
  height: 40,
  backgroundColor: 'white',
  border: `2px solid ${theme.palette.grey[300]}`,
  borderRadius: theme.shape.borderRadius,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '1.5rem',
  fontWeight: 'bold',
  boxShadow: '0 2px 5px rgba(0,0,0,0.15)',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 50%)',
    borderRadius: 'inherit',
  }
}));

// Tab panel component
function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`game-tabpanel-${index}`}
      aria-labelledby={`game-tab-${index}`}
      {...other}
      style={{ height: '100%' }}
    >
      {value === index && children}
    </div>
  );
}

const GameContainer = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [isSidebarOpen, setIsSidebarOpen] = useState(!isMobile);
  const [activeTab, setActiveTab] = useState(0);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const { gameState } = useGame();
  const { socket, emit, connectSocket, isConnected } = useSocket();
  const gameContainerRef = React.useRef(null);

  // Connect socket when component mounts
  useEffect(() => {
    if (!isConnected) {
      connectSocket({
        path: '/ws/socket.io',
        transports: ['websocket', 'polling']
      });
    }
  }, [isConnected, connectSocket]);

  // Request game state update
  useEffect(() => {
    if (isConnected) {
      requestGameState();
      const interval = setInterval(requestGameState, 5000);
      return () => clearInterval(interval);
    }
  }, [isConnected]);

  // Update fullscreen state
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullScreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullScreenChange);
  }, []);

  const requestGameState = () => {
    emit('request_game_state', { gameId: 1 });
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement && gameContainerRef.current) {
      gameContainerRef.current.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Loading state
  if (!gameState || !gameState.players) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          backgroundColor: theme.palette.background.default
        }}
      >
        <CircularProgress size={60} thickness={4} color="primary" />
        <Typography variant="h6" sx={{ mt: 3, fontWeight: 500 }}>
          Loading game...
        </Typography>
      </Box>
    );
  }

  return (
    <Box 
      ref={gameContainerRef}
      sx={{ 
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: theme.palette.background.default
      }}
    >
      {/* App Bar */}
      <GameAppBar position="fixed">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle sidebar"
            onClick={toggleSidebar}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Pi-nopoly
          </Typography>
          
          {/* Game status */}
          <Chip 
            label={gameState.status} 
            color={gameState.status === 'In Progress' ? 'success' : 'default'}
            size="small"
            sx={{ mr: 2, fontWeight: 500 }}
          />
          
          {/* Current player indicator */}
          {gameState.current_player_id != null && (
            <Chip 
              avatar={
                <Avatar 
                  sx={{ bgcolor: PLAYER_COLORS[gameState.current_player_id % PLAYER_COLORS.length] }}
                >
                  {gameState.players.find(p => p.id === gameState.current_player_id)?.username.charAt(0).toUpperCase()}
                </Avatar>
              }
              label={`${gameState.players.find(p => p.id === gameState.current_player_id)?.username}'s Turn`}
              variant="outlined"
              size="small"
              sx={{ 
                mr: 2,
                bgcolor: 'rgba(255,255,255,0.1)',
                color: 'white',
                border: 'none'
              }}
            />
          )}
          
          {/* Dice display */}
          {gameState.last_dice_roll && gameState.last_dice_roll.length === 2 && (
            <DiceDisplay>
              <CasinoIcon color="inherit" fontSize="small" />
              <Die value={gameState.last_dice_roll[0]}>
                {gameState.last_dice_roll[0]}
              </Die>
              <Die value={gameState.last_dice_roll[1]}>
                {gameState.last_dice_roll[1]}
              </Die>
            </DiceDisplay>
          )}
          
          {/* Action buttons */}
          <IconButton color="inherit" onClick={requestGameState} sx={{ ml: 1 }}>
            <RefreshIcon />
          </IconButton>
          
          <IconButton color="inherit" onClick={toggleFullScreen} sx={{ ml: 1 }}>
            {isFullScreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
          </IconButton>
        </Toolbar>
        
        {/* Sub navigation for mobile */}
        {isMobile && (
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            variant="fullWidth"
            textColor="inherit"
            sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}
          >
            <Tab icon={<MapIcon />} label="Board" />
            <Tab icon={<GroupIcon />} label="Players" />
            <Tab icon={<InfoIcon />} label="Log" />
            <Tab icon={<SettingsIcon />} label="Settings" />
          </Tabs>
        )}
      </GameAppBar>
      
      {/* Sidebar Drawer */}
      <SidebarDrawer
        variant={isMobile ? "temporary" : "persistent"}
        anchor="left"
        open={isSidebarOpen}
        onClose={toggleSidebar}
      >
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          p: 2,
          borderBottom: `1px solid ${theme.palette.divider}`
        }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}>
            Game Info
          </Typography>
          <IconButton onClick={toggleSidebar}>
            <CloseIcon />
          </IconButton>
        </Box>
        
        {/* Game Status Section */}
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Game Status
          </Typography>
          <Typography variant="body1" fontWeight="500">
            {gameState.status}
          </Typography>
          
          <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }} gutterBottom>
            Current Turn
          </Typography>
          <Typography variant="body1" fontWeight="500">
            {gameState.current_turn || 1}
          </Typography>
        </Box>
        
        <Divider />
        
        {/* Players List */}
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Players ({gameState.players.length})
          </Typography>
          
          <List disablePadding>
            {gameState.players.map((player) => (
              <ListItem 
                key={player.id}
                disablePadding
                sx={{
                  py: 1,
                  px: 0,
                  borderRadius: 1,
                  mb: 0.5,
                  bgcolor: gameState.current_player_id === player.id ? 'rgba(46, 125, 50, 0.1)' : 'transparent',
                }}
              >
                <ListItemAvatar sx={{ minWidth: 40 }}>
                  <Avatar 
                    sx={{ 
                      width: 32, 
                      height: 32,
                      bgcolor: PLAYER_COLORS[player.id % PLAYER_COLORS.length],
                      fontSize: '0.875rem'
                    }}
                  >
                    {player.username.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemAvatar>
                
                <ListItemText 
                  primary={player.username}
                  secondary={`$${player.money} • Position: ${player.position}`}
                  primaryTypographyProps={{ 
                    fontWeight: 500,
                    variant: 'body2',
                    fontSize: '0.875rem'
                  }}
                  secondaryTypographyProps={{ 
                    variant: 'caption',
                    fontSize: '0.75rem'
                  }}
                />
                
                {gameState.current_player_id === player.id && (
                  <Chip 
                    label="Turn" 
                    color="primary" 
                    size="small"
                    sx={{ height: 24 }}
                  />
                )}
              </ListItem>
            ))}
          </List>
        </Box>
        
        <Divider />
        
        {/* Game log section */}
        <Box sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Recent Activity
          </Typography>
          
          <Box sx={{ 
            maxHeight: 200, 
            overflowY: 'auto',
            bgcolor: theme.palette.background.paper,
            borderRadius: 1,
            p: 1,
            border: `1px solid ${theme.palette.divider}`
          }}>
            {gameState.log && gameState.log.length > 0 ? (
              <Box component="ul" sx={{ pl: 2, m: 0 }}>
                {gameState.log.slice().reverse().slice(0, 8).map((entry, index) => (
                  <Typography 
                    key={index} 
                    component="li" 
                    variant="caption" 
                    color="text.secondary"
                    sx={{ mb: 0.5 }}
                  >
                    {entry}
                  </Typography>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.disabled" align="center">
                No game events yet
              </Typography>
            )}
          </Box>
        </Box>
      </SidebarDrawer>
      
      {/* Main Content */}
      <MainContent 
        isSidebarOpen={isSidebarOpen} 
        isMobile={isMobile}
        sx={{ mt: isMobile ? 8 : 8 }}
      >
        {isMobile ? (
          <Box sx={{ mt: 5 }}>
            <TabPanel value={activeTab} index={0}>
              <Board 
                players={gameState.players} 
                currentPlayerId={gameState.current_player_id}
                properties={gameState.properties}
              />
            </TabPanel>
            
            <TabPanel value={activeTab} index={1}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>Players</Typography>
                <Grid container spacing={2}>
                  {gameState.players.map((player) => (
                    <Grid item xs={12} sm={6} key={player.id}>
                      <Paper 
                        variant="outlined" 
                        sx={{ 
                          p: 2, 
                          borderRadius: 2,
                          borderColor: gameState.current_player_id === player.id ? 'primary.main' : 'divider'
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar 
                            sx={{ 
                              bgcolor: PLAYER_COLORS[player.id % PLAYER_COLORS.length],
                              mr: 1
                            }}
                          >
                            {player.username.charAt(0).toUpperCase()}
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle1">{player.username}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              ${player.money} • Position: {player.position}
                            </Typography>
                          </Box>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            </TabPanel>
            
            <TabPanel value={activeTab} index={2}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>Game Log</Typography>
                <Box sx={{ 
                  maxHeight: '60vh', 
                  overflowY: 'auto',
                  bgcolor: theme.palette.background.paper,
                  borderRadius: 1,
                  p: 1
                }}>
                  {gameState.log && gameState.log.length > 0 ? (
                    <Box component="ul" sx={{ pl: 2, m: 0 }}>
                      {gameState.log.slice().reverse().map((entry, index) => (
                        <Typography 
                          key={index} 
                          component="li" 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ mb: 1 }}
                        >
                          {entry}
                        </Typography>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.disabled" align="center">
                      No game events yet
                    </Typography>
                  )}
                </Box>
              </Paper>
            </TabPanel>
            
            <TabPanel value={activeTab} index={3}>
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>Settings</Typography>
                <Button
                  variant="contained"
                  onClick={toggleFullScreen}
                  startIcon={isFullScreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                  sx={{ mb: 2 }}
                >
                  {isFullScreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={requestGameState}
                  startIcon={<RefreshIcon />}
                >
                  Refresh Game State
                </Button>
              </Paper>
            </TabPanel>
          </Box>
        ) : (
          <Grid container spacing={3}>
            <Grid item xs={12} lg={9}>
              <Board 
                players={gameState.players} 
                currentPlayerId={gameState.current_player_id}
                properties={gameState.properties}
              />
            </Grid>
            
            <Grid item xs={12} lg={3}>
              {/* Game status card for desktop */}
              <Paper sx={{ p: 2, borderRadius: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Current Game</Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">Status</Typography>
                  <Chip 
                    label={gameState.status} 
                    color={gameState.status === 'In Progress' ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">Current Player</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <Avatar 
                      sx={{ 
                        width: 24, 
                        height: 24, 
                        mr: 1,
                        bgcolor: gameState.current_player_id != null
                          ? PLAYER_COLORS[gameState.current_player_id % PLAYER_COLORS.length]
                          : 'grey.500'
                      }}
                    >
                      {gameState.current_player_id != null
                        ? gameState.players.find(p => p.id === gameState.current_player_id)?.username.charAt(0).toUpperCase()
                        : '?'}
                    </Avatar>
                    <Typography variant="body2">
                      {gameState.current_player_id != null
                        ? gameState.players.find(p => p.id === gameState.current_player_id)?.username
                        : 'None'}
                    </Typography>
                  </Box>
                </Box>
                
                {gameState.last_dice_roll && gameState.last_dice_roll.length === 2 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Last Roll
                    </Typography>
                    <DiceDisplay>
                      <Die value={gameState.last_dice_roll[0]}>
                        {gameState.last_dice_roll[0]}
                      </Die>
                      <Die value={gameState.last_dice_roll[1]}>
                        {gameState.last_dice_roll[1]}
                      </Die>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                        = {gameState.last_dice_roll[0] + gameState.last_dice_roll[1]}
                      </Typography>
                    </DiceDisplay>
                  </Box>
                )}
                
                <Button
                  variant="outlined"
                  onClick={requestGameState}
                  startIcon={<RefreshIcon />}
                  size="small"
                  fullWidth
                >
                  Refresh
                </Button>
              </Paper>
              
              {/* Players card for desktop */}
              <Paper sx={{ p: 2, borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>Players</Typography>
                
                <List disablePadding>
                  {gameState.players.map((player) => (
                    <ListItem 
                      key={player.id}
                      disablePadding
                      sx={{
                        py: 1,
                        borderRadius: 1,
                        mb: 1,
                        bgcolor: gameState.current_player_id === player.id ? 'rgba(46, 125, 50, 0.1)' : 'transparent',
                      }}
                    >
                      <ListItemAvatar>
                        <Avatar 
                          sx={{ 
                            bgcolor: PLAYER_COLORS[player.id % PLAYER_COLORS.length]
                          }}
                        >
                          {player.username.charAt(0).toUpperCase()}
                        </Avatar>
                      </ListItemAvatar>
                      
                      <ListItemText 
                        primary={player.username}
                        secondary={`$${player.money} • Position: ${player.position}${player.in_jail ? ' • In Jail' : ''}`}
                        primaryTypographyProps={{ fontWeight: gameState.current_player_id === player.id ? 700 : 500 }}
                      />
                      
                      {gameState.current_player_id === player.id && (
                        <Chip 
                          label="Turn" 
                          color="primary" 
                          size="small"
                        />
                      )}
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Grid>
          </Grid>
        )}
      </MainContent>
    </Box>
  );
};

export default GameContainer; 