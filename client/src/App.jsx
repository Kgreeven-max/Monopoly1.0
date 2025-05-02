import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation
} from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SocketProvider } from './contexts/SocketContext';
import { GameProvider } from './contexts/GameContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { Box, CircularProgress } from '@mui/material';

// Import Page Components
import HomePage from './pages/HomePage';
import BoardPage from './pages/BoardPage';
import PlayerPage from './pages/PlayerPage';
import AdminDashboard from './AdminDashboard';
import RemotePlayerPage from './pages/RemotePlayerPage';
import ConnectPage from './pages/ConnectPage';
import NotFoundPage from './pages/NotFoundPage';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Green
      light: '#4CAF50',
      dark: '#1B5E20',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#1565C0', // Blue
      light: '#1E88E5',
      dark: '#0D47A1',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#D32F2F',
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF',
    },
  },
  typography: {
    fontFamily: "'Poppins', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 10,
          fontWeight: 500,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 6px 20px rgba(0,0,0,0.05)',
        },
      },
    },
    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: 20,
        },
      },
    },
  },
});

// Auth-protected route
function PrivateRoute({ children }) {
  const { currentUser, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return currentUser ? children : <Navigate to="/" state={{ from: location }} />;
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <SocketProvider>
          <AuthProvider>
            <GameProvider>
              <NotificationProvider>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/connect" element={<ConnectPage />} />
                  <Route path="/board" element={<BoardPage />} />
                  <Route path="/player/:playerId" element={<PlayerPage />} />
                  <Route path="/remote/:playerId" element={<RemotePlayerPage />} />
                  <Route path="/admin" element={<PrivateRoute><AdminDashboard /></PrivateRoute>} />
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </NotificationProvider>
            </GameProvider>
          </AuthProvider>
        </SocketProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App; 