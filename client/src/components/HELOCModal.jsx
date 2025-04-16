import React, { useState, useEffect } from 'react';
import { finance } from '../services/api';
import { useNotifications } from '../contexts/NotificationContext';
import { useGame } from '../contexts/GameContext';
import './HELOCModal.css';

const HELOCModal = ({ onClose }) => {
  const { state } = useGame();
  const { addNotification } = useNotifications();
  const [amount, setAmount] = useState(500);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingProperties, setFetchingProperties] = useState(true);
  
  // Get the player data from game state
  const playerData = state.players.find(p => p.id === state.currentPlayer?.id);
  
  // Fetch player's properties
  useEffect(() => {
    const fetchProperties = async () => {
      try {
        setFetchingProperties(true);
        // Fetch properties owned by the player
        const response = await fetch(`/api/player/${playerData.id}/properties?pin=${playerData.pin}`);
        const data = await response.json();
        
        if (data.success) {
          // Filter out mortgaged properties
          const availableProperties = data.properties.filter(prop => !prop.is_mortgaged);
          setProperties(availableProperties);
          
          // Select the first property by default if any available
          if (availableProperties.length > 0) {
            setSelectedProperty(availableProperties[0]);
            
            // Set default amount to 60% of property value up to player cash
            const defaultAmount = Math.min(
              Math.round(availableProperties[0].current_price * 0.6),
              playerData?.cash || 0
            );
            setAmount(defaultAmount);
          }
        }
      } catch (error) {
        addNotification({
          type: 'error',
          title: 'Error',
          message: 'Failed to fetch properties',
          duration: 5000
        });
      } finally {
        setFetchingProperties(false);
      }
    };
    
    if (playerData) {
      fetchProperties();
    }
  }, [playerData, addNotification]);
  
  const calculateMaxHeloc = (property) => {
    if (!property) return 0;
    
    // Base HELOC is 60% of property value
    let maxHeloc = Math.round(property.current_price * 0.6);
    
    // Add bonus for developed properties (5% per level)
    if (property.development_level) {
      const developmentBonus = property.development_level * 0.05;
      maxHeloc = Math.round(maxHeloc * (1 + developmentBonus));
    }
    
    return maxHeloc;
  };
  
  const calculateInterestRate = () => {
    // Get base rate for HELOC - typically lower than standard loans
    const baseRate = 0.08; // 8% base rate
    
    // Economic state modifiers
    const economicModifiers = {
      'recession': -0.015,  // -1.5% in recession
      'normal': 0,
      'growth': 0.015,     // +1.5% in growth
      'boom': 0.04         // +4% in boom
    };
    
    const modifier = economicModifiers[state.economicState] || 0;
    
    return baseRate + modifier;
  };
  
  const interestRate = calculateInterestRate();
  const maxAmount = selectedProperty ? calculateMaxHeloc(selectedProperty) : 0;
  
  const handleAmountChange = (e) => {
    const value = Math.min(
      Math.max(100, parseInt(e.target.value) || 0),
      maxAmount
    );
    setAmount(value);
  };
  
  const handlePropertyChange = (property) => {
    setSelectedProperty(property);
    
    // Update amount to default 60% of new property value (capped at max HELOC)
    const newMaxAmount = calculateMaxHeloc(property);
    const newAmount = Math.min(amount, newMaxAmount);
    setAmount(newAmount);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (loading || !selectedProperty) return;
    
    try {
      setLoading(true);
      
      const response = await finance.getHELOC(selectedProperty.id, amount);
      
      addNotification({
        type: 'success',
        title: 'HELOC Created',
        message: `Successfully borrowed $${amount} against ${selectedProperty.name}.`,
        duration: 5000
      });
      
      setLoading(false);
      onClose();
    } catch (error) {
      setLoading(false);
      addNotification({
        type: 'error',
        title: 'Error Creating HELOC',
        message: error.message || 'Failed to create HELOC. Please try again.',
        duration: 5000
      });
    }
  };
  
  if (fetchingProperties) {
    return (
      <div className="modal-backdrop">
        <div className="heloc-modal">
          <div className="heloc-modal-header">
            <h2>Loading Properties...</h2>
            <button className="close-button" onClick={onClose}>&times;</button>
          </div>
          <div className="heloc-modal-content loading">
            <div className="spinner"></div>
            <p>Fetching your properties...</p>
          </div>
        </div>
      </div>
    );
  }
  
  if (properties.length === 0) {
    return (
      <div className="modal-backdrop">
        <div className="heloc-modal">
          <div className="heloc-modal-header">
            <h2>No Eligible Properties</h2>
            <button className="close-button" onClick={onClose}>&times;</button>
          </div>
          <div className="heloc-modal-content">
            <p>You don't have any properties eligible for a HELOC.</p>
            <p>You need to own unmortgaged properties to take out a HELOC.</p>
            <div className="modal-actions">
              <button className="cancel-button" onClick={onClose}>Close</button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="modal-backdrop">
      <div className="heloc-modal">
        <div className="heloc-modal-header">
          <h2>Home Equity Line of Credit (HELOC)</h2>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        
        <div className="heloc-modal-content">
          <div className="heloc-info">
            <p>A HELOC allows you to borrow against the value of your properties at a lower interest rate than standard loans.</p>
            <p>You can borrow up to 60% of the property's value, with developed properties offering higher limits.</p>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Select Property</label>
              <div className="property-selector">
                {properties.map(property => (
                  <div 
                    key={property.id}
                    className={`property-option ${selectedProperty?.id === property.id ? 'selected' : ''}`}
                    onClick={() => handlePropertyChange(property)}
                  >
                    <div className="property-name">{property.name}</div>
                    <div className="property-value">Value: ${property.current_price}</div>
                    <div className="property-group" style={{ backgroundColor: property.color }}></div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="form-group">
              <label>Loan Amount</label>
              <div className="amount-input">
                <span className="currency-symbol">$</span>
                <input
                  type="number"
                  value={amount}
                  onChange={handleAmountChange}
                  min={100}
                  max={maxAmount}
                  required
                />
              </div>
              <div className="amount-slider">
                <input
                  type="range"
                  min={100}
                  max={maxAmount}
                  value={amount}
                  onChange={handleAmountChange}
                  step={100}
                />
              </div>
              <div className="max-amount">
                Maximum HELOC: ${maxAmount}
              </div>
            </div>
            
            <div className="loan-summary">
              <div className="summary-item">
                <span>Interest Rate:</span>
                <span className="value">{(interestRate * 100).toFixed(1)}%</span>
              </div>
              <div className="summary-item">
                <span>Property:</span>
                <span className="value">{selectedProperty?.name}</span>
              </div>
              <div className="summary-item">
                <span>Property Value:</span>
                <span className="value">${selectedProperty?.current_price}</span>
              </div>
              <div className="summary-item">
                <span>Loan-to-Value Ratio:</span>
                <span className="value">
                  {selectedProperty ? ((amount / selectedProperty.current_price) * 100).toFixed(1) : 0}%
                </span>
              </div>
              <div className="summary-item total">
                <span>Amount to Borrow:</span>
                <span className="value">${amount}</span>
              </div>
            </div>
            
            <div className="modal-actions">
              <button type="button" className="cancel-button" onClick={onClose}>
                Cancel
              </button>
              <button
                type="submit"
                className="create-button"
                disabled={loading || !selectedProperty}
              >
                {loading ? 'Processing...' : 'Create HELOC'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default HELOCModal; 