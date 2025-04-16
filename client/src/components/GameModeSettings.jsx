import React, { useState, useEffect } from 'react';
import { GameModeService } from '../services';

/**
 * Component for configuring game mode settings
 */
const GameModeSettings = ({ gameId, mode }) => {
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState({});
  const [configOptions, setConfigOptions] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [formValues, setFormValues] = useState({});

  // Fetch current game mode settings on component mount or mode change
  useEffect(() => {
    const fetchSettings = async () => {
      if (!gameId) return;
      
      try {
        setLoading(true);
        const response = await GameModeService.getGameModeSettings(gameId);
        
        if (response.success) {
          setSettings(response.settings);
          
          // Get config options for this mode type
          const options = GameModeService.getModeConfigOptions(response.mode);
          setConfigOptions(options.settings || []);
          
          // Initialize form values
          const initialValues = {};
          options.settings.forEach(option => {
            // Navigate nested settings if needed (e.g., custom_settings.some_value)
            if (option.id.includes('.')) {
              const [parent, child] = option.id.split('.');
              if (response.settings.custom_settings && response.settings.custom_settings[child] !== undefined) {
                initialValues[option.id] = response.settings.custom_settings[child];
              } else {
                initialValues[option.id] = option.default;
              }
            } else if (response.settings[option.id] !== undefined) {
              initialValues[option.id] = response.settings[option.id];
            } else {
              initialValues[option.id] = option.default;
            }
          });
          
          setFormValues(initialValues);
        } else {
          setError(response.error || 'Failed to fetch game mode settings');
        }
      } catch (err) {
        setError(`Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, [gameId, mode]);

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // Convert values to appropriate types
    let processedValue;
    if (type === 'checkbox') {
      processedValue = checked;
    } else if (type === 'number') {
      processedValue = parseFloat(value);
    } else {
      processedValue = value;
    }
    
    setFormValues(prev => ({
      ...prev,
      [name]: processedValue
    }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      // Prepare settings update
      const updatedSettings = {};
      Object.entries(formValues).forEach(([key, value]) => {
        // Handle nested settings (e.g., custom_settings.some_value)
        if (key.includes('.')) {
          const [parent, child] = key.split('.');
          if (!updatedSettings[parent]) {
            updatedSettings[parent] = {};
          }
          updatedSettings[parent][child] = value;
        } else {
          updatedSettings[key] = value;
        }
      });
      
      const response = await GameModeService.updateGameModeSettings(gameId, updatedSettings);
      
      if (response.success) {
        setSettings(response.settings);
        setSuccess('Game mode settings updated successfully');
      } else {
        setError(response.error || 'Failed to update game mode settings');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Render setting input based on type
  const renderSettingInput = (setting) => {
    const { id, label, type, default: defaultValue } = setting;
    const value = formValues[id] ?? defaultValue;
    
    switch (type) {
      case 'boolean':
        return (
          <div className="form-check" key={id}>
            <input
              type="checkbox"
              id={id}
              name={id}
              className="form-check-input"
              checked={value}
              onChange={handleInputChange}
            />
            <label htmlFor={id} className="form-check-label">{label}</label>
          </div>
        );
        
      case 'number':
        return (
          <div className="form-group" key={id}>
            <label htmlFor={id}>{label}</label>
            <input
              type="number"
              id={id}
              name={id}
              className="form-control"
              value={value}
              onChange={handleInputChange}
            />
          </div>
        );
        
      case 'text':
      default:
        return (
          <div className="form-group" key={id}>
            <label htmlFor={id}>{label}</label>
            <input
              type="text"
              id={id}
              name={id}
              className="form-control"
              value={value}
              onChange={handleInputChange}
            />
          </div>
        );
    }
  };

  return (
    <div className="game-mode-settings">
      <h2>Game Mode Settings</h2>
      
      {loading && <div className="loading">Loading settings...</div>}
      
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
      
      {!loading && settings.mode_type && (
        <div className="settings-container">
          <div className="mode-info">
            <h3>{settings.name}</h3>
            <p>Mode: {settings.mode_type}</p>
            <p>Win Condition: {settings.win_condition}</p>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="settings-form">
              {configOptions.map(setting => renderSettingInput(setting))}
            </div>
            
            <div className="form-actions">
              <button
                type="submit"
                className="submit-button"
                disabled={loading}
              >
                {loading ? 'Saving...' : 'Save Settings'}
              </button>
              
              <button
                type="button"
                className="reset-button"
                onClick={() => window.location.reload()}
                disabled={loading}
              >
                Reset
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default GameModeSettings; 