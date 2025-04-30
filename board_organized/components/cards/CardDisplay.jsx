import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Button } from '@mui/material';
import { useGame } from '../contexts/GameContext';

const cardColors = {
  chance: '#FF9800', // Orange
  community_chest: '#2196F3' // Blue
};

export default function CardDisplay() {
  const { gameState } = useGame();
  const [visible, setVisible] = useState(false);
  const [currentCard, setCurrentCard] = useState(null);

  useEffect(() => {
    // When a new card is drawn, show it
    if (gameState.lastCardDrawn && gameState.lastCardDrawn !== currentCard) {
      setCurrentCard(gameState.lastCardDrawn);
      setVisible(true);
      
      // Hide the card after 5 seconds
      const timer = setTimeout(() => {
        setVisible(false);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [gameState.lastCardDrawn]);

  // If no card or not visible, return null
  if (!visible || !currentCard) return null;
  
  const cardType = currentCard.cardType || 'chance';
  const card = currentCard.card || {};
  
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 1000,
      }}
    >
      <Paper
        elevation={5}
        sx={{
          width: '300px',
          padding: 3,
          backgroundColor: cardColors[cardType] || '#FFF',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          borderRadius: 2,
          transition: 'all 0.3s ease',
          transform: 'scale(1)',
          animation: 'appear 0.5s ease-out',
          '@keyframes appear': {
            '0%': { transform: 'scale(0.8)', opacity: 0 },
            '100%': { transform: 'scale(1)', opacity: 1 },
          }
        }}
      >
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'white' }}>
          {cardType === 'chance' ? 'CHANCE' : 'COMMUNITY CHEST'}
        </Typography>
        
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2, color: 'white' }}>
          {card.title || ''}
        </Typography>
        
        <Typography sx={{ textAlign: 'center', mb: 3, color: 'white' }}>
          {card.description || ''}
        </Typography>
        
        <Button 
          variant="contained" 
          onClick={() => setVisible(false)}
          sx={{ backgroundColor: 'white', color: cardColors[cardType] }}
        >
          Close
        </Button>
      </Paper>
    </Box>
  );
} 