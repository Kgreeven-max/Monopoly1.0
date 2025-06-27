import React, { useEffect, useState } from 'react';
import { Box, Typography, Button, Paper, Switch, FormControlLabel, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import SmartGameBoard from '../../game-board/components/Board/SmartGameBoard';
import { useGame } from '../../game-state/contexts/GameContext';
import useGameEventDebugger from '../../game-board/hooks/useGameEventDebugger';
import NavBar from '../../components/ui/NavBar';

export default function DebugBoardPage() {
  const { state } = useGame();
  const [animationEnabled, setAnimationEnabled] = useState(true);
  const [debugMode, setDebugMode] = useState(true);
  
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
        
        {/* Debug Panel */}
        <Box sx={{ width: 350, maxHeight: '90vh', overflowY: 'auto' }}>
          {/* Controls */}
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Debug Controls
            </Typography>
            
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
            
            <FormControlLabel
              control={
                <Switch
                  checked={debugMode}
                  onChange={(e) => setDebugMode(e.target.checked)}
                  color="secondary"
                />
              }
              label="Verbose Debug"
              sx={{ mb: 2 }}
            />
          </Paper>

          {/* Current Game State */}
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Current State
            </Typography>
            
            <Box sx={{ fontSize: '0.8rem' }}>
              <Typography variant="body2">
                Game ID: {state.gameId || 'None'}
              </Typography>
              <Typography variant="body2">
                Status: {state.status}
              </Typography>
              <Typography variant="body2">
                Players: {currentState.playersCount}
              </Typography>
              <Typography variant="body2">
                Notifications: {currentState.notificationsCount}
              </Typography>
              <Typography variant="body2">
                Current Player: {currentState.currentPlayer || 'None'}
              </Typography>
              <Typography variant="body2">
                Last Dice: {currentState.lastDiceRoll ? currentState.lastDiceRoll.join(', ') : 'None'}
              </Typography>
              <Typography variant="body2" color={hasRecentMovement() ? 'success.main' : 'text.secondary'}>
                Recent Movement: {hasRecentMovement() ? 'YES' : 'No'}
              </Typography>
            </Box>
          </Paper>

          {/* Player Positions */}
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Player Positions
            </Typography>
            
            {state.players && state.players.length > 0 ? (
              <Box sx={{ maxHeight: 150, overflow: 'auto' }}>
                {state.players.map((player) => (
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
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          bgcolor: player.color || '#999'
                        }}
                      />
                      <Typography variant="body2">
                        {player.name || player.username || `Player ${player.id}`}
                        {player.is_bot && ' 🤖'}
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

          {/* Recent Movements */}
          <Accordion defaultExpanded>
            <AccordionSummary>
              <Typography variant="h6">
                Recent Movements ({playerMovements.filter(m => m.isMovement).length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                {playerMovements.filter(m => m.isMovement).length > 0 ? (
                  playerMovements.filter(m => m.isMovement).map((movement, index) => (
                    <Box
                      key={index}
                      sx={{
                        p: 1,
                        mb: 1,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        fontSize: '0.75rem'
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

          {/* Recent Notifications */}
          <Accordion>
            <AccordionSummary>
              <Typography variant="h6">
                Recent Notifications ({state.notifications?.length || 0})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                {state.notifications && state.notifications.length > 0 ? (
                  state.notifications.slice(0, 10).map((notification, index) => (
                    <Box
                      key={index}
                      sx={{
                        p: 1,
                        mb: 1,
                        bgcolor: notification.type === 'error' ? 'error.light' : 'grey.50',
                        borderRadius: 1,
                        fontSize: '0.75rem'
                      }}
                    >
                      <Typography variant="caption" display="block">
                        {notification.message}
                      </Typography>
                      {notification.type && (
                        <Typography variant="caption" sx={{ opacity: 0.7 }}>
                          Type: {notification.type}
                        </Typography>
                      )}
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

          {/* Event Log */}
          {debugMode && (
            <Accordion>
              <AccordionSummary>
                <Typography variant="h6">
                  Event Log ({eventLog.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                  {eventLog.map((entry, index) => (
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
                        <strong>{entry.timestamp}</strong> - {entry.type}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Players: {entry.players?.length || 0}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Notifications: {entry.notifications?.length || 0}
                      </Typography>
                      {entry.lastDiceRoll && (
                        <Typography variant="caption" display="block">
                          Dice: {entry.lastDiceRoll.join(', ')}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Instructions */}
          <Paper elevation={3} sx={{ p: 2, mt: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
            <Typography variant="subtitle2" gutterBottom>
              Debugging Help:
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
              • "Test Move" should work (animation system OK)
              <br />
              • Watch "Recent Movements" for real bot moves
              <br />
              • Check "Recent Notifications" for game events
              <br />
              • If movements show but no animation, the event detection needs fixing
            </Typography>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}