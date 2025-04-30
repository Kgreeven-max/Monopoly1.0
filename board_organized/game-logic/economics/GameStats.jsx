import React, { useState, useEffect } from 'react';
import { useGame } from '../contexts/GameContext';
import './GameStats.css';

const GameStats = () => {
  const { state } = useGame();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    economicStats: {},
    playerStats: [],
    propertyStats: {},
    eventStats: {}
  });

  useEffect(() => {
    const fetchGameStats = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/game/stats');
        const data = await response.json();
        
        if (data.success) {
          setStats(data.stats);
        } else {
          setError(data.error || 'Failed to fetch game statistics');
        }
      } catch (err) {
        setError('Error fetching game statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchGameStats();
  }, []);

  // Calculate player rankings based on net worth
  const playerRankings = [...(state.players || [])].sort((a, b) => (b.netWorth || 0) - (a.netWorth || 0));

  // Helper function to format currency values
  const formatCurrency = (value) => {
    return `$${value.toLocaleString()}`;
  };

  // Helper function to format percentage values
  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Helper function to determine economic state color
  const getEconomicStateColor = (state) => {
    const colors = {
      'recession': '#f44336',
      'normal': '#4caf50',
      'growth': '#2196f3',
      'boom': '#9c27b0'
    };
    return colors[state] || '#757575';
  };

  if (loading) {
    return (
      <div className="game-stats">
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Loading game statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="game-stats">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="game-stats">
      <h2 className="stats-title">Game Statistics</h2>
      
      {/* Navigation Tabs */}
      <div className="stats-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`} 
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'players' ? 'active' : ''}`} 
          onClick={() => setActiveTab('players')}
        >
          Players
        </button>
        <button 
          className={`tab-button ${activeTab === 'properties' ? 'active' : ''}`} 
          onClick={() => setActiveTab('properties')}
        >
          Properties
        </button>
        <button 
          className={`tab-button ${activeTab === 'events' ? 'active' : ''}`} 
          onClick={() => setActiveTab('events')}
        >
          Events
        </button>
      </div>
      
      <div className="stats-content">
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="stats-card economic-state">
              <h3>Economic State</h3>
              <div 
                className="economic-indicator"
                style={{ 
                  backgroundColor: getEconomicStateColor(state.economicState) 
                }}
              >
                <span className="economic-state-label">{state.economicState || 'Normal'}</span>
              </div>
              <div className="stats-details">
                <div className="stat-item">
                  <span>Inflation Rate:</span>
                  <span>{formatPercentage(stats.economicStats?.inflationRate || 0.03)}</span>
                </div>
                <div className="stat-item">
                  <span>Base Interest Rate:</span>
                  <span>{formatPercentage(stats.economicStats?.baseInterestRate || 0.05)}</span>
                </div>
                <div className="stat-item">
                  <span>Market Volatility:</span>
                  <span>{stats.economicStats?.marketVolatility || 'Normal'}</span>
                </div>
              </div>
            </div>
            
            <div className="stats-card game-info">
              <h3>Game Information</h3>
              <div className="stats-details">
                <div className="stat-item">
                  <span>Game Mode:</span>
                  <span>{state.gameMode || 'Classic'}</span>
                </div>
                <div className="stat-item">
                  <span>Current Turn:</span>
                  <span>{state.turn || 1}</span>
                </div>
                <div className="stat-item">
                  <span>Lap Number:</span>
                  <span>{state.lap || 1}</span>
                </div>
                <div className="stat-item">
                  <span>Community Fund:</span>
                  <span>{formatCurrency(stats.economicStats?.communityFund || 0)}</span>
                </div>
              </div>
            </div>
            
            <div className="stats-card property-summary">
              <h3>Property Summary</h3>
              <div className="stats-details">
                <div className="stat-item">
                  <span>Properties Owned:</span>
                  <span>{stats.propertyStats?.totalOwned || 0} / {stats.propertyStats?.total || 28}</span>
                </div>
                <div className="stat-item">
                  <span>Developed Properties:</span>
                  <span>{stats.propertyStats?.developed || 0}</span>
                </div>
                <div className="stat-item">
                  <span>Average Property Value:</span>
                  <span>{formatCurrency(stats.propertyStats?.averageValue || 200)}</span>
                </div>
                <div className="stat-item">
                  <span>Most Valuable Property:</span>
                  <span>{stats.propertyStats?.mostValuable?.name || 'None'}</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'players' && (
          <div className="players-section">
            <h3>Player Rankings</h3>
            <div className="player-rankings">
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Cash</th>
                    <th>Properties</th>
                    <th>Net Worth</th>
                  </tr>
                </thead>
                <tbody>
                  {playerRankings.map((player, index) => (
                    <tr key={player.id} className={player.id === state.currentPlayer?.id ? 'current-player' : ''}>
                      <td>{index + 1}</td>
                      <td>{player.name}</td>
                      <td>{formatCurrency(player.cash || 0)}</td>
                      <td>{player.properties?.length || 0}</td>
                      <td>{formatCurrency(player.netWorth || 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <h3>Player Statistics</h3>
            <div className="player-stats-grid">
              {state.players?.map(player => (
                <div key={player.id} className="player-stat-card">
                  <div className="player-header">
                    <h4>{player.name}</h4>
                    <span className={`player-status ${player.active ? 'active' : 'inactive'}`}>
                      {player.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="player-stats-details">
                    <div className="stat-item">
                      <span>Cash:</span>
                      <span>{formatCurrency(player.cash || 0)}</span>
                    </div>
                    <div className="stat-item">
                      <span>Properties:</span>
                      <span>{player.properties?.length || 0}</span>
                    </div>
                    <div className="stat-item">
                      <span>Net Worth:</span>
                      <span>{formatCurrency(player.netWorth || 0)}</span>
                    </div>
                    <div className="stat-item">
                      <span>Position:</span>
                      <span>{player.position || 0}</span>
                    </div>
                    <div className="stat-item">
                      <span>Bankrupt Count:</span>
                      <span>{player.bankruptcyCount || 0}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {activeTab === 'properties' && (
          <div className="properties-section">
            <h3>Property Statistics</h3>
            <div className="property-stats-summary">
              <div className="stat-card">
                <h4>Ownership Distribution</h4>
                <div className="stat-visualization ownership-chart">
                  {/* Simple bar chart visualization */}
                  <div className="bar-container">
                    {state.players?.map(player => (
                      <div 
                        key={player.id} 
                        className="player-bar" 
                        style={{ 
                          width: `${((player.properties?.length || 0) / (stats.propertyStats?.total || 28)) * 100}%`,
                          backgroundColor: player.color || '#999'
                        }}
                        title={`${player.name}: ${player.properties?.length || 0} properties`}
                      />
                    ))}
                    <div 
                      className="player-bar unowned" 
                      style={{ 
                        width: `${((stats.propertyStats?.total || 28) - (stats.propertyStats?.totalOwned || 0)) / (stats.propertyStats?.total || 28) * 100}%` 
                      }}
                      title={`Unowned: ${(stats.propertyStats?.total || 28) - (stats.propertyStats?.totalOwned || 0)} properties`}
                    />
                  </div>
                  <div className="chart-legend">
                    {state.players?.map(player => (
                      <div key={player.id} className="legend-item">
                        <span className="color-indicator" style={{ backgroundColor: player.color || '#999' }}></span>
                        <span>{player.name}</span>
                      </div>
                    ))}
                    <div className="legend-item">
                      <span className="color-indicator unowned"></span>
                      <span>Unowned</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="stat-card">
                <h4>Property Value Distribution</h4>
                <div className="stats-details">
                  <div className="stat-item">
                    <span>Lowest Value:</span>
                    <span>{formatCurrency(stats.propertyStats?.lowestValue || 60)}</span>
                  </div>
                  <div className="stat-item">
                    <span>Average Value:</span>
                    <span>{formatCurrency(stats.propertyStats?.averageValue || 200)}</span>
                  </div>
                  <div className="stat-item">
                    <span>Highest Value:</span>
                    <span>{formatCurrency(stats.propertyStats?.highestValue || 400)}</span>
                  </div>
                  <div className="stat-item">
                    <span>Total Value:</span>
                    <span>{formatCurrency(stats.propertyStats?.totalValue || 5600)}</span>
                  </div>
                </div>
              </div>
              
              <div className="stat-card">
                <h4>Development Status</h4>
                <div className="stats-details">
                  <div className="stat-item">
                    <span>Undeveloped:</span>
                    <span>{(stats.propertyStats?.totalOwned || 0) - (stats.propertyStats?.developed || 0)}</span>
                  </div>
                  <div className="stat-item">
                    <span>Level 1:</span>
                    <span>{stats.propertyStats?.level1 || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Level 2:</span>
                    <span>{stats.propertyStats?.level2 || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Level 3:</span>
                    <span>{stats.propertyStats?.level3 || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Level 4:</span>
                    <span>{stats.propertyStats?.level4 || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'events' && (
          <div className="events-section">
            <h3>Recent Events</h3>
            <div className="events-list">
              {(stats.eventStats?.recentEvents || []).length > 0 ? (
                <div className="event-timeline">
                  {(stats.eventStats?.recentEvents || []).map((event, index) => (
                    <div key={index} className={`event-item ${event.type.toLowerCase()}`}>
                      <div className="event-icon"></div>
                      <div className="event-content">
                        <h4>{event.name}</h4>
                        <p>{event.description}</p>
                        <span className="event-timestamp">Turn {event.turn}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-events">
                  <p>No events have occurred yet</p>
                </div>
              )}
            </div>
            
            <h3>Event Statistics</h3>
            <div className="event-stats-grid">
              <div className="stat-card">
                <h4>Event Type Distribution</h4>
                <div className="stats-details">
                  <div className="stat-item">
                    <span>Economic:</span>
                    <span>{stats.eventStats?.economicEvents || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Disaster:</span>
                    <span>{stats.eventStats?.disasterEvents || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Community:</span>
                    <span>{stats.eventStats?.communityEvents || 0}</span>
                  </div>
                  <div className="stat-item">
                    <span>Special:</span>
                    <span>{stats.eventStats?.specialEvents || 0}</span>
                  </div>
                </div>
              </div>
              
              <div className="stat-card">
                <h4>Event Impact</h4>
                <div className="stats-details">
                  <div className="stat-item">
                    <span>Property Value Impact:</span>
                    <span>{formatCurrency(stats.eventStats?.propertyValueImpact || 0)}</span>
                  </div>
                  <div className="stat-item">
                    <span>Player Cash Impact:</span>
                    <span>{formatCurrency(stats.eventStats?.playerCashImpact || 0)}</span>
                  </div>
                  <div className="stat-item">
                    <span>Total Property Damage:</span>
                    <span>{formatCurrency(stats.eventStats?.totalPropertyDamage || 0)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GameStats; 