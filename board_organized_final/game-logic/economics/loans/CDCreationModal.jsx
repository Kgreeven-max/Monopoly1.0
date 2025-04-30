import React, { useState } from 'react';
import { finance } from '../services/api';
import { useNotifications } from '../contexts/NotificationContext';
import { useGame } from '../contexts/GameContext';
import './CDCreationModal.css';

const CDCreationModal = ({ onClose }) => {
  const { state } = useGame();
  const { addNotification } = useNotifications();
  const [amount, setAmount] = useState(500);
  const [term, setTerm] = useState(3);
  const [loading, setLoading] = useState(false);
  
  // Get the player data from game state
  const playerData = state.players.find(p => p.id === state.currentPlayer?.id);
  
  const calculateInterestRate = (term) => {
    // Base rates for different terms
    const baseRates = {
      3: 0.05, // 5% for 3 lap term
      5: 0.08, // 8% for 5 lap term
      7: 0.12  // 12% for 7 lap term
    };
    
    // Economic state modifiers
    const economicModifiers = {
      'recession': -0.01,
      'normal': 0,
      'growth': 0.01,
      'boom': 0.02
    };
    
    const baseRate = baseRates[term] || baseRates[3];
    const modifier = economicModifiers[state.economicState] || 0;
    
    return baseRate + modifier;
  };
  
  const interestRate = calculateInterestRate(term);
  const estimatedReturn = Math.round(amount * (1 + interestRate * term));
  
  const handleAmountChange = (e) => {
    const value = Math.min(
      Math.max(100, parseInt(e.target.value) || 0),
      playerData?.cash || 1000
    );
    setAmount(value);
  };
  
  const handleTermChange = (newTerm) => {
    setTerm(newTerm);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (loading) return;
    
    try {
      setLoading(true);
      
      const response = await finance.createCD(amount, term);
      
      addNotification({
        type: 'success',
        title: 'CD Created',
        message: `Successfully invested $${amount} for ${term} laps at ${(interestRate * 100).toFixed(1)}% interest.`,
        duration: 5000
      });
      
      setLoading(false);
      onClose();
    } catch (error) {
      setLoading(false);
      addNotification({
        type: 'error',
        title: 'Error Creating CD',
        message: error.message || 'Failed to create CD. Please try again.',
        duration: 5000
      });
    }
  };
  
  return (
    <div className="modal-backdrop">
      <div className="cd-modal">
        <div className="cd-modal-header">
          <h2>Create Certificate of Deposit (CD)</h2>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        
        <div className="cd-modal-content">
          <div className="cd-info">
            <p>A Certificate of Deposit (CD) allows you to earn interest on your money over time.</p>
            <p>Funds will be locked for the selected term duration.</p>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Investment Amount</label>
              <div className="amount-input">
                <span className="currency-symbol">$</span>
                <input
                  type="number"
                  value={amount}
                  onChange={handleAmountChange}
                  min={100}
                  max={playerData?.cash || 1000}
                  required
                />
              </div>
              <div className="amount-slider">
                <input
                  type="range"
                  min={100}
                  max={playerData?.cash || 1000}
                  value={amount}
                  onChange={handleAmountChange}
                  step={100}
                />
              </div>
              <div className="cash-available">
                Cash available: ${playerData?.cash || 0}
              </div>
            </div>
            
            <div className="form-group">
              <label>Term Length</label>
              <div className="term-options">
                <button
                  type="button"
                  className={`term-option ${term === 3 ? 'selected' : ''}`}
                  onClick={() => handleTermChange(3)}
                >
                  3 Laps
                </button>
                <button
                  type="button"
                  className={`term-option ${term === 5 ? 'selected' : ''}`}
                  onClick={() => handleTermChange(5)}
                >
                  5 Laps
                </button>
                <button
                  type="button"
                  className={`term-option ${term === 7 ? 'selected' : ''}`}
                  onClick={() => handleTermChange(7)}
                >
                  7 Laps
                </button>
              </div>
            </div>
            
            <div className="investment-summary">
              <div className="summary-item">
                <span>Interest Rate:</span>
                <span className="value">{(interestRate * 100).toFixed(1)}%</span>
              </div>
              <div className="summary-item">
                <span>Term Duration:</span>
                <span className="value">{term} Laps</span>
              </div>
              <div className="summary-item">
                <span>Amount Invested:</span>
                <span className="value">${amount}</span>
              </div>
              <div className="summary-item total">
                <span>Estimated Return:</span>
                <span className="value">${estimatedReturn}</span>
              </div>
            </div>
            
            <div className="modal-actions">
              <button type="button" className="cancel-button" onClick={onClose}>
                Cancel
              </button>
              <button
                type="submit"
                className="create-button"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create CD'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CDCreationModal; 