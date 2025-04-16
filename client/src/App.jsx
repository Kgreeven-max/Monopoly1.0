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

// Define a basic theme (optional, customize as needed)
const theme = createTheme({
  palette: {
    mode: 'light', // or 'dark'
    primary: {
      main: '#1976d2', // Blue
    },
    secondary: {
      main: '#dc004e', // Pink
    },
  },
});

// Protected route component
const ProtectedRoute = ({ children, roleRequired }) => {
  const { isAuthenticated, role, loading, user } = useAuth();
  const location = useLocation();

  console.log(`[ProtectedRoute] Checking access:`, { isAuthenticated, loading, role });

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><CircularProgress /></Box>;
  }

  if (!isAuthenticated) {
    console.log(`[ProtectedRoute] Access DENIED (Not Authenticated). Redirecting to /`);
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  if (roleRequired && role !== roleRequired) {
    console.log(`[ProtectedRoute] Access DENIED (Role Mismatch: required ${roleRequired}, user has ${role}). Redirecting to /`);
    return <Navigate to="/" replace />;
  }

  console.log(`[ProtectedRoute] Access GRANTED.`);
  return children;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* Provides basic CSS reset and background */}
      <Router> {/* Router should wrap providers */}
        <SocketProvider>
          <AuthProvider>
            <GameProvider>
              <NotificationProvider>
                {/* Routes component now directly inside NotificationProvider */}
                <Routes>
                  {/* Public Route */}
                  <Route path="/" element={<HomePage />} />
                  <Route path="/connect" element={<ConnectPage />} />

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
                  <Route
                    path="/board"
                    element={
                      <ProtectedRoute roleRequired="display">
                        <BoardPage />
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