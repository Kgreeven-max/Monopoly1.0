import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './PropertyDevelopmentModal.css';

const PropertyDevelopmentModal = ({ 
  property, 
  onClose, 
  onDevelop,
  onRequestApproval,
  onRequestStudy,
  gameState 
}) => {
  const [selectedLevel, setSelectedLevel] = useState(property.improvement_level);
  const [developmentCosts, setDevelopmentCosts] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch development requirements and costs when modal opens or selected level changes
  useEffect(() => {
    const fetchDevelopmentInfo = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/board/property-development/requirements?` +
          `property_id=${property.id}&target_level=${selectedLevel}`
        );
        const data = await response.json();
        
        if (data.success) {
          setDevelopmentCosts(data.development_costs);
        } else {
          setError(data.error || 'Failed to fetch development information');
        }
      } catch (err) {
        setError('Failed to fetch development information');
      } finally {
        setLoading(false);
      }
    };

    if (selectedLevel > property.improvement_level) {
      fetchDevelopmentInfo();
    }
  }, [property.id, selectedLevel, property.improvement_level]);

  const handleDevelop = async () => {
    if (selectedLevel <= property.improvement_level) {
      setError('Please select a higher development level');
      return;
    }

    try {
      await onDevelop(property.id, selectedLevel);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to develop property');
    }
  };

  const renderRequirements = () => {
    const { DEVELOPMENT_LEVELS, ZONING_REGULATIONS } = property;
    const zoning = ZONING_REGULATIONS[property.group_name.toLowerCase()];
    const currentLevel = DEVELOPMENT_LEVELS[property.improvement_level];
    const targetLevel = DEVELOPMENT_LEVELS[selectedLevel];

    return (
      <div className="development-requirements">
        <h3>Development Requirements</h3>
        
        {/* Zoning Information */}
        <div className="requirement-section">
          <h4>Zoning Information</h4>
          <p>Maximum Level: {zoning.max_level}</p>
          <p>Cost Modifier: {(zoning.cost_modifier * 100).toFixed(0)}%</p>
        </div>

        {/* Level Information */}
        <div className="requirement-section">
          <h4>Level Details</h4>
          <div className="level-comparison">
            <div className="current-level">
              <h5>Current: {currentLevel.name}</h5>
              <p>Rent Multiplier: {currentLevel.rent_multiplier}x</p>
              <p>Value Multiplier: {currentLevel.value_multiplier}x</p>
            </div>
            <div className="target-level">
              <h5>Target: {targetLevel.name}</h5>
              <p>Rent Multiplier: {targetLevel.rent_multiplier}x</p>
              <p>Value Multiplier: {targetLevel.value_multiplier}x</p>
            </div>
          </div>
        </div>

        {/* Development Costs */}
        {developmentCosts && (
          <div className="requirement-section">
            <h4>Development Costs</h4>
            <div className="costs-breakdown">
              {developmentCosts.level_costs.map(cost => (
                <div key={cost.level} className="cost-item">
                  <span>Level {cost.level}:</span>
                  <span className="cost-amount">${cost.cost}</span>
                </div>
              ))}
              <div className="total-cost">
                <span>Total Cost:</span>
                <span className="cost-amount">${developmentCosts.total_cost}</span>
              </div>
            </div>
          </div>
        )}

        {/* Approval Requirements */}
        {zoning.approval_required && selectedLevel >= 3 && (
          <div className="requirement-section">
            <h4>Community Approval</h4>
            {property.has_community_approval ? (
              <p className="requirement-met">✓ Community Approval Obtained</p>
            ) : (
              <button 
                onClick={() => onRequestApproval(property.id)}
                className="request-button"
              >
                Request Community Approval
              </button>
            )}
          </div>
        )}

        {/* Environmental Study */}
        {zoning.study_required && selectedLevel >= 4 && (
          <div className="requirement-section">
            <h4>Environmental Study</h4>
            {property.has_environmental_study ? (
              <p className="requirement-met">
                ✓ Environmental Study Complete
                {property.environmental_study_expires && (
                  <span className="study-expiry">
                    (Expires: {new Date(property.environmental_study_expires).toLocaleDateString()})
                  </span>
                )}
              </p>
            ) : (
              <button 
                onClick={() => onRequestStudy(property.id)}
                className="request-button"
              >
                Commission Environmental Study
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="modal-overlay">
      <div className="development-modal">
        <header className="modal-header">
          <h2>Develop Property: {property.name}</h2>
          <button onClick={onClose} className="close-button">×</button>
        </header>

        <div className="modal-content">
          {/* Level Selection */}
          <div className="level-selection">
            <label htmlFor="development-level">Development Level:</label>
            <select
              id="development-level"
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(Number(e.target.value))}
            >
              {Array.from({ length: property.max_development_level + 1 }, (_, i) => (
                <option 
                  key={i} 
                  value={i}
                  disabled={i < property.improvement_level}
                >
                  Level {i}: {property.DEVELOPMENT_LEVELS[i].name}
                </option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="loading-spinner">Loading development information...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : (
            renderRequirements()
          )}
        </div>

        <footer className="modal-footer">
          <button 
            onClick={onClose}
            className="cancel-button"
          >
            Cancel
          </button>
          <button
            onClick={handleDevelop}
            className="develop-button"
            disabled={
              loading || 
              selectedLevel <= property.improvement_level ||
              (developmentCosts && developmentCosts.total_cost > gameState.current_player.cash)
            }
          >
            Develop Property
          </button>
        </footer>
      </div>
    </div>
  );
};

PropertyDevelopmentModal.propTypes = {
  property: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    improvement_level: PropTypes.number.isRequired,
    max_development_level: PropTypes.number.isRequired,
    group_name: PropTypes.string.isRequired,
    has_community_approval: PropTypes.bool.isRequired,
    has_environmental_study: PropTypes.bool.isRequired,
    environmental_study_expires: PropTypes.string,
    DEVELOPMENT_LEVELS: PropTypes.object.isRequired,
    ZONING_REGULATIONS: PropTypes.object.isRequired
  }).isRequired,
  onClose: PropTypes.func.isRequired,
  onDevelop: PropTypes.func.isRequired,
  onRequestApproval: PropTypes.func.isRequired,
  onRequestStudy: PropTypes.func.isRequired,
  gameState: PropTypes.shape({
    current_player: PropTypes.shape({
      cash: PropTypes.number.isRequired
    }).isRequired
  }).isRequired
};

export default PropertyDevelopmentModal; 