import React, { useEffect, useState } from 'react';
import { Box, Typography, Button, Paper, Switch, FormControlLabel, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import SmartGameBoard from '../../game-board/components/Board/SmartGameBoard';
import { useGame } from '../../game-state/contexts/GameContext';
import useGameEventDebugger from '../../game-board/hooks/useGameEventDebugger';
import NavBar from '../../components/ui/NavBar';

export default function BoardPage() {
  const { state } = useGame();
  const [animationEnabled, setAnimationEnabled] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  
  // Debug logging to verify component is loading
  console.log('[BoardPage] Component loaded, debugMode:', debugMode);
  
  const {
    eventLog,
    playerMovements,
    getLatestMovement,
    hasRecentMovement,
    currentState
  } = useGameEventDebugger();

  return (
    <Box>
      <NavBar />
      
      <Box sx={{ display: 'flex', gap: 2, p: 2 }}>
        {/* Game Board */}
        <Box sx={{ flex: 1 }}>
          {/* Smart Game Board with Real Game Event Detection */}
          <SmartGameBoard />
        </Box>
        
        {/* Control Panel */}
        <Box sx={{ width: 320, maxHeight: '90vh', overflowY: 'auto' }}>
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom style={{ color: 'red', fontWeight: 'bold' }}>
              🎮 Enhanced Board Controls (v2.0)
            </Typography>
            
            {/* Animation Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={animationEnabled}
                  onChange={(e) => setAnimationEnabled(e.target.checked)}
                  color="primary"
                />
              }
              label="Enable Animations"
              sx={{ mb: 1 }}
            />
            
            {/* Debug Mode Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  color="secondary"
                />
              }
              label="Debug Mode"
              sx={{ mb: 2 }}
            />
            
            {/* Enhanced Debug Info - Always Visible */}
            <Box sx={{ 
              p: 1, 
              bgcolor: debugMode ? 'success.light' : 'grey.100', 
              borderRadius: 1,
              fontSize: '0.75rem',
              border: debugMode ? '2px solid green' : '1px solid #ccc'
            }}>
              <Typography variant="caption" display="block" fontWeight="bold">
                🔧 DEBUG INFO (Mode: {debugMode ? 'ON' : 'OFF'})
              </Typography>
              <Typography variant="caption" display="block">
                Socket: {state.gameId ? '✅ Connected' : '❌ Disconnected'}
              </Typography>
              <Typography variant="caption" display="block">
                Players: {currentState.playersCount}
              </Typography>
              <Typography variant="caption" display="block">
                Notifications: {currentState.notificationsCount}
              </Typography>
              <Typography variant="caption" display="block">
                Current Player: {currentState.currentPlayer || 'None'}
              </Typography>
              <Typography variant="caption" display="block">
                Last Dice: {currentState.lastDiceRoll ? currentState.lastDiceRoll.join(', ') : 'None'}
              </Typography>
              <Typography variant="caption" display="block" color={hasRecentMovement() ? 'success.main' : 'text.secondary'}>
                Recent Movement: {hasRecentMovement() ? '✅ YES' : '❌ No'}
              </Typography>
            </Box>
          </Paper>

          {/* Game Status */}
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Game Status
            </Typography>
            
            <Box sx={{ fontSize: '0.85rem' }}>
              <Typography variant="body2">
                Game ID: {state.gameId || 'None'}
              </Typography>
              <Typography variant="body2">
                Status: {state.status}
              </Typography>
              <Typography variant="body2">
                Players: {state.players?.length || 0}
              </Typography>
              <Typography variant="body2">
                Current Turn: {state.currentTurn}
              </Typography>
              <Typography variant="body2">
                Game Mode: {state.gameMode || 'Standard'}
              </Typography>
            </Box>
          </Paper>

          {/* Player List */}
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Players
            </Typography>
            
            {state.players && state.players.length > 0 ? (
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                {state.players.map((player, index) => (
                  <Box
                    key={player.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 1,
                      mb: 1,
                      bgcolor: player.id === state.currentPlayerId ? 'primary.light' : 'grey.50',
                      borderRadius: 1,
                      fontSize: '0.8rem'
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          bgcolor: player.color || '#999'
                        }}
                      />
                      <Typography variant="body2">
                        {player.name || player.username || `Player ${player.id}`}
                        {player.is_bot && ' (Bot)'}
                      </Typography>
                    </Box>
                    <Typography variant="caption">
                      Pos: {player.position || 0}
                    </Typography>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No players in game
              </Typography>
            )}
          </Paper>

          {/* Recent Movements - Debug Mode */}
          {debugMode && (
            <Accordion defaultExpanded>
              <AccordionSummary>
                <Typography variant="h6">
                  Recent Movements ({playerMovements.filter(m => m.isMovement).length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                  {playerMovements.filter(m => m.isMovement).length > 0 ? (
                    playerMovements.filter(m => m.isMovement).slice(0, 5).map((movement, index) => (
                      <Box
                        key={index}
                        sx={{
                          p: 1,
                          mb: 1,
                          bgcolor: 'grey.50',
                          borderRadius: 1,
                          fontSize: '0.7rem'
                        }}
                      >
                        <Typography variant="caption" display="block">
                          <strong>{movement.playerName}</strong> {movement.isBot && '🤖'}
                        </Typography>
                        <Typography variant="caption" display="block">
                          {movement.timestamp}: {movement.previousPosition} → {movement.position}
                        </Typography>
                      </Box>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No movements detected
                    </Typography>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Recent Notifications - Debug Mode */}
          {debugMode && (
            <Accordion>
              <AccordionSummary>
                <Typography variant="h6">
                  Recent Notifications ({state.notifications?.length || 0})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                  {state.notifications && state.notifications.length > 0 ? (
                    state.notifications.slice(0, 5).map((notification, index) => (
                      <Box
                        key={index}
                        sx={{
                          p: 1,
                          mb: 1,
                          bgcolor: notification.type === 'error' ? 'error.light' : 'grey.50',
                          borderRadius: 1,
                          fontSize: '0.7rem'
                        }}
                      >
                        <Typography variant="caption" display="block">
                          {notification.message}
                        </Typography>
                      </Box>
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No notifications
                    </Typography>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Instructions */}
          <Paper elevation={3} sx={{ p: 2, mt: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
            <Typography variant="subtitle2" gutterBottom>
              How to Test:
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
              • Use the "Test Move" button on the board to see smooth animations
              <br />
              • Use "Test Dice" to see dice roll effects
              <br />
              • Turn on "Debug Mode" to see movement detection
              <br />
              • When bots move, watch "Recent Movements" section
            </Typography>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}