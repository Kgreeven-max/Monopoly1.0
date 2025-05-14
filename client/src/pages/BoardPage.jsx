import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, Divider, Paper, Avatar, Chip } from '@mui/material';
import io from 'socket.io-client';
import gsap from 'gsap';
import { useSocket } from '../contexts/SocketContext';

// Custom hook for player movement animation
const usePlayerAnimation = (onCompleteLanding) => {
  const [isAnimatingMovement, setIsAnimatingMovement] = useState(false);
  const [playerMoving, setPlayerMoving] = useState(null);
  const [startPosition, setStartPosition] = useState(null);
  const [targetPosition, setTargetPosition] = useState(null);
  const [remainingSteps, setRemainingSteps] = useState(0);
  const playerTokenRefs = useRef({});
  const animationTimelineRef = useRef(null);
  
  const getPlayerTokenRef = (playerId) => (element) => {
    if (element) {
      playerTokenRefs.current[playerId] = element;
    } else {
      // Remove reference if element is unmounted
      delete playerTokenRefs.current[playerId];
    }
  };
  
  const animatePlayerMovement = (playerId, fromPosition, toPosition, steps) => {
    if (!playerTokenRefs.current[playerId]) {
      console.error(`No ref found for player ${playerId}`);
      return Promise.reject('No player ref found');
    }
    
    // Clear any existing timeline
    if (animationTimelineRef.current) {
      animationTimelineRef.current.kill();
    }
    
    // Calculate path around the board
    const path = [];
    let currentPosition = fromPosition;
    
    // Generate each step along the path
    for (let i = 0; i < steps; i++) {
      currentPosition = (currentPosition + 1) % 40; // Wrap around the board
      path.push(currentPosition);
    }
    
    setPlayerMoving(playerId);
    setIsAnimatingMovement(true);
    setStartPosition(fromPosition);
    setTargetPosition(toPosition);
    setRemainingSteps(steps);
    
    // Create animation timeline
    const timeline = gsap.timeline({
      onComplete: () => {
        setIsAnimatingMovement(false);
        setPlayerMoving(null);
        setRemainingSteps(0);
        
        // Call the landing callback if provided
        if (typeof onCompleteLanding === 'function') {
          onCompleteLanding(toPosition);
        }
      }
    });
    
    // Find all space elements
    const spaceElements = document.querySelectorAll('[data-space-id]');
    const spaceMap = {};
    
    // Create a map of spaces by ID
    spaceElements.forEach(el => {
      const id = parseInt(el.getAttribute('data-space-id'));
      spaceMap[id] = el;
    });
    
    // Define starting position - player is already here in the DOM
    // We need to get its current computed transform to use as a starting point
    // This avoids jumps at the beginning of the animation
    const startStyle = window.getComputedStyle(playerTokenRefs.current[playerId]);
    const startTransform = startStyle.transform;
    
    // Reset position to allow GSAP to handle transforms
    gsap.set(playerTokenRefs.current[playerId], {
      clearProps: "transform",
      position: "absolute",
      zIndex: 100
    });
    
    // Add sequential animations for each step
    path.forEach((pos, index) => {
      const spaceElement = spaceMap[pos];
      
      if (!spaceElement) {
        console.error(`Could not find element for space ${pos}`);
        return;
      }
      
      // Get space position relative to the board
      const spaceRect = spaceElement.getBoundingClientRect();
      const playerRect = playerTokenRefs.current[playerId].getBoundingClientRect();
      
      // Calculate center position
      const x = spaceRect.left + (spaceRect.width / 2) - (playerRect.width / 2);
      const y = spaceRect.top + (spaceRect.height * 0.7) - (playerRect.height / 2);
      
      timeline.to(playerTokenRefs.current[playerId], {
        duration: 0.4, // Duration for each step
        top: 0,
        left: 0,
        x: x,
        y: y,
        ease: "power2.inOut",
        onStart: () => {
          setRemainingSteps(steps - index - 1);
          
          // If passing Go (position 0), add visual effect
          if (pos === 0 && fromPosition !== 0) {
            gsap.to(playerTokenRefs.current[playerId], {
              duration: 0.2,
              scale: 1.3,
              backgroundColor: 'gold',
              boxShadow: '0 0 15px gold',
              yoyo: true,
              repeat: 1
            });
          }
        },
        onComplete: () => {
          // Bounce effect when landing on final space
          if (index === path.length - 1) {
            gsap.to(playerTokenRefs.current[playerId], {
              duration: 0.3,
              y: `-=10px`,
              yoyo: true,
              repeat: 1,
              ease: "power2.inOut"
            });
          }
        }
      });
    });
    
    // Store the timeline for potential interruption
    animationTimelineRef.current = timeline;
    
    // Return a promise that resolves when animation completes
    return new Promise((resolve) => {
      timeline.eventCallback('onComplete', () => {
        // Reset to original style with regular transitions
        gsap.set(playerTokenRefs.current[playerId], {
          clearProps: "transform,position,zIndex,x,y,top,left",
        });
        resolve();
      });
    });
  };
  
  return {
    isAnimatingMovement,
    playerMoving,
    remainingSteps,
    getPlayerTokenRef,
    animatePlayerMovement
  };
};

// Card data - moved to top level for easy editing
// Add new cards by simply adding new objects to these arrays
const CHANCE_CARDS = [
  { 
    id: 1, 
    title: "Advance to Go", 
    description: "Collect $200", 
    action: "move", 
    value: 0,
    color: "#FFC663"  // Standard Chance yellow color
  },
  { 
    id: 2, 
    title: "Bank error in your favor", 
    description: "Collect $200", 
    action: "collect", 
    value: 200,
    color: "#FFC663"
  },
  { 
    id: 3, 
    title: "Doctor's fees", 
    description: "Pay $50", 
    action: "pay", 
    value: 50,
    color: "#FFC663"
  },
  { 
    id: 4, 
    title: "Get out of jail free", 
    description: "This card may be kept until needed", 
    action: "getOutOfJail", 
    value: null,
    color: "#FFC663"
  },
  { 
    id: 5, 
    title: "Go to jail", 
    description: "Go directly to jail. Do not pass Go. Do not collect $200.", 
    action: "goToJail", 
    value: null,
    color: "#FFC663"
  },
  // Add more Chance cards here
  { 
    id: 6, 
    title: "Speeding fine", 
    description: "Pay $15", 
    action: "pay", 
    value: 15,
    color: "#FFC663"
  },
  { 
    id: 7, 
    title: "You've been elected", 
    description: "Pay each player $50", 
    action: "payEach", 
    value: 50,
    color: "#FFC663"
  },
  { 
    id: 8, 
    title: "Building loan matures", 
    description: "Collect $150", 
    action: "collect", 
    value: 150,
    color: "#FFC663"
  },
];

const COMMUNITY_CHEST_CARDS = [
  { 
    id: 1, 
    title: "Income tax refund", 
    description: "Collect $20", 
    action: "collect", 
    value: 20,
    color: "#CBDFF8"  // Standard Community Chest blue color
  },
  { 
    id: 2, 
    title: "Holiday fund matures", 
    description: "Collect $100", 
    action: "collect", 
    value: 100,
    color: "#CBDFF8"
  },
  { 
    id: 3, 
    title: "Pay hospital fees", 
    description: "Pay $100", 
    action: "pay", 
    value: 100,
    color: "#CBDFF8"
  },
  { 
    id: 4, 
    title: "Go to jail", 
    description: "Go directly to jail. Do not pass Go. Do not collect $200.", 
    action: "goToJail", 
    value: null,
    color: "#CBDFF8"
  },
  { 
    id: 5, 
    title: "It's your birthday", 
    description: "Collect $10 from each player", 
    action: "collectFromEach", 
    value: 10,
    color: "#CBDFF8"
  },
  // Add more Community Chest cards here
  { 
    id: 6, 
    title: "Life insurance matures", 
    description: "Collect $100", 
    action: "collect", 
    value: 100,
    color: "#CBDFF8"
  },
  { 
    id: 7, 
    title: "School fees", 
    description: "Pay $50", 
    action: "pay", 
    value: 50,
    color: "#CBDFF8"
  },
  { 
    id: 8, 
    title: "You inherit", 
    description: "Collect $100", 
    action: "collect", 
    value: 100,
    color: "#CBDFF8"
  },
  { 
    id: 9, 
    title: "From sale of stock", 
    description: "Collect $50", 
    action: "collect", 
    value: 50,
    color: "#CBDFF8"
  },
];

// Token options for player pieces
const tokenOptions = {
  car: { icon: '🚗', name: 'Car' },
  ship: { icon: '🚢', name: 'Ship' },
  hat: { icon: '🎩', name: 'Top Hat' },
  dog: { icon: '🐕', name: 'Dog' },
  cat: { icon: '🐈', name: 'Cat' },
  plane: { icon: '✈️', name: 'Airplane' },
  money: { icon: '💰', name: 'Money Bag' },
  crown: { icon: '👑', name: 'Crown' },
  boot: { icon: '👢', name: 'Boot' },
  robot: { icon: '🤖', name: 'Robot' }
};

