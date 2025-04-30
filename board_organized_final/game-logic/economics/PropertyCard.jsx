import React from 'react';
import PropTypes from 'prop-types';
import './PropertyCard.css';

const PropertyCard = ({ property, onAction, isOwned, canImprove }) => {
  const {
    name,
    group_name,
    current_price,
    current_rent,
    improvement_level,
    development_level_name,
    is_mortgaged,
    has_lien,
    damage_amount,
    has_community_approval,
    has_environmental_study
  } = property;

  // Calculate status indicators
  const needsRepair = damage_amount > 0;
  const canDevelop = canImprove && !is_mortgaged && !has_lien && !needsRepair;
  
  // Get color class based on property group
  const getGroupColorClass = (group) => `property-group-${group.toLowerCase()}`;

  return (
    <div className={`property-card ${isOwned ? 'owned' : ''}`}>
      <div className={`property-header ${getGroupColorClass(group_name)}`}>
        <h3>{name}</h3>
        <span className="property-group">{group_name}</span>
      </div>
      
      <div className="property-details">
        <div className="property-value">
          <span>Value:</span>
          <span className="amount">${current_price}</span>
        </div>
        <div className="property-rent">
          <span>Rent:</span>
          <span className="amount">${current_rent}</span>
        </div>
        <div className="property-development">
          <span>Level:</span>
          <span className="level">{development_level_name}</span>
        </div>
      </div>

      {/* Status indicators */}
      <div className="property-status">
        {is_mortgaged && (
          <span className="status-tag mortgaged">Mortgaged</span>
        )}
        {has_lien && (
          <span className="status-tag lien">Has Lien</span>
        )}
        {needsRepair && (
          <span className="status-tag damaged">Needs Repair</span>
        )}
        {has_community_approval && (
          <span className="status-tag approved">Community Approved</span>
        )}
        {has_environmental_study && (
          <span className="status-tag study">Environmental Study Complete</span>
        )}
      </div>

      {/* Action buttons */}
      <div className="property-actions">
        {isOwned && (
          <>
            {canDevelop && (
              <button 
                onClick={() => onAction('improve', property)}
                className="action-button improve"
              >
                Improve
              </button>
            )}
            {needsRepair && (
              <button 
                onClick={() => onAction('repair', property)}
                className="action-button repair"
              >
                Repair
              </button>
            )}
            {!is_mortgaged && (
              <button 
                onClick={() => onAction('mortgage', property)}
                className="action-button mortgage"
              >
                Mortgage
              </button>
            )}
            {is_mortgaged && (
              <button 
                onClick={() => onAction('unmortgage', property)}
                className="action-button unmortgage"
              >
                Unmortgage
              </button>
            )}
          </>
        )}
        <button 
          onClick={() => onAction('details', property)}
          className="action-button details"
        >
          Details
        </button>
      </div>
    </div>
  );
};

PropertyCard.propTypes = {
  property: PropTypes.shape({
    name: PropTypes.string.isRequired,
    group_name: PropTypes.string.isRequired,
    current_price: PropTypes.number.isRequired,
    current_rent: PropTypes.number.isRequired,
    improvement_level: PropTypes.number.isRequired,
    development_level_name: PropTypes.string.isRequired,
    is_mortgaged: PropTypes.bool.isRequired,
    has_lien: PropTypes.bool.isRequired,
    damage_amount: PropTypes.number.isRequired,
    has_community_approval: PropTypes.bool.isRequired,
    has_environmental_study: PropTypes.bool.isRequired
  }).isRequired,
  onAction: PropTypes.func.isRequired,
  isOwned: PropTypes.bool.isRequired,
  canImprove: PropTypes.bool.isRequired
};

export default PropertyCard; 