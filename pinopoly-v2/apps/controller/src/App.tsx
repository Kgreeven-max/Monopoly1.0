import { usePlayerStore } from './store/playerStore';
import { useSocket } from './hooks/useSocket';
import { AnimationProvider } from './contexts/AnimationContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ToastContainer } from './components/Toast';
import { JoinScreen } from './screens/JoinScreen';
import { LobbyScreen } from './screens/LobbyScreen';
import { GameScreen } from './screens/GameScreen';
import { ResultsScreen } from './screens/ResultsScreen';

function AppContent() {
  const { playerId, gameState } = usePlayerStore();
  const { isConnected } = useSocket();

  // Render appropriate screen based on state
  const renderScreen = () => {
    // Not joined yet
    if (!playerId) {
      return <JoinScreen />;
    }

    // Joined but waiting for game state
    if (!gameState) {
      return (
        <div className="flex flex-col items-center justify-center h-screen gap-4">
          <div className="spinner" />
          <p className="text-white/60">Joining game...</p>
        </div>
      );
    }

    // Render based on game status
    switch (gameState.status) {
      case 'lobby':
        return <LobbyScreen />;
      case 'playing':
      case 'paused':
        return <GameScreen />;
      case 'finished':
        return <ResultsScreen />;
      default:
        return <JoinScreen />;
    }
  };

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Connection status */}
      <div className="fixed top-2 right-2 z-50 flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-xs text-white/50">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {renderScreen()}
    </div>
  );
}

// Wrap with providers for animation and notification contexts
function App() {
  return (
    <NotificationProvider>
      <AnimationProvider>
        <AppContent />
        <ToastContainer />
      </AnimationProvider>
    </NotificationProvider>
  );
}

export default App;
