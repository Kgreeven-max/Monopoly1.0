import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Enhanced contexts with animation support
import { AnimationProvider } from '../game-state/contexts/AnimationContext';
import { AnimatedGameProvider } from '../game-state/contexts/GameContext/AnimatedGameContext';

// Original contexts (still needed)
import { SocketProvider } from '../game-state/contexts/SocketContext';
import { AuthProvider } from '../game-state/contexts/AuthContext';
import { NotificationProvider } from '../game-state/contexts/NotificationContext';

// Pages
import HomePage from '../pages/HomePage';
import ConnectPage from '../pages/ConnectPage';
import PlayerPage from '../pages/PlayerPage';
import AdminPage from '../pages/AdminPage';
import NotFoundPage from '../pages/NotFoundPage';
import DebugPage from '../pages/DebugPage';
import RemotePlayerPage from '../pages/RemotePlayerPage';

// New animated board page
import AnimatedBoardPage from '../pages/BoardPage/AnimatedBoardPage';

function AppWithAnimations() {
  return (
    <Router>
      <AuthProvider>
        <SocketProvider>
          <NotificationProvider>
            {/* Wrap with animation contexts */}
            <AnimationProvider>
              <AnimatedGameProvider>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/connect" element={<ConnectPage />} />
                  <Route path="/player" element={<PlayerPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                  <Route path="/debug" element={<DebugPage />} />
                  <Route path="/remote" element={<RemotePlayerPage />} />
                  
                  {/* Enhanced board with animations */}
                  <Route path="/board" element={<AnimatedBoardPage />} />
                  
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </AnimatedGameProvider>
            </AnimationProvider>
          </NotificationProvider>
        </SocketProvider>
      </AuthProvider>
    </Router>
  );
}

export default AppWithAnimations;