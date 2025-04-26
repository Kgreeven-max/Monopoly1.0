import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';

export default function NavBar() {
  const location = useLocation();
  
  return (
    <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold', color: '#2E7D32' }}>
          Pi-nopoly
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            component={Link} 
            to="/board" 
            color={location.pathname === '/board' ? 'primary' : 'inherit'}
            variant={location.pathname === '/board' ? 'contained' : 'text'}
          >
            Game Board
          </Button>
          
          <Button 
            component={Link} 
            to="/debug" 
            color={location.pathname === '/debug' ? 'primary' : 'inherit'}
            variant={location.pathname === '/debug' ? 'contained' : 'text'}
          >
            Debug View
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
} 