// Helper function to get default color for a player
const getDefaultPlayerColor = (playerId) => {
  const colors = ['#ff5722', '#9c27b0', '#2196f3', '#4caf50', '#ffeb3b', '#795548', '#607d8b', '#e91e63', '#00bcd4', '#ff9800'];
  const index = typeof playerId === 'string' ? 
    Math.abs(playerId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % colors.length : 
    Math.abs(playerId) % colors.length;
  return colors[index];
};

// Helper function to get default token for a player
const getDefaultPlayerToken = (playerId) => {
  const tokens = Object.keys(tokenOptions);
  const index = typeof playerId === 'string' ? 
    Math.abs(playerId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % tokens.length : 
    Math.abs(playerId) % tokens.length;
  return tokens[index];
};

/*
  CARD TEMPLATE - Copy this to add new cards:
  
  { 
    id: 0,                       // Unique ID (increment from the last one)
    title: "Card title",         // Main card title
    description: "Description",  // Card text
    action: "action_type",       // Action type: "move", "collect", "pay", "goToJail", etc.
    value: 100,                  // Value associated with the action (amount to pay/collect, space to move to)
    color: "#CBDFF8"             // Card color - use #FFC663 for Chance, #CBDFF8 for Community Chest
  },
*/

function BoardPage() {
  // Initialize with default property data but will be updated from backend
  const [boardSpaces, setBoardSpaces] = useState([
    { id: 0, name: 'GO', type: 'corner', color: '#FFECD6' },
    { id: 1, name: 'MEDITERRANEAN AVE', price: 60, type: 'property', color: '#955436' },
    { id: 2, name: 'COMMUNITY CHEST', type: 'chest', color: '#CBDFF8' },
    { id: 3, name: 'BALTIC AVE', price: 60, type: 'property', color: '#955436' },
    { id: 4, name: 'INCOME TAX', price: 200, type: 'tax', color: '#FFFFFF' },
    { id: 5, name: 'READING RAILROAD', price: 200, type: 'railroad', color: '#000000' },
    { id: 6, name: 'ORIENTAL AVE', price: 100, type: 'property', color: '#AACCF1' },
    { id: 7, name: 'CHANCE', type: 'chance', color: '#FFC663' },
    { id: 8, name: 'VERMONT AVE', price: 100, type: 'property', color: '#AACCF1' },
    { id: 9, name: 'CONNECTICUT AVE', price: 120, type: 'property', color: '#AACCF1' },
    { id: 10, name: 'JAIL', type: 'corner', color: '#FFECD6' },
    { id: 11, name: 'ST. CHARLES PLACE', price: 140, type: 'property', color: '#D93A96' },
    { id: 12, name: 'ELECTRIC COMPANY', price: 150, type: 'utility', color: '#FFFFFF' },
    { id: 13, name: 'STATES AVE', price: 140, type: 'property', color: '#D93A96' },
    { id: 14, name: 'VIRGINIA AVE', price: 160, type: 'property', color: '#D93A96' },
    { id: 15, name: 'PENNSYLVANIA RAILROAD', price: 200, type: 'railroad', color: '#000000' },
    { id: 16, name: 'ST. JAMES PLACE', price: 180, type: 'property', color: '#F7941D' },
    { id: 17, name: 'COMMUNITY CHEST', type: 'chest', color: '#CBDFF8' },
    { id: 18, name: 'TENNESSEE AVE', price: 180, type: 'property', color: '#F7941D' },
    { id: 19, name: 'NEW YORK AVE', price: 200, type: 'property', color: '#F7941D' },
    { id: 20, name: 'FREE PARKING', type: 'corner', color: '#FFECD6' },
    { id: 21, name: 'KENTUCKY AVE', price: 220, type: 'property', color: '#ED1B24' },
    { id: 22, name: 'CHANCE', type: 'chance', color: '#FFC663' },
    { id: 23, name: 'INDIANA AVE', price: 220, type: 'property', color: '#ED1B24' },
    { id: 24, name: 'ILLINOIS AVE', price: 240, type: 'property', color: '#ED1B24' },
    { id: 25, name: 'B & O RAILROAD', price: 100, type: 'railroad', color: '#000000' },
    { id: 26, name: 'ATLANTIC AVE', price: 260, type: 'property', color: '#FEF200' },
    { id: 27, name: 'VENTNOR AVE', price: 260, type: 'property', color: '#FEF200' },
    { id: 28, name: 'WATER WORKS', price: 150, type: 'utility', color: '#FFFFFF' },
    { id: 29, name: 'MARVIN GARDENS', price: 280, type: 'property', color: '#FEF200' },
    { id: 30, name: 'GO TO JAIL', type: 'corner', color: '#FFECD6' },
    { id: 31, name: 'PACIFIC AVE', price: 300, type: 'property', color: '#0D9B4D' },
    { id: 32, name: 'NORTH CAROLINA AVE', price: 300, type: 'property', color: '#0D9B4D' },
    { id: 33, name: 'COMMUNITY CHEST', type: 'chest', color: '#CBDFF8' },
    { id: 34, name: 'PENNSYLVANIA AVE', price: 320, type: 'property', color: '#0D9B4D' },
    { id: 35, name: 'SHORT LINE RAILROAD', price: 200, type: 'railroad', color: '#000000' },
    { id: 36, name: 'CHANCE', type: 'chance', color: '#FFC663' },
    { id: 37, name: 'PARK PLACE', price: 350, type: 'property', color: '#0072BC' },
    { id: 38, name: 'LUXURY TAX', price: 112, type: 'tax', color: '#FFFFFF' },
    { id: 39, name: 'BOARDWALK', price: 400, type: 'property', color: '#0072BC' },
  ]);

  // Get socket from context
  const { socket, emit, isConnected } = useSocket();

  // Function to get position for each space
  const getPosition = (index) => {
    const side = Math.floor(index / 10); // 0=bottom, 1=left, 2=top, 3=right
    const pos = index % 10;
    
    // Different positioning based on which side of the board
    if (side === 0) return { gridRow: 11, gridColumn: 11 - pos }; // bottom row
    if (side === 1) return { gridRow: 11 - pos, gridColumn: 1 }; // left column
    if (side === 2) return { gridRow: 1, gridColumn: pos + 1 }; // top row
    if (side === 3) return { gridRow: pos + 1, gridColumn: 11 }; // right column
    
    return {}; // fallback
  };

  // Space content based on type
  const getSpaceContent = (space) => {
    const isCorner = space.type === 'corner';
    
    // Format property name to fit better
    const formatPropertyName = (name) => {
      if (name.includes(' AVE')) {
        return name.replace(' AVE', '').trim();
      }
      if (name.includes(' RAILROAD')) {
        return name.replace(' RAILROAD', '').trim();
      }
      if (name.includes(' PLACE')) {
        return name.replace(' PLACE', '').trim();
      }
      return name;
    };
    
    // Generic content for all spaces
    const genericContent = (
      <>
        {/* Space header/color bar */}
        {space.type === 'property' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: space.color,
            borderBottom: '2px solid black',
            position: 'relative',
          }}>
            {space.owner && (
              <Box 
                sx={{ 
                  position: 'absolute', 
                  top: 0, 
                  right: 0, 
                  width: '25%', 
                  height: '25%', 
                  bgcolor: (players && players.length > 0) ? 
                    players.find(p => p.id === space.owner)?.color || '#777' : 
                    '#777',
                  borderBottomLeftRadius: '50%',
                }}
              />
            )}
          </Box>
        )}
        
        {space.type === 'railroad' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: '#000000',
            color: 'white',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.4vmin' : '1.3vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            RAILROAD
          </Box>
        )}
        
        {space.type === 'utility' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: '#CCCCCC',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.4vmin' : '1.3vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            UTILITY
          </Box>
        )}
        
        {space.type === 'chance' && (
          <Box sx={{ 
            width: '100%', 
            height: '30%', 
            backgroundColor: space.color,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '2.2vmin' : '2.0vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            ?
          </Box>
        )}
        
        {space.type === 'chest' && (
          <Box sx={{ 
            width: '100%', 
            height: '30%', 
            backgroundColor: space.color,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.3vmin' : '1.2vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
            textTransform: 'uppercase',
          }}>
            COMMUNITY
          </Box>
        )}
        
        {space.type === 'tax' && (
          <Box sx={{ 
            width: '100%', 
            height: '25%', 
            backgroundColor: '#FFE5B4',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: isFullScreen ? '1.5vmin' : '1.3vmin',
            fontWeight: 'bold',
            borderBottom: '2px solid black',
          }}>
            TAX
          </Box>
        )}
        
        {/* Space name */}
        <Box sx={{ 
          px: 0.7, 
          pt: space.type !== 'corner' ? 0.7 : 0,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: isCorner ? 'center' : 'space-between',
          alignItems: 'center',
          textAlign: 'center',
        }}>
          {space.type === 'chest' && (
            <Typography 
              variant="caption" 
              sx={{ 
                fontSize: isFullScreen ? '1.3vmin' : '1.2vmin',
                fontWeight: 'bold',
                mb: 0.3,
                textTransform: 'uppercase',
              }}
            >
              CHEST
            </Typography>
          )}
          
          <Typography 
            variant="caption" 
            sx={{ 
              fontSize: isCorner 
                ? (isFullScreen ? '2.3vmin' : '2.1vmin') 
                : (isFullScreen ? '1.5vmin' : '1.3vmin'),
              fontWeight: 'bold',
              lineHeight: 1.1,
              wordBreak: 'break-word',
              width: '100%',
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
              ...(space.type === 'chest' && {display: 'none'}) // Hide duplicate text for chest spaces
            }}
          >
            {space.type === 'property' || space.type === 'railroad' ? formatPropertyName(space.name) : space.name}
          </Typography>
          
          {/* Price (if applicable) */}
          {space.price && (
            <Typography 
              variant="caption" 
              sx={{ 
                fontSize: isFullScreen ? '1.6vmin' : '1.4vmin', 
                fontWeight: 'bold',
                mt: 'auto',
                padding: '2px 0',
                width: '100%',
                textAlign: 'center',
                borderTop: '1px solid #ddd',
                // Add visual indicator for inflation
                color: inflation > 1.5 ? '#d32f2f' : 
                       inflation > 1.2 ? '#f57c00' : 'inherit',
              }}
            >
              {formatMoney(space.price)}
            </Typography>
          )}
        </Box>
      </>
    );
    
    // Special corner spaces
    if (isCorner) {
      switch(space.id) {
        case 0: // GO
          return (
            <Box sx={{ transform: 'rotate(45deg)', textAlign: 'center', padding: '5px' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.6vmin' : '2.4vmin', fontWeight: 'bold', color: 'red' }}>
                GO
              </Typography>
              <Typography sx={{ fontSize: isFullScreen ? '1.7vmin' : '1.5vmin', fontWeight: 'bold' }}>
                COLLECT $200
              </Typography>
              <Box sx={{ 
                position: 'absolute', 
                bottom: '8px', 
                right: '8px', 
                transform: 'rotate(-45deg)',
                fontSize: isFullScreen ? '1.5vmin' : '1.3vmin',
                fontWeight: 'bold',
                backgroundColor: 'rgba(255,255,255,0.7)',
                padding: '2px 5px',
                borderRadius: '2px',
              }}>
                $200
              </Box>
            </Box>
          );
        case 10: // JAIL
          return (
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.8vmin' : '2.6vmin', fontWeight: 'bold' }}>
                JAIL
              </Typography>
            </Box>
          );
        case 20: // FREE PARKING
          return (
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                FREE
              </Typography>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                PARKING
              </Typography>
            </Box>
          );
        case 30: // GO TO JAIL
          return (
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                GO TO
              </Typography>
              <Typography sx={{ fontSize: isFullScreen ? '2.4vmin' : '2.2vmin', fontWeight: 'bold' }}>
                JAIL
              </Typography>
            </Box>
          );
        default:
          return genericContent;
      }
    }
    
    return genericContent;
  };

  /**
   * Handle when a player lands on a space
   * @param {number} spaceId - The ID of the space landed on
   */
  const handleLanding = (spaceId) => {
    console.log(`Player landed on space ${spaceId}`);
    const space = boardSpaces.find(s => s.id === spaceId);
    
    if (!space) {
      console.error(`Could not find space with ID ${spaceId}`);
      return;
    }
    
    // In real implementation, the backend will trigger these events
    // This is just to provide immediate feedback for landing actions
    if (space.type === 'chance') {
      console.log('Landed on Chance space');
      // After animation completes, draw a Chance card
      if (socket) {
        setTimeout(() => drawCard('chance'), 300);
      } else {
        // Local fallback
        const randomCard = CHANCE_CARDS[Math.floor(Math.random() * CHANCE_CARDS.length)];
        setCardType('chance');
        setCardContent(randomCard);
        setShowCard(true);
        
        // Animation sequence for the card
        setCardAnimation('initial');
        setTimeout(() => setCardAnimation('flipping'), 800);
        setTimeout(() => setCardAnimation('showing'), 2000);
        setTimeout(() => setCardAnimation('flying'), 8000);
        setTimeout(() => setShowCard(false), 9500);
      }
    } 
    else if (space.type === 'chest') {
      console.log('Landed on Community Chest space');
      // After animation completes, draw a Community Chest card
      if (socket) {
        setTimeout(() => drawCard('chest'), 300);
      } else {
        // Local fallback
        const randomCard = COMMUNITY_CHEST_CARDS[Math.floor(Math.random() * COMMUNITY_CHEST_CARDS.length)];
        setCardType('chest');
        setCardContent(randomCard);
        setShowCard(true);
        
        // Animation sequence for the card
        setCardAnimation('initial');
        setTimeout(() => setCardAnimation('flipping'), 800);
        setTimeout(() => setCardAnimation('showing'), 2000);
        setTimeout(() => setCardAnimation('flying'), 8000);
        setTimeout(() => setShowCard(false), 9500);
      }
    }
    else if (space.type === 'corner' && space.id === 30) {
      console.log('Landed on Go To Jail space');
      // Visual feedback for going to jail
      // In real implementation, backend would handle this
      if (socket) {
        // Backend handles movement to jail
        console.log('Backend will handle movement to jail');
      } else {
        // Local fallback animation
        alert('Go to jail! Moving to jail space...');
        // In a real implementation, we would animate the move to jail here
      }
    }
    else if (space.type === 'tax') {
      console.log(`Landed on Tax space: ${space.name}`);
      // Visual feedback for paying tax
      // In real implementation, backend would handle this
    }
    
    // Additional landing actions can be added here
  };
  
  // Test functions for local testing
  const testChanceCard = () => {
    if (socket) {
      drawCard('chance');
    } else {
      // Fallback to local card handling
      console.log('No socket connection, using local card logic');
      const randomCard = CHANCE_CARDS[Math.floor(Math.random() * CHANCE_CARDS.length)];
      setCardType('chance');
      setCardContent(randomCard);
      setShowCard(true);
      
      // Animation sequence
      setCardAnimation('initial');
      setTimeout(() => setCardAnimation('flipping'), 800);
      setTimeout(() => setCardAnimation('showing'), 2000);
      setTimeout(() => setCardAnimation('flying'), 8000);
      setTimeout(() => setShowCard(false), 9500);
    }
  };
  
  const testChestCard = () => {
    if (socket) {
      drawCard('chest');
    } else {
      // Fallback to local card handling
      console.log('No socket connection, using local card logic');
      const randomCard = COMMUNITY_CHEST_CARDS[Math.floor(Math.random() * COMMUNITY_CHEST_CARDS.length)];
      setCardType('chest');
      setCardContent(randomCard);
      setShowCard(true);
      
      // Animation sequence
      setCardAnimation('initial');
      setTimeout(() => setCardAnimation('flipping'), 800);
      setTimeout(() => setCardAnimation('showing'), 2000);
      setTimeout(() => setCardAnimation('flying'), 8000);
      setTimeout(() => setShowCard(false), 9500);
    }
  };

  // State for game variables
  const [players, setPlayers] = useState([]);
  const [currentPlayerId, setCurrentPlayerId] = useState(null);
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [gameStarted, setGameStarted] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [inflation, setInflation] = useState(1.0);
  const [economicState, setEconomicState] = useState('stable');
  
  // Dice roll state
  const [isRolling, setIsRolling] = useState(false);
  const [diceValues, setDiceValues] = useState([1, 1]);
  const [diceAnimationStage, setDiceAnimationStage] = useState('idle'); // 'idle', 'rolling', 'result', 'moving'
  const [showRollResult, setShowRollResult] = useState(false);
  const [rollTotal, setRollTotal] = useState(0);
  
  // Card display state
  const [showCard, setShowCard] = useState(false);
  const [cardType, setCardType] = useState('chance');
  const [cardContent, setCardContent] = useState(null);
  const [cardAnimation, setCardAnimation] = useState('initial');
  
  // Container ref for fullscreen
  const containerRef = useRef(null);
  
  // Toggle fullscreen function
  const toggleFullScreen = () => {
    setIsFullScreen(!isFullScreen);
  };
  
  // Utility function to format money
  const formatMoney = (amount) => {
    return `$${amount}`;
  };
  
  // Draw card function
  const drawCard = (type) => {
    if (!socket) return;
    
    socket.emit('draw_card', {
      playerId: currentPlayerId,
      gameId: gameId,
      cardType: type
    });
  };
  
  // Updated dice roll function to use socket
  const rollDice = () => {
    if (isRolling || !socket) return; // Prevent multiple rolls or if no connection
    
    // Also check that currentPlayerId and gameId are defined
    if (!currentPlayerId || !gameId) {
      console.log('Cannot roll dice: Player ID or Game ID not initialized');
      setErrorMessage('Cannot roll dice: waiting for game initialization');
      return;
    }
    
    // Start local animation immediately for better UX
    setIsRolling(true);
    setShowRollResult(false);
    setDiceAnimationStage('rolling');
    
    // Request roll from backend
    socket.emit('roll_dice', {
      playerId: currentPlayerId,
      gameId: gameId
    });
    
    console.log(`Requesting dice roll for player ${currentPlayerId} in game ${gameId}`);
  };
  
  // Listen for dice roll events
  useEffect(() => {
    if (!socket) return;
    
    const handleDiceRolled = (data) => {
      console.log('Dice rolled:', data);
      
      // Extract roll data
      const roll = data.roll || [1, 1];
      const die1 = roll[0];
      const die2 = roll[1];
      const total = die1 + die2;
      
      // Update dice state
      setDiceValues([die1, die2]);
      setRollTotal(total);
      
      // Animation sequence
      setTimeout(() => {
        setDiceAnimationStage('result');
        
        // After showing result briefly, initiate throwing animation
        setTimeout(() => {
          setDiceAnimationStage('throwing');
          
          // After dice throw completes, show final result
          setTimeout(() => {
            setShowRollResult(true);
            
            // At this point, the dice roll is complete
            // The player_moved event will be handled separately with animation
            
            // After showing the result for a moment, end dice animation
            // But keep isRolling true until movement animation completes
            setTimeout(() => {
              setDiceAnimationStage('idle');
              setShowRollResult(false);
              
              // Note: isRolling will be set to false after movement animation completes
            }, 2000); // Display the result for 2 seconds
          }, 1500); // Time for dice to finish throwing
        }, 1000); // Time to show the initial result
      }, 1500); // Time for dice to roll
    };
    
    // Handle player movement event
    const handlePlayerMoved = (data) => {
      console.log('Player moved:', data);
      
      if (!data || !data.playerId) {
        console.error('Invalid player movement data received');
        setIsRolling(false);
        return;
      }
      
      // Extract movement data
      const playerId = data.playerId;
      const newPosition = data.newPosition || 0;
      const diceTotal = data.diceTotal || 1;
      
      // Find the player - with safeguards
      const playersList = players || [];
      
      // Fallback case if players state isn't set yet
      if (playersList.length === 0) {
        console.warn('No players loaded yet, creating temporary player');
        const tempPlayer = {
          id: playerId,
          position: 0,
          name: `Player ${playerId}`,
          color: getDefaultPlayerColor(playerId),
          token: getDefaultPlayerToken(playerId)
        };
        
        // Update with new position immediately
        const updatedPlayer = { ...tempPlayer, position: newPosition };
        setPlayers([updatedPlayer]);
        setIsRolling(false);
        return;
      }
      
      const player = playersList.find(p => p.id === playerId);
      if (!player) {
        console.error(`Player ${playerId} not found.`);
        setIsRolling(false);
        return;
      }
      
      const oldPosition = player.position || 0;
      
      // Create a local copy of player data to be updated after animation
      const updatedPlayer = { ...player, position: newPosition };
      
      // Update local player state immediately for other players
      // but animate for the current player or if we're in observer mode
      try {
        if (playerId === currentPlayerId || !currentPlayerId) {
          // Start the animation sequence
          console.log(`Animating player ${playerId} movement from ${oldPosition} to ${newPosition}`);
          
          if (typeof animatePlayerMovement === 'function') {
            // Delay the state update until animation completes
            animatePlayerMovement(playerId, oldPosition, newPosition, diceTotal)
              .then(() => {
                console.log(`Animation complete for player ${playerId}`);
                setPlayers(prevPlayers => 
                  prevPlayers.map(p => p.id === playerId ? updatedPlayer : p)
                );
                setIsRolling(false);
              })
              .catch(error => {
                console.error(`Animation failed: ${error}`);
                setPlayers(prevPlayers => 
                  prevPlayers.map(p => p.id === playerId ? updatedPlayer : p)
                );
                setIsRolling(false);
              });
          } else {
            console.warn('animatePlayerMovement function not available');
            setPlayers(prevPlayers => 
              prevPlayers.map(p => p.id === playerId ? updatedPlayer : p)
            );
            setIsRolling(false);
          }
        } else {
          // For other players, just update position without special animation
          console.log(`Updating position for player ${playerId} without animation`);
          setPlayers(prevPlayers => 
            prevPlayers.map(p => p.id === playerId ? updatedPlayer : p)
          );
          setIsRolling(false);
        }
      } catch (error) {
        console.error('Error in player movement handler:', error);
        setPlayers(prevPlayers => 
          prevPlayers.map(p => p.id === playerId ? updatedPlayer : p)
        );
        setIsRolling(false);
      }
    };
    
    // Handle errors with dice roll
    const handleDiceError = (data) => {
      console.error('Dice roll error:', data?.error || 'Unknown error');
      setIsRolling(false);
      setDiceAnimationStage('idle');
      
      // Display error message
      setErrorMessage(data?.error || 'Error with dice roll');
      
      // Auto-clear error after a few seconds
      setTimeout(() => setErrorMessage(null), 3000);
    };
    
    socket.on('dice_rolled', handleDiceRolled);
    socket.on('roll_error', handleDiceError);
    socket.on('player_moved', handlePlayerMoved);
    
    return () => {
      socket.off('dice_rolled', handleDiceRolled);
      socket.off('roll_error', handleDiceError);
      socket.off('player_moved', handlePlayerMoved);
    };
  }, [socket]); // Remove dependencies that can cause circular references or uninitialized variables
  
  // Function for 3D dice face
  const getDiceFace = (value) => {
    // Pattern of dots for each face value
    const dotPositions = {
      1: ['center'],
      2: ['top-left', 'bottom-right'],
      3: ['top-left', 'center', 'bottom-right'],
      4: ['top-left', 'top-right', 'bottom-left', 'bottom-right'],
      5: ['top-left', 'top-right', 'center', 'bottom-left', 'bottom-right'],
      6: ['top-left', 'top-right', 'middle-left', 'middle-right', 'bottom-left', 'bottom-right']
    };
    
    const getPositionStyle = (position) => {
      switch(position) {
        case 'center': return { top: '50%', left: '50%' };
        case 'top-left': return { top: '20%', left: '20%' };
        case 'top-right': return { top: '20%', left: '80%' };
        case 'middle-left': return { top: '50%', left: '20%' };
        case 'middle-right': return { top: '50%', left: '80%' };
        case 'bottom-left': return { top: '80%', left: '20%' };
        case 'bottom-right': return { top: '80%', left: '80%' };
        default: return {};
      }
    };
    
    return (
      <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
        {dotPositions[value].map((position, index) => (
          <Box
            key={index}
            sx={{
              position: 'absolute',
              width: '18%',
              height: '18%',
              borderRadius: '50%',
              backgroundColor: '#333',
              transform: 'translate(-50%, -50%)',
              ...getPositionStyle(position)
            }}
          />
        ))}
      </Box>
    );
  };
  
  // Helper function to get the final transform based on dice value
  const getDiceFinalTransform = (value) => {
    // Return the transform that will show the correct face value
    switch(value) {
      case 1: return 'rotateX(0deg) rotateY(0deg)';
      case 2: return 'rotateX(0deg) rotateY(-90deg)';
      case 3: return 'rotateX(-90deg) rotateY(0deg)';
      case 4: return 'rotateX(90deg) rotateY(0deg)';
      case 5: return 'rotateX(0deg) rotateY(90deg)';
      case 6: return 'rotateX(180deg) rotateY(0deg)';
      default: return 'rotateX(0deg) rotateY(0deg)';
    }
  };

  // Function to handle ending the current player's turn
  const endTurn = () => {
    if (!socket) return;
    
    // Also check that currentPlayerId and gameId are defined
    if (!currentPlayerId || !gameId) {
      console.log('Cannot end turn: Player ID or Game ID not initialized');
      setErrorMessage('Cannot end turn: waiting for game initialization');
      return;
    }
    
    socket.emit('end_turn', {
      playerId: currentPlayerId,
      gameId: gameId
    });
    
    console.log(`Player ${currentPlayerId} ended their turn`);
  };

  // Determine if current player can roll dice
  const canRollDice = () => {
    if (!isConnected || !gameStarted || !currentPlayer) return false;
    
    // Only current player can roll dice on their turn
    return currentPlayer.id === currentPlayerId && !isRolling;
  };

  // Determine if current player can end turn
  const canEndTurn = () => {
    if (!isConnected || !gameStarted || !currentPlayer) return false;
    
    // Only current player can end turn, and not during animations
    return currentPlayer.id === currentPlayerId && !isRolling && !isAnimatingMovement;
  };

  // Function to leave the game
  const leaveGame = () => {
    if (!socket || !currentPlayerId) return;
    
    socket.emit('leave_game', {
      playerId: currentPlayerId,
      gameId: gameId
    });
    
    // Redirect to home or another page after leaving
    // window.location.href = '/'; // Uncomment to enable redirecting
  };
  
  // Function to manually refresh the player list
  const refreshPlayers = () => {
    console.log('Attempting to refresh players...');
    
    // Try socket method first for reliability
    if (socket && isConnected) {
      console.log('Using socket to get player list...');
      socket.emit('get_all_players', { request_type: 'board_view' });
      return;
    }
    
    // Fallback to HTTP API if socket is unavailable
    // Use API_BASE_URL from environment or default to current host
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.host}`;
    
    // Use the correct API endpoint directly
    fetch(`${API_BASE_URL}/api/players`)
      .then(response => {
        console.log('Players API response status:', response.status);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        if (data && Array.isArray(data.players)) {
          console.log('Players refreshed from API:', data.players);
          
          // Format players from API response
          const formattedPlayers = data.players.map(player => ({
            id: player.id,
            name: player.username || player.name,
            cash: player.money,
            position: player.position || 0,
            color: player.color || getDefaultPlayerColor(player.id),
            token: player.token || getDefaultPlayerToken(player.id),
            inJail: player.in_jail || false,
            getOutOfJailCards: player.get_out_of_jail_cards || 0,
            isBot: player.is_bot || false
          }));
          
          setPlayers(formattedPlayers);
        } else {
          console.log('Unexpected data format from players API');
          
          // Fallback to socket if API fails
          if (socket && isConnected) {
            console.log('Falling back to socket.emit...');
            socket.emit('get_all_players', { request_type: 'board_view' });
          }
        }
      })
      .catch(error => {
        console.error('Error in player refresh process:', error);
        
        // Fallback to socket
        if (socket && isConnected) {
          console.log('Falling back to socket after error...');
          socket.emit('get_all_players', { request_type: 'board_view' });
        }
      });
    
    console.log('Manually requested player list refresh');
  };

  // Initialize game data from server
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    console.log('Socket connected, initializing game data...');
    
    // Socket event handler for player list
    const handlePlayerList = (data) => {
      if (data && data.success && Array.isArray(data.players)) {
        console.log('Received player list via socket:', data.players);
        
        // Format players from socket response
        const formattedPlayers = data.players.map(player => ({
          id: player.id,
          name: player.username || player.name,
          cash: player.money,
          position: player.position || 0,
          color: player.color || getDefaultPlayerColor(player.id),
          token: player.token || getDefaultPlayerToken(player.id),
          inJail: player.in_jail || false,
          getOutOfJailCards: player.get_out_of_jail_cards || 0,
          isBot: player.is_bot || false
        }));
        
        setPlayers(formattedPlayers);
      }
    };
    
    // Fetch game state
    socket.emit('get_game_state', {}, (response) => {
      if (response && response.success) {
        console.log('Game state received:', response.data);
        
        // Set game ID
        if (response.data.gameId) {
          setGameId(response.data.gameId);
        }
        
        // Set game started status
        setGameStarted(response.data.started || false);
        
        // Set economic data if available
        if (response.data.economicState) {
          setEconomicState(response.data.economicState);
        }
        
        if (response.data.inflation !== undefined) {
          setInflation(response.data.inflation);
        }
      }
    });
    
    // Get player ID from authentication
    socket.emit('get_current_player', {}, (response) => {
      if (response && response.success && response.player) {
        console.log('Current player received:', response.player);
        setCurrentPlayerId(response.player.id);
      }
    });
    
    // Fetch all players
    socket.emit('get_all_players', { request_type: 'board_view' });
    
    // Listen for player updates
    const handlePlayersUpdate = (data) => {
      if (data && Array.isArray(data.players)) {
        console.log('Players updated:', data);
        setPlayers(data.players);
      }
    };
    
    // Listen for game state updates
    const handleGameStateUpdate = (data) => {
      console.log('Game state updated:', data);
      
      if (data) {
        // Update game started status
        if (data.started !== undefined) {
          setGameStarted(data.started);
        }
        
        // Update economic state
        if (data.economicState) {
          setEconomicState(data.economicState);
        }
        
        if (data.inflation !== undefined) {
          setInflation(data.inflation);
        }
        
        // Update current player ID if turn changed
        if (data.currentPlayerId) {
          setCurrentPlayerId(data.currentPlayerId);
        }
      }
    };
    
    socket.on('players_updated', handlePlayersUpdate);
    socket.on('game_state_updated', handleGameStateUpdate);
    socket.on('all_players_list', handlePlayerList);
    
    // Auto-refresh players every 5 seconds
    const playerRefreshInterval = setInterval(refreshPlayers, 5000);
    
    return () => {
      socket.off('players_updated', handlePlayersUpdate);
      socket.off('game_state_updated', handleGameStateUpdate);
      socket.off('all_players_list', handlePlayerList);
      clearInterval(playerRefreshInterval);
    };
  }, [socket, isConnected]);
  
  // Update current player whenever players or currentPlayerId changes
  useEffect(() => {
    if (currentPlayerId && players && players.length > 0) {
      const player = players.find(p => p.id === currentPlayerId);
      if (player) {
        setCurrentPlayer(player);
      }
    }
  }, [players, currentPlayerId]);

  // Use our custom animation hook
  const {
    isAnimatingMovement,
    playerMoving,
    remainingSteps,
    getPlayerTokenRef,
    animatePlayerMovement
  } = usePlayerAnimation((spaceId) => {
    // Handle landing on special spaces
    console.log(`Player landed on space ${spaceId}`);
    const space = boardSpaces.find(s => s.id === spaceId);
    
    if (!space) {
      console.error(`Could not find space with ID ${spaceId}`);
      return;
    }
    
    // In real implementation, the backend will trigger these events
    // This is just to provide immediate feedback for landing actions
    if (space.type === 'chance') {
      console.log('Landed on Chance space');
      // After animation completes, draw a Chance card
      if (socket) {
        setTimeout(() => drawCard('chance'), 300);
      } else {
        // Local fallback
        const randomCard = CHANCE_CARDS[Math.floor(Math.random() * CHANCE_CARDS.length)];
        setCardType('chance');
        setCardContent(randomCard);
        setShowCard(true);
        
        // Animation sequence for the card
        setCardAnimation('initial');
        setTimeout(() => setCardAnimation('flipping'), 800);
        setTimeout(() => setCardAnimation('showing'), 2000);
        setTimeout(() => setCardAnimation('flying'), 8000);
        setTimeout(() => setShowCard(false), 9500);
      }
    } 
    else if (space.type === 'chest') {
      console.log('Landed on Community Chest space');
      // After animation completes, draw a Community Chest card
      if (socket) {
        setTimeout(() => drawCard('chest'), 300);
      } else {
        // Local fallback
        const randomCard = COMMUNITY_CHEST_CARDS[Math.floor(Math.random() * COMMUNITY_CHEST_CARDS.length)];
        setCardType('chest');
        setCardContent(randomCard);
        setShowCard(true);
        
        // Animation sequence for the card
        setCardAnimation('initial');
        setTimeout(() => setCardAnimation('flipping'), 800);
        setTimeout(() => setCardAnimation('showing'), 2000);
        setTimeout(() => setCardAnimation('flying'), 8000);
        setTimeout(() => setShowCard(false), 9500);
      }
    }
    else if (space.type === 'corner' && space.id === 30) {
      console.log('Landed on Go To Jail space');
      // Visual feedback for going to jail
      // In real implementation, backend would handle this
      if (socket) {
        // Backend handles movement to jail
        console.log('Backend will handle movement to jail');
      } else {
        // Local fallback animation
        alert('Go to jail! Moving to jail space...');
        // In a real implementation, we would animate the move to jail here
      }
    }
    else if (space.type === 'tax') {
      console.log(`Landed on Tax space: ${space.name}`);
      // Visual feedback for paying tax
      // In real implementation, backend would handle this
    }
  });

  return (
    <Box 
      ref={containerRef}
      sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', md: 'row' },
        height: '100vh', 
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: '#C5E8D2', // Add Monopoly green background
        position: 'relative' // Added for absolute positioning of cards
      }}
    >
      {/* Connection status and errors */}
      {!isConnected && (
        <Box sx={{
          position: 'absolute',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          backgroundColor: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Box sx={{ 
            width: '10px', 
            height: '10px', 
            borderRadius: '50%', 
            backgroundColor: 'red',
            animation: 'pulse 1.5s infinite' 
          }} />
          <Typography variant="body2">
            Connecting to game server...
          </Typography>
        </Box>
      )}

      {errorMessage && (
        <Box sx={{
          position: 'absolute',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          backgroundColor: 'rgba(220,0,0,0.8)',
          color: 'white',
          padding: '8px 16px',
          borderRadius: '4px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
        }}>
          <Typography variant="body2">{errorMessage}</Typography>
        </Box>
      )}
      
      {/* Player movement animation indicator */}
      {isAnimatingMovement && (
        <Box sx={{
          position: 'absolute',
          top: '70px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          backgroundColor: 'rgba(255,255,255,0.9)',
          color: '#333',
          padding: '8px 16px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          boxShadow: '0 0 15px rgba(255, 215, 0, 0.5)',
          border: '2px solid gold',
          animation: 'pulse 1s infinite alternate'
        }}>
          <Box sx={{ 
            width: '12px', 
            height: '12px', 
            borderRadius: '50%', 
            backgroundColor: 'gold',
            animation: 'pulse 0.8s infinite alternate' 
          }} />
          <Typography variant="body1" fontWeight="bold">
            Moving {remainingSteps > 0 ? `(${remainingSteps} steps remaining)` : '...'}
          </Typography>
        </Box>
      )}

      {/* Board Container (left/top) */}
      <Box sx={{ 
        flex: { xs: '1', md: '3' }, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        p: isFullScreen ? 0 : 2,
        overflow: 'hidden',
        backgroundColor: '#C5E8D2', // Match Monopoly green
      }}>
        <Box 
          onClick={toggleFullScreen}
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(11, 1fr)',
            gridTemplateRows: 'repeat(11, 1fr)',
            width: isFullScreen ? '99vmin' : '92vmin',
            height: isFullScreen ? '99vmin' : '92vmin',
            maxWidth: isFullScreen ? 'none' : '900px',
            maxHeight: isFullScreen ? 'none' : '900px',
            gap: 0.7, // Increased gap between spaces
            border: '4px solid #333',
            backgroundColor: '#C5E8D2', // Classic Monopoly green
            padding: 0.7, // Increased padding
            boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
            borderRadius: 3,
            position: 'relative',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
        >
          {/* Center area */}
          <Box sx={{ 
            gridRow: '2 / 11', 
            gridColumn: '2 / 11',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative'
          }}>
            {/* Game Title */}
            <Box sx={{ 
              transform: 'rotate(-45deg)',
              fontSize: '5vmin', // Slightly smaller to make room for cards
              fontWeight: 'bold',
              color: '#CC0000', // Monopoly red
              textShadow: '2px 2px 4px rgba(0,0,0,0.3)',
              letterSpacing: '-0.05em',
              fontFamily: 'Arial, sans-serif',
              marginBottom: '6vmin' // Increased space between title and cards
            }}>
              CAPITAL WARS
            </Box>
            
            {/* Card decks */}
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-around', 
              width: '80%',
              marginTop: '8vmin' // Increased to move cards down
            }}>
              {/* Community Chest */}
              <Box sx={{
                width: '15vmin',
                height: '10vmin',
                backgroundColor: '#CBDFF8', // Match Community Chest color
                border: '2px solid #333',
                borderRadius: '0.8vmin',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                boxShadow: '0 0.4vmin 0.8vmin rgba(0,0,0,0.3)',
                position: 'relative',
                transform: 'rotate(-5deg)',
                '&::after': {
                  content: '""',
                  position: 'absolute',
                  top: '0.5vmin',
                  left: '0.5vmin',
                  right: '0.5vmin',
                  bottom: '0.5vmin',
                  border: '1px solid rgba(0,0,0,0.2)',
                  borderRadius: '0.4vmin',
                  pointerEvents: 'none'
                }
              }}>
                <Typography sx={{ 
                  fontSize: '1.6vmin', 
                  fontWeight: 'bold',
                  textAlign: 'center',
                  color: '#333',
                  mb: '0.3vmin',
                  textTransform: 'uppercase'
                }}>
                  Community
                </Typography>
                <Typography sx={{ 
                  fontSize: '1.6vmin', 
                  fontWeight: 'bold',
                  textAlign: 'center',
                  color: '#333',
                  textTransform: 'uppercase'
                }}>
                  Chest
                </Typography>
                
                {/* Card stack effect */}
                <Box sx={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#CBDFF8',
                  border: '2px solid #333',
                  borderRadius: '0.8vmin',
                  transform: 'rotate(3deg) translate(-0.2vmin, -0.2vmin)',
                  zIndex: -1
                }} />
                <Box sx={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#CBDFF8',
                  border: '2px solid #333',
                  borderRadius: '0.8vmin',
                  transform: 'rotate(6deg) translate(-0.4vmin, -0.4vmin)',
                  zIndex: -2
                }} />
              </Box>
              
              {/* Chance */}
              <Box sx={{
                width: '15vmin',
                height: '10vmin',
                backgroundColor: '#FFC663', // Match Chance color
                border: '2px solid #333',
                borderRadius: '0.8vmin',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                boxShadow: '0 0.4vmin 0.8vmin rgba(0,0,0,0.3)',
                position: 'relative',
                transform: 'rotate(5deg)',
                '&::after': {
                  content: '""',
                  position: 'absolute',
                  top: '0.5vmin',
                  left: '0.5vmin',
                  right: '0.5vmin',
                  bottom: '0.5vmin',
                  border: '1px solid rgba(0,0,0,0.2)',
                  borderRadius: '0.4vmin',
                  pointerEvents: 'none'
                }
              }}>
                <Typography sx={{ 
                  fontSize: '4vmin', 
                  fontWeight: 'bold',
                  textAlign: 'center',
                  color: '#333'
                }}>
                  ?
                </Typography>
                <Typography sx={{ 
                  fontSize: '1.6vmin', 
                  fontWeight: 'bold',
                  textAlign: 'center',
                  color: '#333',
                  position: 'absolute',
                  bottom: '0.8vmin',
                  textTransform: 'uppercase'
                }}>
                  Chance
                </Typography>
                
                {/* Card stack effect */}
                <Box sx={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#FFC663',
                  border: '2px solid #333',
                  borderRadius: '0.8vmin',
                  transform: 'rotate(-3deg) translate(0.2vmin, -0.2vmin)',
                  zIndex: -1
                }} />
                <Box sx={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#FFC663',
                  border: '2px solid #333',
                  borderRadius: '0.8vmin',
                  transform: 'rotate(-6deg) translate(0.4vmin, -0.4vmin)',
                  zIndex: -2
                }} />
              </Box>
            </Box>
          </Box>
          
          {/* Board spaces */}
          {boardSpaces.map(space => {
            const pos = getPosition(space.id);
            const isCorner = space.id % 10 === 0;
            
            // Players on this space
            const playersHere = players.filter(p => p.position === space.id);
            
            return (
              <Box 
                key={space.id}
                data-space-id={space.id}
                sx={{
                  ...pos,
                  backgroundColor: 'white',
                  border: '1px solid #333',
                  borderRadius: '2px',
                  ...(isCorner && {
                    gridRow: pos.gridRow,
                    gridColumn: pos.gridColumn,
                    backgroundColor: space.color,
                    position: 'relative',
                    borderRadius: '4px',
                  }),
                  display: 'flex',
                  flexDirection: 'column',
                  padding: 0,
                  position: 'relative',
                  overflow: 'hidden', 
                  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                  // Make the corner spaces a bit larger
                  ...(isCorner && isFullScreen && {
                    transform: 'scale(1.05)',
                    zIndex: 5
                  }),
                  // Make all spaces slightly larger
                  transform: isFullScreen ? 'scale(1.04)' : 'scale(1.02)', // Increased scale for better visibility
                  zIndex: 1
                }}
              >
                {getSpaceContent(space)}
                
                {/* Player tokens */}
                {playersHere.length > 0 && (
                  <Box sx={{ 
                    position: 'absolute',
                    bottom: '3px',
                    left: 0,
                    right: 0,
                    display: 'flex', 
                    flexWrap: 'wrap',
                    gap: '3px',
                    justifyContent: 'center',
                    zIndex: 10
                  }}>
                    {playersHere.map(player => (
                      <Box 
                        key={player.id}
                        ref={getPlayerTokenRef(player.id)}
                        data-player-id={player.id}
                        sx={{
                          width: isFullScreen ? '3.2vmin' : '2.8vmin',
                          height: isFullScreen ? '3.2vmin' : '2.8vmin',
                          borderRadius: '50%',
                          background: `radial-gradient(circle at 30% 30%, ${player.color || '#cccccc'}, ${darkenColor(player.color || '#cccccc', 30)})`,
                          border: player.id === currentPlayerId ? '2px solid gold' : '1px solid rgba(0,0,0,0.5)',
                          boxShadow: player.id === currentPlayerId 
                            ? '0 0 8px gold, 0 2px 5px rgba(0,0,0,0.4), inset 0 -2px 5px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5)' 
                            : '0 2px 5px rgba(0,0,0,0.4), inset 0 -2px 5px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          fontSize: isFullScreen ? '1.8vmin' : '1.6vmin',
                          transform: 'translateY(-5px) perspective(500px) rotateX(10deg)',
                          transformStyle: 'preserve-3d',
                          transition: isAnimatingMovement && player.id === playerMoving 
                            ? 'none' // Disable transition during GSAP animation
                            : 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                          position: 'relative',
                          overflow: 'visible',
                          '&:hover': {
                            transform: 'translateY(-10px) perspective(500px) rotateX(15deg) scale(1.15)',
                            boxShadow: player.id === currentPlayerId 
                              ? '0 0 12px gold, 0 8px 16px rgba(0,0,0,0.4), inset 0 -2px 5px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5)'
                              : '0 8px 16px rgba(0,0,0,0.4), inset 0 -2px 5px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5)',
                            zIndex: 10
                          },
                          '&::after': {
                            content: '""',
                            position: 'absolute',
                            width: '100%',
                            height: '20%',
                            bottom: '-10%',
                            left: '0',
                            backgroundColor: 'rgba(0,0,0,0.2)',
                            filter: 'blur(4px)',
                            borderRadius: '50%',
                            zIndex: -1,
                            transition: 'all 0.3s ease',
                            transform: 'rotateX(60deg) scale(0.8, 0.4)',
                          },
                          '&:hover::after': {
                            width: '120%',
                            left: '-10%',
                            filter: 'blur(6px)',
                          }
                        }}
                      >
                        <Box sx={{
                          fontSize: isFullScreen ? '2.2vmin' : '2vmin',
                          filter: 'drop-shadow(0 1px 1px rgba(0,0,0,0.5))',
                          transform: 'translateZ(5px)',
                        }}>
                          {(tokenOptions[player.token] && tokenOptions[player.token].icon) || player.id || '?'}
                        </Box>
                      </Box>
                    ))}
                  </Box>
                )}
              </Box>
            );
          })}
        </Box>
      </Box>
      
      {/* Player Dashboard (right/bottom) */}
      <Box 
        sx={{ 
          flex: { xs: 'auto', md: '0 0 320px' },
          height: { xs: 'auto', md: '100%' },
          borderLeft: { xs: 'none', md: '2px solid #ccc' },
          borderTop: { xs: '2px solid #ccc', md: 'none' },
          overflow: 'auto',
          backgroundColor: '#f9f9f9',
          boxShadow: '-2px 0 10px rgba(0,0,0,0.1)'
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2, textAlign: 'center', color: '#333' }}>
            Game Dashboard
          </Typography>
          
          {/* Game not started message */}
          {!gameStarted && (
            <Paper elevation={3} sx={{ p: 2, mb: 3, textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                Waiting for Game to Start
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                The game has not started yet. Please wait for an admin to start the game.
              </Typography>
              <Box sx={{ 
                width: '20px', 
                height: '20px', 
                borderRadius: '50%', 
                backgroundColor: isConnected ? '#4CAF50' : '#f44336',
                margin: '0 auto',
                boxShadow: '0 0 10px rgba(0,0,0,0.2)'
              }} />
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Status: {isConnected ? 'Connected' : 'Disconnected'}
              </Typography>
            </Paper>
          )}
          
          {/* Current player */}
          {gameStarted && currentPlayer && (
            <Paper elevation={3} sx={{ 
              p: 2, 
              mb: 3, 
              backgroundColor: alpha(currentPlayer?.color || '#cccccc', 0.15), 
              borderRadius: '10px',
              border: currentPlayer?.id === currentPlayerId ? '2px solid gold' : 'none' 
            }}>
              <Typography variant="h6" gutterBottom sx={{ textAlign: 'center', borderBottom: '1px solid rgba(0,0,0,0.1)', pb: 1 }}>
                {currentPlayer?.id === currentPlayerId ? 'Your Turn' : 'Current Turn'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'center' }}>
                <Avatar sx={{ bgcolor: currentPlayer?.color || '#cccccc', mr: 2, width: 40, height: 40, boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}>
                  {tokenOptions[currentPlayer?.token || 'car']?.icon || currentPlayer?.name?.charAt(0) || '?'}
                </Avatar>
                <Typography variant="body1" fontWeight="bold" fontSize="1.1rem">
                  {currentPlayer?.name || 'Player'}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, px: 1 }}>
                <Typography variant="body2" fontWeight="medium">Cash:</Typography>
                <Typography variant="body2" fontWeight="bold" fontSize="1rem">${currentPlayer?.cash || 0}</Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', px: 1 }}>
                <Typography variant="body2" fontWeight="medium">Position:</Typography>
                <Typography variant="body2" fontWeight="bold" fontSize="1rem">
                  Space {currentPlayer?.position || 0}
                  {currentPlayer?.position !== undefined && boardSpaces[currentPlayer.position]?.name && ` (${boardSpaces[currentPlayer.position].name})`}
                </Typography>
              </Box>
              
              {currentPlayer?.inJail && (
                <Box sx={{ 
                  mt: 1, 
                  p: 1, 
                  backgroundColor: 'rgba(244, 67, 54, 0.1)', 
                  borderRadius: '4px',
                  border: '1px dashed #f44336'
                }}>
                  <Typography variant="body2" sx={{ color: '#d32f2f', textAlign: 'center' }}>
                    In Jail {currentPlayer?.getOutOfJailCards > 0 && `(${currentPlayer.getOutOfJailCards} Get Out of Jail Free card${currentPlayer.getOutOfJailCards > 1 ? 's' : ''})`}
                  </Typography>
                </Box>
              )}
              
              <Box sx={{ mt: 2 }}>
                <Button 
                  variant="contained" 
                  fullWidth 
                  sx={{ 
                    mb: 1, 
                    bgcolor: '#4CAF50', 
                    '&:hover': { bgcolor: '#388E3C' },
                    fontWeight: 'bold',
                    py: 1,
                    boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
                  }}
                  onClick={rollDice}
                  disabled={!canRollDice()}
                >
                  {isRolling ? 'Rolling...' : 'Roll Dice'}
                </Button>
                <Button 
                  variant="outlined" 
                  fullWidth
                  sx={{
                    borderColor: '#4CAF50',
                    color: '#4CAF50',
                    '&:hover': { borderColor: '#388E3C', bgcolor: 'rgba(76, 175, 80, 0.05)' },
                    fontWeight: 'medium'
                  }}
                  onClick={endTurn}
                  disabled={!canEndTurn()}
                >
                  End Turn
                </Button>
              </Box>
            </Paper>
          )}
          
          {/* All players */}
          <Paper elevation={2} sx={{ mb: 3, borderRadius: '10px', overflow: 'hidden' }}>
            <Box sx={{ 
              p: 1.5, 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              bgcolor: '#f5f5f5', 
              borderBottom: '1px solid #eee' 
            }}>
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                Players {players.length > 0 ? `(${players.length})` : ''}
              </Typography>
              <Button 
                size="small" 
                variant="text" 
                onClick={refreshPlayers}
                startIcon={<span>🔄</span>}
                disabled={!isConnected}
              >
                Refresh
              </Button>
            </Box>
            <Box>
              {players.length > 0 ? (
                players.map(player => (
                  <Box 
                    key={player.id}
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      p: 1.5,
                      borderBottom: '1px solid #eee',
                      bgcolor: player.id === currentPlayerId ? alpha(player.color, 0.1) : 'transparent',
                      transition: 'background-color 0.3s ease'
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box 
                        sx={{ 
                          width: 36, 
                          height: 36, 
                          borderRadius: '50%', 
                          background: `radial-gradient(circle at 30% 30%, ${player.color}, ${darkenColor(player.color, 30)})`,
                          mr: 1.5,
                          border: '1px solid rgba(0,0,0,0.3)',
                          boxShadow: '0 3px 6px rgba(0,0,0,0.2), inset 0 -2px 5px rgba(0,0,0,0.2), inset 0 2px 5px rgba(255,255,255,0.4)',
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          fontSize: '20px',
                          position: 'relative',
                          transformStyle: 'preserve-3d',
                          transform: 'perspective(500px) rotateX(10deg)',
                          '&::after': {
                            content: '""',
                            position: 'absolute',
                            width: '90%',
                            height: '15%',
                            bottom: '-8%',
                            left: '5%',
                            backgroundColor: 'rgba(0,0,0,0.2)',
                            filter: 'blur(3px)',
                            borderRadius: '50%',
                            zIndex: -1,
                            transform: 'rotateX(60deg) scale(1, 0.4)',
                          }
                        }} 
                      >
                        <Box sx={{
                          fontSize: '22px',
                          filter: 'drop-shadow(0 1px 1px rgba(0,0,0,0.5))',
                          transform: 'translateZ(2px)',
                        }}>
                          {tokenOptions[player.token]?.icon}
                        </Box>
                      </Box>
                      <Box>
                        <Typography variant="body2" fontWeight={player.id === currentPlayerId ? 'bold' : 'medium'}>
                          {player.name}
                          {player.id === currentPlayerId && " (You)"}
                        </Typography>
                        {player.isBot && (
                          <Typography variant="caption" sx={{ 
                            display: 'inline-block',
                            bgcolor: 'rgba(33, 150, 243, 0.1)',
                            color: '#1976d2',
                            px: 0.8,
                            py: 0.2,
                            borderRadius: 1,
                            fontSize: '0.65rem'
                          }}>
                            Bot
                          </Typography>
                        )}
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                      <Typography variant="body2" fontWeight="bold" fontSize="0.95rem">${player.cash}</Typography>
                      {player.inJail && (
                        <Chip
                          label="In Jail"
                          size="small"
                          sx={{ 
                            height: '18px', 
                            fontSize: '0.65rem', 
                            mt: 0.5,
                            backgroundColor: 'rgba(244, 67, 54, 0.1)',
                            color: '#d32f2f',
                            border: '1px solid #d32f2f'
                          }}
                        />
                      )}
                    </Box>
                  </Box>
                ))
              ) : (
                <Box sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    {isConnected ? 
                      "No players found. Add players or bots from the Admin panel." : 
                      "Connecting to server..."}
                  </Typography>
                  {isConnected && (
                    <Button
                      size="small"
                      variant="outlined"
                      sx={{ mt: 1 }}
                      onClick={refreshPlayers}
                    >
                      Refresh Players
                    </Button>
                  )}
                </Box>
              )}
            </Box>
          </Paper>
          
          {/* Game state and economic info */}
          <Paper elevation={2} sx={{ mb: 3, borderRadius: '10px', overflow: 'hidden' }}>
            <Typography variant="h6" sx={{ p: 1.5, fontWeight: 'bold', bgcolor: '#f5f5f5', borderBottom: '1px solid #eee' }}>
              Game Info
            </Typography>
            <Box sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" fontWeight="medium">Economy:</Typography>
                <Typography 
                  variant="body2" 
                  fontWeight="bold" 
                  sx={{ 
                    color: economicState === 'recession' ? '#d32f2f' : 
                           economicState === 'boom' ? '#388E3C' : 
                           economicState === 'unstable' ? '#FB8C00' : '#1976D2'
                  }}
                >
                  {economicState.charAt(0).toUpperCase() + economicState.slice(1)}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" fontWeight="medium">Inflation:</Typography>
                <Typography 
                  variant="body2" 
                  fontWeight="bold"
                  sx={{ 
                    color: inflation > 2 ? '#d32f2f' : 
                           inflation > 1.5 ? '#FB8C00' : 
                           inflation < 0.7 ? '#1976D2' : 'inherit'
                  }}
                >
                  {(inflation * 100).toFixed(1)}%
                </Typography>
              </Box>
              
              {gameId && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                  <Typography variant="body2" fontWeight="medium">Game ID:</Typography>
                  <Typography variant="body2" fontSize="0.75rem" sx={{ opacity: 0.7 }}>
                    {gameId.slice(0, 8)}...
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
          
          {/* Game controls */}
          <Paper elevation={2} sx={{ borderRadius: '10px', overflow: 'hidden' }}>
            <Typography variant="h6" sx={{ p: 1.5, fontWeight: 'bold', bgcolor: '#f5f5f5', borderBottom: '1px solid #eee' }}>
              Game Controls
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, p: 1.5 }}>
              <Button 
                variant="outlined" 
                size="medium" 
                onClick={toggleFullScreen}
                startIcon={isFullScreen ? <span>⤧</span> : <span>⤢</span>}
                sx={{ 
                  fontWeight: 'medium',
                  borderColor: '#2196F3',
                  color: '#2196F3',
                  '&:hover': { borderColor: '#1976D2', bgcolor: 'rgba(33, 150, 243, 0.05)' }
                }}
              >
                {isFullScreen ? 'Exit Fullscreen' : 'Fullscreen'}
              </Button>
              
              {/* Test Card Buttons */}
              <Button 
                variant="outlined"
                size="medium"
                onClick={testChanceCard}
                sx={{ 
                  fontWeight: 'medium',
                  borderColor: '#FFC663',
                  color: '#333',
                  bgcolor: 'rgba(255, 198, 99, 0.1)',
                  '&:hover': { bgcolor: 'rgba(255, 198, 99, 0.2)' },
                  mb: 1
                }}
                disabled={!isConnected}
              >
                Test Chance Card
              </Button>
              <Button 
                variant="outlined"
                size="medium"
                onClick={testChestCard}
                sx={{ 
                  fontWeight: 'medium',
                  borderColor: '#CBDFF8',
                  color: '#333',
                  bgcolor: 'rgba(203, 223, 248, 0.1)',
                  '&:hover': { bgcolor: 'rgba(203, 223, 248, 0.2)' },
                  mb: 1
                }}
                disabled={!isConnected}
              >
                Test Community Chest
              </Button>
              
              <Button 
                variant="outlined" 
                size="medium" 
                color="error"
                sx={{ fontWeight: 'medium' }}
                onClick={leaveGame}
                disabled={!isConnected || !gameStarted}
              >
                Leave Game
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>
      
      {/* 3D Dice Animation */}
      {diceAnimationStage !== 'idle' && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 900,
            pointerEvents: 'none',
          }}
        >
          {/* Dice container */}
          <Box
            sx={{
              display: 'flex',
              gap: '20px',
              perspective: '1200px',
              transformStyle: 'preserve-3d',
              position: 'absolute',
              // Different positioning based on animation stage
              ...(diceAnimationStage === 'rolling' && {
                bottom: '50%',
                left: '50%',
                transform: 'translate(-50%, 0)',
              }),
              ...(diceAnimationStage === 'result' && {
                bottom: '50%',
                left: '50%',
                transform: 'translate(-50%, 0)',
              }),
              ...(diceAnimationStage === 'throwing' && {
                animation: 'diceThrowing 1.5s ease-out forwards',
                bottom: '50%',
                left: '50%',
                transform: 'translate(-50%, 0)',
              }),
              '@keyframes diceThrowing': {
                '0%': {
                  bottom: '50%',
                  left: '50%',
                  transform: 'translate(-50%, 0) scale(1)',
                },
                '50%': {
                  bottom: '60%',
                  left: '40%',
                  transform: 'translate(-50%, -30px) scale(1.1)',
                },
                '100%': {
                  bottom: '55%',
                  left: '30%',
                  transform: 'translate(-50%, 0) scale(1)',
                }
              }
            }}
          >
            {/* First die */}
            <Box
              sx={{
                width: '60px',
                height: '60px',
                position: 'relative',
                transformStyle: 'preserve-3d',
                animation: diceAnimationStage === 'rolling' 
                  ? 'firstDiceRoll 1.5s ease-out forwards'
                  : diceAnimationStage === 'throwing'
                    ? 'firstDiceThrown 1.5s ease-out forwards'
                    : diceAnimationStage === 'result'
                      ? 'slowSpin 1s ease-out'
                      : 'none',
                transform: diceAnimationStage === 'result' || diceAnimationStage === 'throwing'
                  ? getDiceFinalTransform(diceValues[0])
                  : 'rotateX(0deg) rotateY(0deg) rotateZ(0deg)',
                '@keyframes firstDiceRoll': {
                  '0%': { transform: 'rotateX(0deg) rotateY(0deg) rotateZ(0deg)' },
                  '20%': { transform: 'rotateX(180deg) rotateY(90deg) rotateZ(0deg)' },
                  '40%': { transform: 'rotateX(360deg) rotateY(180deg) rotateZ(0deg)' },
                  '60%': { transform: 'rotateX(540deg) rotateY(270deg) rotateZ(0deg)' },
                  '80%': { transform: 'rotateX(720deg) rotateY(360deg) rotateZ(0deg)' },
                  '100%': { transform: getDiceFinalTransform(diceValues[0]) }
                },
                '@keyframes firstDiceThrown': {
                  '0%': { transform: `${getDiceFinalTransform(diceValues[0])}` },
                  '50%': { transform: `${getDiceFinalTransform(diceValues[0])} rotateX(180deg)` },
                  '100%': { transform: getDiceFinalTransform(diceValues[0]) }
                },
                '@keyframes slowSpin': {
                  '0%': { transform: 'rotateX(0deg) rotateY(0deg) rotateZ(0deg)' },
                  '100%': { transform: getDiceFinalTransform(diceValues[0]) }
                },
                '@keyframes diceSmallBounce': {
                  '0%': { transform: `${getDiceFinalTransform(diceValues[0])} translateZ(0px)` },
                  '50%': { transform: `${getDiceFinalTransform(diceValues[0])} translateZ(15px)` },
                  '100%': { transform: `${getDiceFinalTransform(diceValues[0])} translateZ(5px)` }
                },
                boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
              }}
            >
              {/* Die faces */}
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(0deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(1)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(180deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(6)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(2)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(-90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(5)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateX(90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(3)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateX(-90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(4)}
              </Box>
            </Box>
            
            {/* Second die */}
            <Box
              sx={{
                width: '60px',
                height: '60px',
                position: 'relative',
                transformStyle: 'preserve-3d',
                animation: diceAnimationStage === 'rolling' 
                  ? 'secondDiceRoll 1.5s ease-out forwards'
                  : diceAnimationStage === 'throwing'
                    ? 'secondDiceThrown 1.5s ease-out forwards'
                    : diceAnimationStage === 'result'
                      ? 'slowSpin 1s ease-out'
                      : 'none',
                transform: diceAnimationStage === 'result' || diceAnimationStage === 'throwing'
                  ? getDiceFinalTransform(diceValues[1])
                  : 'rotateX(0deg) rotateY(0deg) rotateZ(0deg)',
                '@keyframes secondDiceRoll': {
                  '0%': { transform: 'rotateX(0deg) rotateY(0deg) rotateZ(0deg)' },
                  '25%': { transform: 'rotateX(270deg) rotateY(90deg) rotateZ(0deg)' },
                  '50%': { transform: 'rotateX(540deg) rotateY(180deg) rotateZ(0deg)' },
                  '75%': { transform: 'rotateX(720deg) rotateY(270deg) rotateZ(0deg)' },
                  '100%': { transform: getDiceFinalTransform(diceValues[1]) }
                },
                '@keyframes secondDiceThrown': {
                  '0%': { transform: `${getDiceFinalTransform(diceValues[1])}` },
                  '50%': { transform: `${getDiceFinalTransform(diceValues[1])} rotateY(180deg)` },
                  '100%': { transform: getDiceFinalTransform(diceValues[1]) }
                },
                boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
              }}
            >
              {/* Die faces */}
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(0deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(1)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(180deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(6)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(2)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateY(-90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(5)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateX(90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(3)}
              </Box>
              <Box sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '8px',
                transform: 'rotateX(-90deg) translateZ(30px)',
                boxShadow: '0 0 10px rgba(0,0,0,0.25)',
              }}>
                {getDiceFace(4)}
              </Box>
            </Box>
          </Box>
          
          {/* Roll result display - Capital Wars themed */}
          {showRollResult && (
            <Box
              sx={{
                position: 'absolute',
                top: '40%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                background: '#C5E8D2', // Match game background
                borderRadius: '8px',
                padding: '12px 15px',
                display: 'flex',
                alignItems: 'center',
                boxShadow: '0 4px 10px rgba(0,0,0,0.25)',
                border: '2px solid #333',
                animation: 'fadeIn 0.3s ease-out',
                zIndex: 1000,
                gap: '12px',
                minWidth: '120px',
                '@keyframes fadeIn': {
                  '0%': { opacity: 0 },
                  '100%': { opacity: 1 }
                }
              }}
            >
              {/* Dice result */}
              <Box sx={{
                backgroundColor: rollTotal === 7 || rollTotal === 11 ? '#FFEB3B' : 'white',
                borderRadius: '6px',
                width: '50px',
                height: '50px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                border: '1px solid #333',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
              }}>
                <Typography sx={{
                  fontWeight: 'bold',
                  fontSize: '32px',
                  color: '#333'
                }}>
                  {rollTotal}
                </Typography>
              </Box>
              
              {/* Simple text */}
              <Box sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start'
              }}>
                <Typography sx={{
                  fontWeight: 'bold',
                  fontSize: '16px',
                  color: '#333',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {rollTotal === 7 || rollTotal === 11 ? 'Lucky!' : 'Move'}
                </Typography>
                
                <Typography sx={{
                  fontWeight: 'normal',
                  fontSize: '14px',
                  color: '#333'
                }}>
                  {rollTotal} spaces
                </Typography>
              </Box>
            </Box>
          )}
        </Box>
      )}
      
      {/* Animated Card */}
      {showCard && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            zIndex: 1000,
            perspective: '1000px'
          }}
        >
          <Box
            sx={{
              width: '300px',
              height: '200px',
              position: 'relative',
              transition: 'all 1.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
              transformStyle: 'preserve-3d',
              transform: cardAnimation === 'initial' 
                ? 'scale(0.1) translateY(100px)' 
                : cardAnimation === 'flipping' 
                  ? 'scale(1) rotateY(180deg)' 
                  : cardAnimation === 'showing'
                    ? 'scale(1) rotateY(180deg)'
                    : 'scale(0.8) rotateY(180deg) translateY(1000px)',
              opacity: cardAnimation === 'initial' ? 0.5 : 
                      cardAnimation === 'flying' ? 0 : 1
            }}
          >
            {/* Card Back */}
            <Box
              sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backfaceVisibility: 'hidden',
                backgroundColor: cardType === 'chance' ? '#FFC663' : '#CBDFF8',
                border: '2px solid #333',
                borderRadius: '10px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                boxShadow: '0 10px 20px rgba(0,0,0,0.4)',
                transform: 'rotateY(0deg)'
              }}
            >
              <Typography variant="h4">
                {cardType === 'chance' ? '?' : 'COMMUNITY CHEST'}
              </Typography>
            </Box>
            
            {/* Card Front */}
            <Box
              sx={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backfaceVisibility: 'hidden',
                backgroundColor: 'white',
                border: '2px solid #333',
                borderRadius: '10px',
                padding: '15px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: '0 10px 20px rgba(0,0,0,0.4)',
                transform: 'rotateY(180deg)'
              }}
            >
              <Box sx={{ 
                width: '100%', 
                backgroundColor: cardType === 'chance' ? '#FFC663' : '#CBDFF8',
                padding: '5px',
                borderRadius: '5px',
                textAlign: 'center'
              }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {cardType === 'chance' ? 'CHANCE' : 'COMMUNITY CHEST'}
                </Typography>
              </Box>
              
              <Box sx={{ textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
                  {cardContent?.title}
                </Typography>
                <Typography variant="body1">
                  {cardContent?.description}
                </Typography>
              </Box>
              
              {/* Auto-dismiss timer visual indicator */}
              <Box sx={{ 
                position: 'absolute',
                bottom: '10px',
                left: '15px',
                right: '15px',
                height: '3px',
                backgroundColor: '#eee',
                borderRadius: '3px',
                overflow: 'hidden'
              }}>
                <Box sx={{ 
                  height: '100%',
                  width: '100%',
                  backgroundColor: cardType === 'chance' ? '#FFC663' : '#CBDFF8',
                  animation: cardAnimation === 'showing' ? 'timer 6s linear forwards' : 'none',
                  '@keyframes timer': {
                    '0%': { width: '100%' },
                    '100%': { width: '0%' }
                  }
                }} />
              </Box>
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}

// Helper function to create alpha colors
function alpha(color, value) {
  // Simple alpha function for web colors
  return color + Math.round(value * 255).toString(16).padStart(2, '0');
}

// Helper function to darken a color
function darkenColor(color, percent) {
  // Convert hex to RGB
  let r = parseInt(color.substr(1, 2), 16);
  let g = parseInt(color.substr(3, 2), 16);
  let b = parseInt(color.substr(5, 2), 16);
  
  // Darken
  r = Math.floor(r * (100 - percent) / 100);
  g = Math.floor(g * (100 - percent) / 100);
  b = Math.floor(b * (100 - percent) / 100);
  
  // Convert back to hex
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

export default BoardPage; 