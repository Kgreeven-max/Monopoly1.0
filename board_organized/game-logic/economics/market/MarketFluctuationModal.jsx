import React, { useState, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';
import './MarketFluctuationModal.css';

const MarketFluctuationModal = ({ 
  isOpen, 
  onClose, 
  economicState, 
  effects, 
  playerName 
}) => {
  const [fadeIn, setFadeIn] = useState(false);

  useEffect(() => {
    // Trigger fade-in animation when the modal opens
    if (isOpen) {
      setFadeIn(true);
    } else {
      setFadeIn(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Get the corresponding color based on economic state
  const getStateColor = (state) => {
    const colorMap = {
      boom: '#4CAF50',     // Green
      stable: '#2196F3',   // Blue
      recession: '#FF9800', // Orange
      depression: '#F44336' // Red
    };
    return colorMap[state] || '#2196F3';
  };

  // Get the icon based on whether cash/property values increased or decreased
  const getDirectionIcon = (type) => {
    if (type === 'bonus' || type === 'increase') {
      return '↑';
    } else if (type === 'penalty' || type === 'decrease') {
      return '↓';
    }
    return '';
  };

  // Process effects data
  const economicStateColor = getStateColor(economicState);
  const hasCashEffect = effects?.cash_effect;
  const hasPropertyEffect = effects?.property_changes && effects.property_changes.length > 0;

  return (
    <div className={`market-fluctuation-modal ${fadeIn ? 'fade-in' : ''}`}>
      <div className="modal-content">
        <span className="close-button" onClick={onClose}>&times;</span>
        
        <h2>Market Fluctuation</h2>
        
        <div className="economic-state" style={{ borderColor: economicStateColor }}>
          <h3>Economic State: <span style={{ color: economicStateColor }}>{economicState}</span></h3>
          <p>{effects?.description || "The economy has affected your investments."}</p>
        </div>
        
        {hasCashEffect && (
          <div className="cash-effect">
            <h3>Cash Impact</h3>
            <div className={`effect-value ${effects.cash_effect}`}>
              <span className="direction-icon">{getDirectionIcon(effects.cash_effect)}</span>
              <span className="amount">{formatCurrency(effects.cash_change || 0)}</span>
            </div>
          </div>
        )}
        
        {hasPropertyEffect && (
          <div className="property-effect">
            <h3>Property Values</h3>
            <p>Total change: 
              <span className={effects.property_effect}>
                {getDirectionIcon(effects.property_effect)} {formatCurrency(effects.total_property_value_change || 0)}
              </span>
            </p>
            
            <div className="property-list">
              {effects.property_changes.map((prop, index) => (
                <div key={index} className="property-item">
                  <span className="property-name">{prop.property_name}</span>
                  <span className="old-value">{formatCurrency(prop.old_value)}</span>
                  <span className="arrow">→</span>
                  <span className="new-value">{formatCurrency(prop.new_value)}</span>
                  <span className={`change-value ${prop.change >= 0 ? 'increase' : 'decrease'}`}>
                    {prop.change >= 0 ? '+' : ''}{formatCurrency(prop.change)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="modal-actions">
          <button className="action-button" onClick={onClose}>Continue</button>
        </div>
      </div>
    </div>
  );
};

export default MarketFluctuationModal; 