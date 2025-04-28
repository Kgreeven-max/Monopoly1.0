import React, { useState, useEffect } from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton, Tooltip } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';

export default function NavBar() {
  const location = useLocation();
  const [isFullScreen, setIsFullScreen] = useState(false);
  
  // Check if browser supports fullscreen
  const fullScreenAvailable = document.fullscreenEnabled || 
                             document.webkitFullscreenEnabled || 
                             document.mozFullScreenEnabled ||
                             document.msFullscreenEnabled;
  
  // Handle fullscreen changes
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!(document.fullscreenElement || 
                         document.webkitFullscreenElement || 
                         document.mozFullScreenElement ||
                         document.msFullscreenElement));
    };
    
    document.addEventListener('fullscreenchange', handleFullScreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
    document.addEventListener('mozfullscreenchange', handleFullScreenChange);
    document.addEventListener('MSFullscreenChange', handleFullScreenChange);
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullScreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullScreenChange);
    };
  }, []);
  
  // Toggle fullscreen mode
  const toggleFullScreen = () => {
    if (!isFullScreen) {
      // Enter fullscreen
      const element = document.documentElement;
      if (element.requestFullscreen) {
        element.requestFullscreen();
      } else if (element.webkitRequestFullscreen) {
        element.webkitRequestFullscreen();
      } else if (element.mozRequestFullScreen) {
        element.mozRequestFullScreen();
      } else if (element.msRequestFullscreen) {
        element.msRequestFullscreen();
      }
    } else {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
  };
  
  return (
    <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold', color: '#2E7D32' }}>
          Pi-nopoly
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
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
          
          {fullScreenAvailable && (
            <Tooltip title={isFullScreen ? "Exit Full Screen" : "Full Screen"}>
              <IconButton 
                onClick={toggleFullScreen}
                color="primary"
                sx={{ ml: 1 }}
              >
                {isFullScreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
} 