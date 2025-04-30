import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';
import './PropertyMortgageModal.css';

const PropertyMortgageModal = ({ 
  isOpen, 
  onClose, 
  property, 
  onMortgage, 
  onUnmortgage,
  playerMoney
}) => {
  const [fadeIn, setFadeIn] = useState(false);
  const [actionType, setActionType] = useState('mortgage'); // mortgage or unmortgage
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Determine action type based on property's mortgage status
    if (property?.is_mortgaged) {
      setActionType('unmortgage');
    } else {
      setActionType('mortgage');
    }
    
    // Trigger fade-in animation when the modal opens
    if (isOpen) {
      setFadeIn(true);
      setError('');
    } else {
      setFadeIn(false);
    }
  }, [isOpen, property]);

  if (!isOpen || !property) return null;

  // Calculate amounts
  const mortgageValue = property.mortgage_value || 0;
  const unmortgageValue = Math.round(mortgageValue * 1.1); // 10% interest on unmortgage
  const canAffordUnmortgage = playerMoney >= unmortgageValue;
  
  // Get mortgage color based on mortgage status
  const getMortgageColor = () => {
    if (actionType === 'mortgage') {
      return '#2196F3'; // Blue for mortgage
    } else {
      return canAffordUnmortgage ? '#4CAF50' : '#F44336'; // Green if affordable, red if not
    }
  };

  const handleAction = async () => {
    setLoading(true);
    setError('');

    try {
      if (actionType === 'mortgage') {
        await onMortgage(property.id);
      } else {
        if (!canAffordUnmortgage) {
          setError('Insufficient funds to unmortgage this property');
          setLoading(false);
          return;
        }
        await onUnmortgage(property.id);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'An error occurred during the transaction');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`property-mortgage-modal ${fadeIn ? 'fade-in' : ''}`}>
      <div className="modal-content">
        <span className="close-button" onClick={onClose}>&times;</span>
        
        <h2>{actionType === 'mortgage' ? 'Mortgage Property' : 'Unmortgage Property'}</h2>
        
        <div className="property-info" style={{ borderColor: getMortgageColor() }}>
          <h3>{property.name}</h3>
          <p className="color-group">{property.color_group}</p>
        </div>
        
        <div className="transaction-details">
          <div className="detail-row">
            <span className="label">Property Value:</span>
            <span className="value">{formatCurrency(property.price || 0)}</span>
          </div>
          
          {actionType === 'mortgage' ? (
            <div className="detail-row highlight">
              <span className="label">Mortgage Value:</span>
              <span className="value">{formatCurrency(mortgageValue)}</span>
            </div>
          ) : (
            <>
              <div className="detail-row">
                <span className="label">Mortgage Value:</span>
                <span className="value">{formatCurrency(mortgageValue)}</span>
              </div>
              <div className="detail-row">
                <span className="label">Interest (10%):</span>
                <span className="value">{formatCurrency(unmortgageValue - mortgageValue)}</span>
              </div>
              <div className="detail-row highlight">
                <span className="label">Total to Unmortgage:</span>
                <span className="value">{formatCurrency(unmortgageValue)}</span>
              </div>
            </>
          )}
          
          {actionType === 'unmortgage' && (
            <div className="detail-row">
              <span className="label">Your Cash:</span>
              <span className={`value ${canAffordUnmortgage ? 'sufficient' : 'insufficient'}`}>
                {formatCurrency(playerMoney || 0)}
              </span>
            </div>
          )}
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div className="mortgage-warning">
          {actionType === 'mortgage' ? (
            <p>
              Mortgaging this property will provide you with immediate cash, but you won't
              collect rent while it's mortgaged. To unmortgage later, you'll need to pay
              back the mortgage value plus 10% interest.
            </p>
          ) : (
            <p>
              Unmortgaging this property will allow you to collect rent again. 
              You'll need to pay the mortgage value plus 10% interest.
            </p>
          )}
        </div>
        
        <div className="modal-actions">
          <button 
            className="cancel-button" 
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button 
            className={`action-button ${actionType === 'unmortgage' && !canAffordUnmortgage ? 'disabled' : ''}`}
            onClick={handleAction}
            disabled={loading || (actionType === 'unmortgage' && !canAffordUnmortgage)}
          >
            {loading ? 'Processing...' : (actionType === 'mortgage' ? 'Mortgage' : 'Unmortgage')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PropertyMortgageModal; 