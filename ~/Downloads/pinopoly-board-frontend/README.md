# Pi-nopoly Board Frontend

This is a collection of the key files used for the Pi-nopoly game board frontend interface.

## Technology Stack
- **React.js** - UI library/framework
- **Material-UI (MUI)** - React component library
- **Vite** - Build tool
- **CSS** - Styling

## Main Files
- **BoardPage.jsx** - The main board component that displays the game board
- **BoardPage.css** - Styles specific to the board
- **index.css** - Global styles
- **NavBar.jsx** - Navigation bar with the fullscreen button
- **PlayerList.jsx** - Component that displays the list of players
- **GameLog.jsx** - Component that displays the game activity log
- **CardDisplay.jsx** - Component that displays cards and events

## Context Providers
- **GameContext.jsx** - Provides game state to components
- **SocketContext.jsx** - Provides socket.io connection for real-time updates

## Setup Instructions
1. Install dependencies: `npm install`
2. Run the development server: `npm run dev`
3. Open http://localhost:3000 in your browser

## Note
This is just the frontend part of the Pi-nopoly game. For the complete application, the backend (written in Python with Flask) is also required. 