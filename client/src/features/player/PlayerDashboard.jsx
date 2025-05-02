import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Avatar, 
  Chip,
  Divider,
  Card,
  CardContent,
  Button,
  Stack,
  Alert,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  useTheme,
  LinearProgress,
  Tooltip,
  Badge
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useGame } from '../../contexts/GameContext';
import { useSocket } from '../../contexts/SocketContext';

// Icons
import CasinoIcon from '@mui/icons-material/Casino';
import HomeIcon from '@mui/icons-material/Home';
import DoNotDisturbOnIcon from '@mui/icons-material/DoNotDisturbOn';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import SavingsIcon from '@mui/icons-material/Savings';
import PaidIcon from '@mui/icons-material/Paid';
import MapIcon from '@mui/icons-material/Map';
import NotificationsIcon from '@mui/icons-material/Notifications';
import ArrowCircleRightIcon from '@mui/icons-material/ArrowCircleRight';
import LocalAtmIcon from '@mui/icons-material/LocalAtm';
import MoveUpIcon from '@mui/icons-material/MoveUp';
import KeyboardDoubleArrowDownIcon from '@mui/icons-material/KeyboardDoubleArrowDown';
import StackedLineChartIcon from '@mui/icons-material/StackedLineChart';

// Property group colors
const GROUP_COLORS = {
  brown: '#8B4513',
  lightblue: '#87CEEB',
  pink: '#FF69B4',
  orange: '#FFA500',
  red: '#FF0000',
  yellow: '#FFD700',
  green: '#008000',
  blue: '#0000CD',
  railroad: '#000000',
  utility: '#3CB371',
};

// Styled components
const StatsCard = styled(Card)(({ theme }) => ({
  height: '100%',
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: '0 12px 30px rgba(0,0,0,0.1)',
  }
}));

const ActionButton = styled(Button)(({ theme }) => ({
  padding: '12px',
  borderRadius: theme.shape.borderRadius,
  transition: 'transform 0.2s ease',
  '&:hover:not(:disabled)': {
    transform: 'translateY(-2px)',
  }
}));

const PropertyCard = styled(Box)(({ theme, color }) => ({
  padding: theme.spacing(1.5),
  borderRadius: theme.shape.borderRadius,
  border: '1px solid',
  borderColor: theme.palette.divider,
  backgroundColor: 'white',
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '6px',
    backgroundColor: color,
  }
}));

const NotificationBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
  },
}));

