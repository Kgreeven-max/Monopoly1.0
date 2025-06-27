import React, { useEffect, useState } from 'react';
import { Box, Typography, Button, Paper, Switch, FormControlLabel } from '@mui/material';
import AnimatedGameBoard from '../../game-board/components/Board/AnimatedGameBoard';
import { useAnimatedGame } from '../../game-state/contexts/GameContext/AnimatedGameContext';
import { useAnimation } from '../../game-state/contexts/AnimationContext';
import NavBar from '../../components/ui/NavBar';

export default function AnimatedBoardPage() {
  const { 
    gameState, 
    animationMode, 
    toggleAnimationMode,
    getEnhancedGameStatus,
    isAnimating 
  } = useAnimatedGame();
  
  const { 
    animatePlayerMovement,
    queuePlayerMovement,
    queueDiceRoll,
    getAnimationStatus,
    clearAllAnimations 
  } = useAnimation();
  
  const [gameStatus, setGameStatus] = useState(null);

  // Update game status periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setGameStatus(getEnhancedGameStatus());
    }, 1000);

    return () => clearInterval(interval);
  }, [getEnhancedGameStatus]);

  // Test functions for demonstrating the animation system
  const testPlayerMovement = () => {
    if (gameState.players && gameState.players.length > 0) {
      const testPlayer = gameState.players[0];
      const currentPos = testPlayer.position || 0;
      const steps = Math.floor(Math.random() * 12) + 1; // 1-12 steps
      const newPos = (currentPos + steps) % 40;
      
      console.log(`[AnimatedBoardPage] Testing player movement: ${currentPos} → ${newPos} (${steps} steps)`);
      
      queuePlayerMovement(testPlayer.id, currentPos, newPos, steps);
    }
  };

  const testDiceRoll = () => {
    const roll1 = Math.floor(Math.random() * 6) + 1;
    const roll2 = Math.floor(Math.random() * 6) + 1;
    
    console.log(`[AnimatedBoardPage] Testing dice roll: [${roll1}, ${roll2}]`);
    
    queueDiceRoll([roll1, roll2], 1500);
  };

  const testFullTurnSequence = () => {
    if (gameState.players && gameState.players.length > 0) {
      const testPlayer = gameState.players[0];
      const currentPos = testPlayer.position || 0;
      const roll1 = Math.floor(Math.random() * 6) + 1;
      const roll2 = Math.floor(Math.random() * 6) + 1;
      const steps = roll1 + roll2;
      const newPos = (currentPos + steps) % 40;
      
      console.log(`[AnimatedBoardPage] Testing full turn sequence: dice=[${roll1}, ${roll2}], movement=${currentPos}→${newPos}`);
      
      // First queue dice animation
      queueDiceRoll([roll1, roll2], 1500);
      
      // Then queue movement animation with delay
      setTimeout(() => {
        queuePlayerMovement(testPlayer.id, currentPos, newPos, steps);
      }, 1600); // Start movement after dice animation
    }
  };

  const simulateBotTurn = () => {
    if (gameState.players && gameState.players.length > 1) {
      const botPlayer = gameState.players.find(p => p.is_bot) || gameState.players[1];
      const currentPos = botPlayer.position || 0;
      const roll1 = Math.floor(Math.random() * 6) + 1;
      const roll2 = Math.floor(Math.random() * 6) + 1;
      const steps = roll1 + roll2;
      const newPos = (currentPos + steps) % 40;
      
      console.log(`[AnimatedBoardPage] Simulating bot turn for ${botPlayer.name}: dice=[${roll1}, ${roll2}], movement=${currentPos}→${newPos}`);
      
      // Simulate the full sequence as a bot would experience it
      queueDiceRoll([roll1, roll2], 1500);
      setTimeout(() => {
        queuePlayerMovement(botPlayer.id, currentPos, newPos, steps);
      }, 1600);
    }
  };

  return (
    <Box>
      <NavBar />
      
      <Box sx={{ display: 'flex', gap: 2, p: 2 }}>
        {/* Game Board */}
        <Box sx={{ flex: 1 }}>
          <AnimatedGameBoard />
        </Box>
        
        {/* Control Panel */}
        <Box sx={{ width: 300 }}>
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Animation Controls
            </Typography>
            
            {/* Animation Mode Toggle */}
            <FormControlLabel
              control={
                <Switch
                  checked={animationMode}
                  onChange={toggleAnimationMode}
                  color="primary"
                />
              }
              label="Enable Animations"
              sx={{ mb: 2 }}
            />
            
            {/* Test Buttons */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
              <Button 
                variant="outlined" 
                size="small"
                onClick={testPlayerMovement}
                disabled={isAnimating}
              >
                Test Player Movement
              </Button>
              
              <Button 
                variant="outlined" 
                size="small"
                onClick={testDiceRoll}
                disabled={isAnimating}
              >
                Test Dice Roll
              </Button>
              
              <Button 
                variant="outlined" 
                size="small"
                onClick={testFullTurnSequence}
                disabled={isAnimating}
                color="primary"
              >
                Test Full Turn Sequence
              </Button>
              
              <Button 
                variant="outlined" 
                size="small"
                onClick={simulateBotTurn}
                disabled={isAnimating}
                color="secondary"
              >
                Simulate Bot Turn
              </Button>
            </Box>
            
            {/* Emergency Controls */}
            <Button 
              variant="contained" 
              size="small"
              onClick={clearAllAnimations}
              color="error"
              fullWidth
            >
              Stop All Animations
            </Button>
          </Paper>

          {/* Game Status */}
          <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Game Status
            </Typography>
            
            {gameStatus && (
              <Box sx={{ fontSize: '0.8rem' }}>
                <Typography variant="body2">
                  Game ID: {gameState.gameId || 'None'}
                </Typography>
                <Typography variant="body2">
                  Status: {gameState.status}
                </Typography>
                <Typography variant="body2">
                  Players: {gameState.players?.length || 0}
                </Typography>
                <Typography variant="body2">
                  Current Turn: {gameState.currentTurn}
                </Typography>
                <Typography variant="body2" color={animationMode ? 'primary' : 'text.secondary'}>
                  Animation Mode: {animationMode ? 'ON' : 'OFF'}
                </Typography>
              </Box>
            )}
          </Paper>

          {/* Animation Status */}
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Animation Status
            </Typography>
            
            <Box sx={{ fontSize: '0.8rem' }}>
              <Typography variant="body2" color={isAnimating ? 'warning.main' : 'success.main'}>
                Status: {isAnimating ? 'ANIMATING' : 'IDLE'}
              </Typography>
              
              {gameStatus?.animation && (
                <>
                  <Typography variant="body2">
                    Queue Length: {gameStatus.animation.queueLength}
                  </Typography>
                  <Typography variant="body2">
                    Processing: {gameStatus.animation.isProcessingQueue ? 'YES' : 'NO'}
                  </Typography>
                  <Typography variant="body2">
                    Animating Player: {gameStatus.animation.animatingPlayer || 'None'}
                  </Typography>
                </>
              )}
              
              <Typography variant="body2">
                Pending Movements: {gameStatus?.pendingMovementsCount || 0}
              </Typography>
            </Box>
          </Paper>

          {/* Instructions */}
          <Paper elevation={3} sx={{ p: 2, mt: 2, bgcolor: 'background.default' }}>
            <Typography variant="subtitle2" gutterBottom>
              How to Test:
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
              1. Use "Test Player Movement" to see smooth step-by-step animation
              <br />
              2. Use "Test Dice Roll" to see dice animation
              <br />
              3. Use "Test Full Turn Sequence" to see coordinated dice + movement
              <br />
              4. Use "Simulate Bot Turn" to test bot movement animation
              <br />
              5. Toggle "Enable Animations" to compare with/without animation
            </Typography>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}