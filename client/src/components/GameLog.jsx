import React from 'react';
import { Box, Typography } from '@mui/material';

// Define styles for the game log component
export const gameLogStyle = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    padding: '10px',
    maxHeight: '300px',
    overflowY: 'auto',
    marginBottom: '10px',
    width: '100%',
  },
  content: {
    maxHeight: '100%',
    overflowY: 'auto',
    padding: '8px 12px',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: '8px',
    border: '1px solid #ddd',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    fontSize: '0.85rem',
    display: 'flex',
    flexDirection: 'column-reverse', // Show newest entries at the top
  }
};

/**
 * GameLog component displays a log of game activities
 * @param {Object} props - Component props
 * @param {Array} props.notifications - Array of notification messages to display
 */
export const GameLog = ({ notifications }) => {
  if (!notifications || notifications.length === 0) {
    return (
      <Box sx={gameLogStyle.content}>
        <Typography variant="body2" sx={{ fontStyle: 'italic', color: '#888' }}>
          No game activity to display
        </Typography>
      </Box>
    );
  }
  
  return (
    <Box sx={gameLogStyle.content}>
      {notifications.map((notification, index) => {
        const message = notification.message || notification;
        // Add colored indicators for different types of events
        let color = '#000';
        let icon = '•';
        
        if (message.includes('moved to')) {
          color = '#2196F3'; // Blue for movement
          icon = '➡️';
        } else if (message.includes('paid $')) {
          color = '#F44336'; // Red for payments
          icon = '💰';
        } else if (message.includes('Turn changed')) {
          color = '#4CAF50'; // Green for turn changes
          icon = '🔄';
        } else if (message.includes('purchased')) {
          color = '#FFC107'; // Amber for purchases
          icon = '🏠';
        } else if (message.includes('rolled')) {
          color = '#9C27B0'; // Purple for dice rolls
          icon = '🎲';
        }
        
        return (
          <Box 
            key={index} 
            sx={{ 
              mb: 1, 
              color, 
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1
            }}
          >
            <Typography variant="body2" sx={{ minWidth: '24px', fontWeight: 'bold' }}>
              {icon}
            </Typography>
            <Typography variant="body2">
              {message}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
}; 