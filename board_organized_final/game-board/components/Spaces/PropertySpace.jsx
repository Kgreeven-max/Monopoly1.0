import React from 'react';
import { useGame } from '../../contexts/GameContext';
import './PropertySpace.css';

export default function PropertySpace({ property, position }) {
  const { state } = useGame();
  const { economicState } = state;

  // Calculate property value based on economic state
  const calculateValue = () => {
    const baseValue = property.baseValue;
    switch (economicState) {
      case 'recession':
        return baseValue * 0.8;
      case 'growth':
        return baseValue * 1.3;
      case 'boom':
        return baseValue * 1.6;
      default:
        return baseValue;
    }
  };

  // Get owner information
  const owner = state.players.find(p => p.id === property.ownerId);
  
  // Get development level
  const developmentLevel = property.developmentLevel || 0;

  // Calculate rent based on development and economic state
  const calculateRent = () => {
    const baseRent = property.baseRent;
    const developmentMultiplier = 1 + (developmentLevel * 0.5);
    const economicMultiplier = economicState === 'recession' ? 0.8 :
                              economicState === 'growth' ? 1.3 :
                              economicState === 'boom' ? 1.6 : 1;
    
    return baseRent * developmentMultiplier * economicMultiplier;
  };

  return (
    <div
      className={`property-space ${property.group}`}
      style={{
        transform: `translate(${position.x}px, ${position.y}px)`,
        '--group-color': `var(--${property.group}-color, var(--primary-color))`
      }}
      data-development-level={developmentLevel}
    >
      <div className="property-header">
        <div className="property-color-bar" />
        <h3>{property.name}</h3>
      </div>

      <div className="property-details">
        <p className="property-value">${calculateValue()}</p>
        <p className="property-rent">Rent: ${calculateRent()}</p>
        
        {owner && (
          <div className="property-owner">
            <div
              className="owner-token"
              style={{ backgroundColor: owner.color }}
            />
            <span>{owner.name}</span>
          </div>
        )}

        {developmentLevel > 0 && (
          <div className="development-indicators">
            {[...Array(developmentLevel)].map((_, i) => (
              <div key={i} className="development-indicator" />
            ))}
          </div>
        )}

        {property.mortgaged && (
          <div className="mortgaged-indicator">
            MORTGAGED
          </div>
        )}
      </div>
    </div>
  );
} 