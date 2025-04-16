import React, { useState, useEffect } from 'react';
import GameModeSelector from './GameModeSelector';
import GameModeSettings from './GameModeSettings';
import { GameModeService } from '../services';

/**
 * Game mode administration component that combines selection and settings
 */
const GameModeAdmin = ({ gameId }) => {
  const [selectedMode, setSelectedMode] = useState(null);
  const [activeTab, setActiveTab] = useState('select');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Check if a game mode is already set
  useEffect(() => {
    const checkExistingMode = async () => {
      if (!gameId) return;
      
      try {
        setLoading(true);
        const response = await GameModeService.getGameModeSettings(gameId);
        
        if (response.success) {
          setSelectedMode(response.mode);
          // If a mode is already selected, default to settings tab
          setActiveTab('settings');
        }
      } catch (err) {
        setError(`Error checking game mode: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    checkExistingMode();
  }, [gameId]);
  
  // Handle mode selection
  const handleModeSelected = (response) => {
    setSelectedMode(response.mode);
    setActiveTab('settings');
  };
  
  return (
    <div className="game-mode-admin">
      <h2>Game Mode Management</h2>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'select' ? 'active' : ''}`}
          onClick={() => setActiveTab('select')}
        >
          Select Mode
        </button>
        
        <button 
          className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
          disabled={!selectedMode}
        >
          Configure Settings
        </button>
      </div>
      
      <div className="tab-content">
        {activeTab === 'select' && (
          <GameModeSelector 
            gameId={gameId}
            onModeSelected={handleModeSelected}
          />
        )}
        
        {activeTab === 'settings' && selectedMode && (
          <GameModeSettings 
            gameId={gameId}
            mode={selectedMode}
          />
        )}
      </div>
    </div>
  );
};

export default GameModeAdmin; 