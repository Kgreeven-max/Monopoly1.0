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
import DebugPage from './pages/DebugPage';

// Define a modern theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2E7D32', // Green - monopoly color
    },
    secondary: {
      main: '#C62828', // Red - monopoly color
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    }
  },
  typography: {
    fontFamily: '"Poppins", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 600,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 500,
    },
    button: {
      fontWeight: 500,
    }
  },
  shape: {
    borderRadius: 8
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          padding: '8px 16px',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 10px rgba(0, 0, 0, 0.08)',
        },
      },
    },
  },
});

// Protected route component
const ProtectedRoute = ({ children, roleRequired }) => {
  const { isAuthenticated, role, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  if (roleRequired && role !== roleRequired) {
    return <Navigate to="/" replace />;
  }

  return children;
};

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
                  {/* Public Routes */}
                  <Route path="/" element={<HomePage />} />
                  <Route path="/connect" element={<ConnectPage />} />
                  <Route path="/board" element={<BoardPage />} />
                  <Route path="/debug" element={<DebugPage />} />

                  {/* Protected routes */}
                  <Route
                    path="/player/:playerId"
                    element={
                      <ProtectedRoute roleRequired="player">
                        <PlayerPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/remote"
                    element={
                      <ProtectedRoute roleRequired="player">
                        <RemotePlayerPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin"
                    element={
                      <ProtectedRoute roleRequired="admin">
                        <AdminDashboard />
                      </ProtectedRoute>
                    }
                  />

                  {/* 404 route */}
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