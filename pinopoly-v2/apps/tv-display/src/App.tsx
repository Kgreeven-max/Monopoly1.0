import { useEffect, useCallback } from 'react';
import { useGameStore } from './store/gameStore';
import { useSocket } from './hooks/useSocket';
import { LobbyScreen } from './screens/LobbyScreen';
import { GameScreen } from './screens/GameScreen';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { ResultsScreen } from './screens/ResultsScreen';

function App() {
  const { gameState, roomCode } = useGameStore();
  const { connect, isConnected } = useSocket();

  // Handle connection from WelcomeScreen or URL
  const handleConnect = useCallback((code: string) => {
    connect(code);
  }, [connect]);

  useEffect(() => {
    // Extract room code from URL if present
    const params = new URLSearchParams(window.location.search);
    const code = params.get('room');

    if (code) {
      handleConnect(code);
    }
  }, [handleConnect]);

  // Render appropriate screen based on game state
  const renderScreen = () => {
    if (!roomCode) {
      return <WelcomeScreen onConnect={handleConnect} />;
    }

    if (!gameState) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-white text-2xl animate-pulse">
            Connecting to game...
          </div>
        </div>
      );
    }

    switch (gameState.status) {
      case 'lobby':
        return <LobbyScreen />;
      case 'playing':
      case 'paused':
        return <GameScreen />;
      case 'finished':
        return <ResultsScreen />;
      default:
        return <WelcomeScreen />;
    }
  };

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Connection indicator */}
      <div className="fixed top-4 right-4 z-50">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
      </div>

      {renderScreen()}
    </div>
  );
}

export default App;
