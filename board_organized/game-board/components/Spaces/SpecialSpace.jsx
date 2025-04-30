import React from 'react';
import { useGame } from '../../contexts/GameContext';
import './SpecialSpace.css';

const SPECIAL_SPACE_ICONS = {
  go: '⭐',
  jail: '🔒',
  parking: '🅿️',
  goToJail: '👮',
  chance: '❓',
  communityChest: '📦',
  tax: '💰',
};

export default function SpecialSpace({ space, position }) {
  const { state } = useGame();
  const { economicState } = state;

  // Calculate tax amount based on economic state
  const calculateTaxAmount = () => {
    if (space.type !== 'tax') return null;
    
    const baseAmount = space.baseAmount;
    switch (economicState) {
      case 'recession':
        return Math.floor(baseAmount * 0.8);
      case 'growth':
        return Math.floor(baseAmount * 1.2);
      case 'boom':
        return Math.floor(baseAmount * 1.5);
      default:
        return baseAmount;
    }
  };

  // Get special space content
  const getSpaceContent = () => {
    switch (space.type) {
      case 'tax':
        return (
          <>
            <div className="special-space-icon">{SPECIAL_SPACE_ICONS[space.type]}</div>
            <h3>{space.name}</h3>
            <p className="tax-amount">
              Pay ${calculateTaxAmount()}
            </p>
          </>
        );
      
      case 'chance':
      case 'communityChest':
        return (
          <>
            <div className="special-space-icon">{SPECIAL_SPACE_ICONS[space.type]}</div>
            <h3>{space.name}</h3>
            <p className="card-count">
              {state[`${space.type}Cards`]?.length || 0} cards
            </p>
          </>
        );
      
      case 'parking':
        return (
          <>
            <div className="special-space-icon">{SPECIAL_SPACE_ICONS[space.type]}</div>
            <h3>Free Parking</h3>
            <p className="fund-amount">
              Fund: ${state.communityFund}
            </p>
          </>
        );
      
      default:
        return (
          <>
            <div className="special-space-icon">{SPECIAL_SPACE_ICONS[space.type]}</div>
            <h3>{space.name}</h3>
          </>
        );
    }
  };

  return (
    <div
      className={`special-space ${space.type}`}
      style={{
        transform: `translate(${position.x}px, ${position.y}px)`,
      }}
      data-economic-state={economicState}
    >
      {getSpaceContent()}
    </div>
  );
} 