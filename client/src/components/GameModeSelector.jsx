import React, { useState, useEffect } from 'react';
import { GameModeService } from '../services';

/**
 * Game mode selection component for the admin interface
 */
const GameModeSelector = ({ gameId, onModeSelected }) => {
  const [loading, setLoading] = useState(true);
  const [modes, setModes] = useState({ standard: [], specialty: [] });
  const [selectedMode, setSelectedMode] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Fetch available game modes on component mount
  useEffect(() => {
    const fetchModes = async () => {
      try {
        setLoading(true);
        const response = await GameModeService.getAvailableModes();
        
        if (response.success) {
          setModes(response.modes);
        } else {
          setError('Failed to fetch game modes');
        }
      } catch (err) {
        setError(`Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchModes();
  }, []);

  // Handle mode selection
  const handleSelectMode = async (modeId) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const response = await GameModeService.selectGameMode(gameId, modeId);
      
      if (response.success) {
        setSelectedMode(modeId);
        setSuccess(`${response.mode} mode selected successfully`);
        
        // Notify parent component
        if (onModeSelected) {
          onModeSelected(response);
        }
      } else {
        setError(response.error || 'Failed to select game mode');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Render mode description
  const renderModeDescription = (mode) => {
    return (
      <div className="mode-description">
        <h3>{mode.name}</h3>
        <p>{mode.description}</p>
        <div className="mode-details">
          <div>
            <strong>Objective:</strong> {mode.objective}
          </div>
          <div>
            <strong>Win Condition:</strong> {mode.win_condition}
          </div>
          <div>
            <strong>Estimated Time:</strong> {mode.estimated_time}
          </div>
          <div>
            <strong>Difficulty:</strong> {mode.difficulty}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="game-mode-selector">
      <h2>Select Game Mode</h2>
      
      {loading && <div className="loading">Loading game modes...</div>}
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {success && (
        <div className="success-message">
          {success}
        </div>
      )}
      
      {!loading && (
        <div className="mode-categories">
          <div className="mode-category">
            <h3>Standard Modes</h3>
            <div className="mode-list">
              {modes.standard && modes.standard.map((mode) => (
                <div 
                  key={mode.id} 
                  className={`mode-item ${selectedMode === mode.id ? 'selected' : ''}`}
                  onClick={() => handleSelectMode(mode.id)}
                >
                  <div className="mode-header">
                    <h4>{mode.name}</h4>
                    <span className="difficulty-badge">{mode.difficulty}</span>
                  </div>
                  {renderModeDescription(mode)}
                  <button 
                    className="select-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectMode(mode.id);
                    }}
                    disabled={loading}
                  >
                    Select
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          <div className="mode-category">
            <h3>Specialty Modes</h3>
            <div className="mode-list">
              {modes.specialty && modes.specialty.map((mode) => (
                <div 
                  key={mode.id} 
                  className={`mode-item ${selectedMode === mode.id ? 'selected' : ''}`}
                  onClick={() => handleSelectMode(mode.id)}
                >
                  <div className="mode-header">
                    <h4>{mode.name}</h4>
                    <span className="difficulty-badge">{mode.difficulty}</span>
                  </div>
                  {renderModeDescription(mode)}
                  <button 
                    className="select-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectMode(mode.id);
                    }}
                    disabled={loading}
                  >
                    Select
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameModeSelector; 