const PlayerDashboard = ({ playerId }) => {
  const theme = useTheme();
  const { gameState } = useGame();
  const { emit } = useSocket();
  const [notifications, setNotifications] = useState([]);
  const [activeTab, setActiveTab] = useState('actions');
  const [showNotifications, setShowNotifications] = useState(false);

  // Compute player data
  const player = gameState?.players?.find(p => p.id === parseInt(playerId, 10));
  const isCurrentPlayer = gameState?.current_player_id === parseInt(playerId, 10);
  const isGameInProgress = gameState?.status === 'In Progress';
  const canPerformActions = isCurrentPlayer && isGameInProgress;
  
  // Calculate player stats
  const netWorth = player ? (player.money + (player.properties?.length || 0) * 100) : 0;
  const playerProperties = gameState?.properties?.filter(p => p.owner_id === parseInt(playerId, 10)) || [];
  const propertiesByGroup = playerProperties.reduce((groups, property) => {
    const space = gameState?.spaces?.find(s => s.position === property.position);
    const group = space?.group || 'unknown';
    if (!groups[group]) groups[group] = [];
    groups[group].push({ ...property, name: space?.name || `Property ${property.position}` });
    return groups;
  }, {});

  // Game log filtered for this player
  const playerGameLog = (gameState?.log || [])
    .filter(entry => entry.includes(player?.username || ''))
    .slice(-10)
    .reverse();

  // Add notifications when it's player's turn
  useEffect(() => {
    if (isCurrentPlayer && !notifications.some(n => n.type === 'turn')) {
      setNotifications(prev => [
        { id: Date.now(), type: 'turn', message: "It's your turn to play!", important: true },
        ...prev
      ]);
    } else if (!isCurrentPlayer) {
      setNotifications(prev => prev.filter(n => n.type !== 'turn'));
    }
  }, [isCurrentPlayer, gameState?.current_player_id]);

  // Add notification for new properties
  useEffect(() => {
    if (playerProperties.length > 0 && player?.lastAcquiredProperty) {
      const property = gameState?.spaces?.find(s => s.position === player.lastAcquiredProperty);
      if (property) {
        setNotifications(prev => [
          { id: Date.now(), type: 'property', message: `You acquired ${property.name}!`, important: false },
          ...prev.filter(n => n.type !== 'property' || n.message !== `You acquired ${property.name}!`)
        ]);
      }
    }
  }, [playerProperties.length, player?.lastAcquiredProperty]);

  // Dismiss notification
  const dismissNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Game actions
  const handleRollDice = () => {
    emit('roll_dice', { playerId: parseInt(playerId) });
  };

  const handleBuyProperty = () => {
    emit('buy_property', { playerId: parseInt(playerId) });
  };

  const handleEndTurn = () => {
    emit('end_turn', { playerId: parseInt(playerId) });
  };

  if (!player) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="h6" sx={{ mt: 2 }}>Loading player data...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 3, px: { xs: 2, md: 4 } }}>
      {/* Header with player info */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          borderRadius: theme.shape.borderRadius * 1.5,
          background: `linear-gradient(135deg, ${theme.palette.primary.light} 0%, ${theme.palette.primary.main} 100%)`,
          color: 'white',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box sx={{ 
          position: 'absolute', 
          top: 0, 
          right: 0, 
          bottom: 0, 
          width: '40%',
          background: 'radial-gradient(circle at 80% 50%, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%)',
          zIndex: 1,
        }} />

        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Avatar
                sx={{
                  width: 64,
                  height: 64,
                  bgcolor: 'white',
                  color: theme.palette.primary.main,
                  fontWeight: 'bold',
                  fontSize: '1.8rem',
                  mr: 2,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}
              >
                {player.username.charAt(0).toUpperCase()}
              </Avatar>

              <Box>
                <Typography variant="h4" fontWeight="700">
                  {player.username}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                  <Chip
                    label={isCurrentPlayer ? "Your Turn" : "Waiting"}
                    color={isCurrentPlayer ? "secondary" : "default"}
                    size="small"
                    sx={{
                      fontWeight: 500,
                      mr: 1,
                      backgroundColor: isCurrentPlayer ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.3)',
                      color: isCurrentPlayer ? theme.palette.secondary.main : 'white',
                    }}
                  />
                  <Chip
                    label={`Game: ${gameState?.status || 'Unknown'}`}
                    size="small"
                    sx={{
                      fontWeight: 500,
                      backgroundColor: 'rgba(255,255,255,0.3)',
                      color: 'white',
                    }}
                  />
                </Box>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' }, mt: { xs: 2, md: 0 } }}>
              <Box sx={{ textAlign: { xs: 'left', md: 'right' }, mr: { xs: 4, md: 0 } }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Cash Balance
                </Typography>
                <Typography variant="h4" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center' }}>
                  ${player.money}
                  <LocalAtmIcon sx={{ ml: 1, fontSize: '1.8rem' }} />
                </Typography>
              </Box>

              <Box sx={{ textAlign: { xs: 'left', md: 'right' }, ml: 4 }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Net Worth
                </Typography>
                <Typography variant="h4" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center' }}>
                  ${netWorth}
                  <SavingsIcon sx={{ ml: 1, fontSize: '1.8rem' }} />
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Notifications bar (visible only if there are notifications) */}
      {notifications.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2 
            }}
          >
            <Typography variant="h6" fontWeight="600" sx={{ display: 'flex', alignItems: 'center' }}>
              <NotificationsIcon sx={{ mr: 1 }} /> Notifications
            </Typography>
            
            <Button 
              size="small" 
              onClick={() => setShowNotifications(!showNotifications)}
              endIcon={showNotifications ? <KeyboardDoubleArrowDownIcon /> : <MoveUpIcon />}
            >
              {showNotifications ? 'Hide' : 'Show All'}
            </Button>
          </Box>
          
          <Stack spacing={2}>
            {notifications
              .filter(n => showNotifications || n.important)
              .slice(0, showNotifications ? undefined : 2)
              .map(notification => (
                <Alert 
                  key={notification.id}
                  severity={notification.type === 'turn' ? 'success' : 'info'}
                  variant="filled"
                  icon={notification.type === 'turn' ? <ArrowCircleRightIcon /> : undefined}
                  action={
                    <IconButton 
                      color="inherit" 
                      size="small" 
                      onClick={() => dismissNotification(notification.id)}
                    >
                      <NotificationsIcon fontSize="small" />
                    </IconButton>
                  }
                  sx={{ 
                    borderRadius: theme.shape.borderRadius,
                    animation: notification.important ? 'pulse 2s infinite' : 'none'
                  }}
                >
                  {notification.message}
                </Alert>
              ))}
          </Stack>
        </Box>
      )}

      {/* Main content grid */}
      <Grid container spacing={3}>
        {/* Game Actions Card */}
        <Grid item xs={12} md={4}>
          <StatsCard>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <CasinoIcon sx={{ mr: 1 }} /> Game Actions
              </Typography>

              <Stack spacing={2.5} sx={{ mt: 3 }}>
                <ActionButton
                  variant="contained"
                  size="large"
                  startIcon={<CasinoIcon />}
                  onClick={handleRollDice}
                  disabled={!canPerformActions}
                  fullWidth
                  disableElevation
                >
                  Roll Dice
                </ActionButton>

                <ActionButton
                  variant="outlined"
                  size="large"
                  startIcon={<HomeIcon />}
                  onClick={handleBuyProperty}
                  disabled={!canPerformActions}
                  fullWidth
                >
                  Buy Property
                </ActionButton>

                <ActionButton
                  variant="outlined"
                  color="secondary"
                  size="large"
                  startIcon={<DoNotDisturbOnIcon />}
                  onClick={handleEndTurn}
                  disabled={!canPerformActions}
                  fullWidth
                >
                  End Turn
                </ActionButton>
              </Stack>

              <Box sx={{ mt: 4, opacity: canPerformActions ? 1 : 0.5 }}>
                <Alert
                  severity={canPerformActions ? "success" : "info"}
                  variant="outlined"
                  icon={canPerformActions ? <ArrowCircleRightIcon /> : undefined}
                >
                  {canPerformActions
                    ? "It's your turn! Make your move."
                    : "Please wait for your turn."}
                </Alert>
              </Box>
            </CardContent>
          </StatsCard>
        </Grid>

        {/* Player Stats Card */}
        <Grid item xs={12} md={4}>
          <StatsCard>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <StackedLineChartIcon sx={{ mr: 1 }} /> Player Stats
              </Typography>

              <Stack spacing={3} sx={{ mt: 3 }}>
                {/* Position */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">Position</Typography>
                    <Typography variant="body2" fontWeight="500">
                      Space {player.position} 
                      {gameState?.spaces && (
                        <Typography component="span" variant="caption" sx={{ ml: 1, opacity: 0.8 }}>
                          ({gameState.spaces.find(s => s.position === player.position)?.name})
                        </Typography>
                      )}
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={(player.position / 39) * 100} 
                    sx={{ height: 8, borderRadius: 2 }} 
                  />
                </Box>

                {/* Cash flow */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">Last Income</Typography>
                    <Typography 
                      variant="body2" 
                      fontWeight="500"
                      color={player.lastIncome > 0 ? 'success.main' : player.lastIncome < 0 ? 'error.main' : 'text.primary'}
                      sx={{ display: 'flex', alignItems: 'center' }}
                    >
                      {player.lastIncome > 0 ? '+' : ''}{player.lastIncome || 0}
                      {player.lastIncome > 0 ? (
                        <PaidIcon sx={{ ml: 0.5, fontSize: '1rem' }} />
                      ) : player.lastIncome < 0 ? (
                        <LocalAtmIcon sx={{ ml: 0.5, fontSize: '1rem' }} />
                      ) : null}
                    </Typography>
                  </Box>
                </Box>

                <Divider />

                {/* Properties count */}
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" color="text.secondary">Properties Owned</Typography>
                    <Typography variant="body2" fontWeight="500">
                      {playerProperties.length} / {gameState?.properties?.length || 28}
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={(playerProperties.length / (gameState?.properties?.length || 28)) * 100} 
                    color="secondary"
                    sx={{ height: 8, borderRadius: 2 }} 
                  />
                </Box>

                {/* Jail status */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Jail Status</Typography>
                  <Chip 
                    label={player.in_jail ? 'In Jail' : 'Free'} 
                    color={player.in_jail ? 'error' : 'success'} 
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Stack>
            </CardContent>
          </StatsCard>
        </Grid>

        {/* Properties Card */}
        <Grid item xs={12} md={4}>
          <StatsCard>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <HomeIcon sx={{ mr: 1 }} /> Your Properties
              </Typography>

              {playerProperties.length > 0 ? (
                <Box sx={{ mt: 2, maxHeight: 270, overflowY: 'auto' }}>
                  <Stack spacing={1.5}>
                    {Object.entries(propertiesByGroup).map(([group, properties]) => (
                      <Box key={group}>
                        <Typography 
                          variant="subtitle2" 
                          sx={{ 
                            mb: 1, 
                            color: GROUP_COLORS[group] || 'text.primary',
                            display: 'flex',
                            alignItems: 'center'
                          }}
                        >
                          <Box 
                            sx={{ 
                              width: 12, 
                              height: 12, 
                              borderRadius: '50%', 
                              backgroundColor: GROUP_COLORS[group] || 'grey.500',
                              mr: 1
                            }} 
                          />
                          {group.charAt(0).toUpperCase() + group.slice(1)} ({properties.length})
                        </Typography>
                        
                        <Stack spacing={1}>
                          {properties.map(property => (
                            <PropertyCard key={property.position} color={GROUP_COLORS[group]}>
                              <Typography variant="body2" fontWeight="500">
                                {property.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Rent: ${property.rent || 50} • Value: ${property.value || 200}
                              </Typography>
                            </PropertyCard>
                          ))}
                        </Stack>
                      </Box>
                    ))}
                  </Stack>
                </Box>
              ) : (
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
              )}
            </CardContent>
          </StatsCard>
        </Grid>

        {/* Game Log (full width) */}
        <Grid item xs={12}>
          <StatsCard>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <MapIcon sx={{ mr: 1 }} /> Game Activity
              </Typography>

              <TableContainer sx={{ mt: 2, maxHeight: 180 }}>
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell width="20%">Time</TableCell>
                      <TableCell>Event</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {playerGameLog.length > 0 ? (
                      playerGameLog.map((entry, index) => (
                        <TableRow key={index} hover>
                          <TableCell>
                            {new Date(entry.timestamp || Date.now() - index * 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </TableCell>
                          <TableCell>{entry.message || entry}</TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={2} align="center">
                          <Typography variant="body2" color="text.disabled">
                            No game activity yet
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </StatsCard>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PlayerDashboard; 