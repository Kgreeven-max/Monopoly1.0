import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import PropertyCard from './PropertyCard';
import './PropertyList.css';

const PropertyList = ({ properties, onPropertyAction, currentPlayerId }) => {
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [searchTerm, setSearchTerm] = useState('');

  // Filter and sort properties
  const filteredAndSortedProperties = useMemo(() => {
    let filtered = [...properties];

    // Apply filters
    if (filterType === 'owned') {
      filtered = filtered.filter(p => p.owner_id === currentPlayerId);
    } else if (filterType === 'unowned') {
      filtered = filtered.filter(p => !p.owner_id);
    } else if (filterType === 'mortgaged') {
      filtered = filtered.filter(p => p.is_mortgaged);
    } else if (filterType === 'damaged') {
      filtered = filtered.filter(p => p.damage_amount > 0);
    }

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.group_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'price':
          return b.current_price - a.current_price;
        case 'rent':
          return b.current_rent - a.current_rent;
        case 'group':
          return a.group_name.localeCompare(b.group_name);
        default:
          return 0;
      }
    });
  }, [properties, filterType, sortBy, searchTerm, currentPlayerId]);

  // Group properties by color group
  const groupedProperties = useMemo(() => {
    return filteredAndSortedProperties.reduce((groups, property) => {
      const group = property.group_name;
      if (!groups[group]) {
        groups[group] = [];
      }
      groups[group].push(property);
      return groups;
    }, {});
  }, [filteredAndSortedProperties]);

  return (
    <div className="property-list">
      <div className="property-list-controls">
        {/* Search bar */}
        <input
          type="text"
          placeholder="Search properties..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="property-search"
        />

        {/* Filter dropdown */}
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="property-filter"
        >
          <option value="all">All Properties</option>
          <option value="owned">My Properties</option>
          <option value="unowned">Available Properties</option>
          <option value="mortgaged">Mortgaged Properties</option>
          <option value="damaged">Damaged Properties</option>
        </select>

        {/* Sort dropdown */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="property-sort"
        >
          <option value="name">Sort by Name</option>
          <option value="price">Sort by Price</option>
          <option value="rent">Sort by Rent</option>
          <option value="group">Sort by Group</option>
        </select>
      </div>

      {/* Property groups */}
      <div className="property-groups">
        {Object.entries(groupedProperties).map(([groupName, groupProperties]) => (
          <div key={groupName} className="property-group-section">
            <h2 className="property-group-header">{groupName}</h2>
            <div className="property-group-cards">
              {groupProperties.map(property => (
                <PropertyCard
                  key={property.id}
                  property={property}
                  onAction={onPropertyAction}
                  isOwned={property.owner_id === currentPlayerId}
                  canImprove={
                    property.owner_id === currentPlayerId &&
                    property.improvement_level < property.max_development_level
                  }
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* No results message */}
      {filteredAndSortedProperties.length === 0 && (
        <div className="no-properties">
          <p>No properties found matching your criteria.</p>
        </div>
      )}
    </div>
  );
};

PropertyList.propTypes = {
  properties: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      group_name: PropTypes.string.isRequired,
      current_price: PropTypes.number.isRequired,
      current_rent: PropTypes.number.isRequired,
      improvement_level: PropTypes.number.isRequired,
      max_development_level: PropTypes.number.isRequired,
      owner_id: PropTypes.number,
      is_mortgaged: PropTypes.bool.isRequired,
      damage_amount: PropTypes.number.isRequired
    })
  ).isRequired,
  onPropertyAction: PropTypes.func.isRequired,
  currentPlayerId: PropTypes.number.isRequired
};

export default PropertyList; 