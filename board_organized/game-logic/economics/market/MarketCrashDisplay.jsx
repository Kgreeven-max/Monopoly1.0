import React, { useState, useEffect } from 'react';
import { GameModeService } from '../services';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const MarketCrashDisplay = ({ gameId }) => {
  const [marketData, setMarketData] = useState(null);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [propertyHistory, setPropertyHistory] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);
        const [marketData, events] = await Promise.all([
          GameModeService.getMarketCrashData(gameId),
          GameModeService.getMarketCrashEvents(gameId)
        ]);
        
        setMarketData(marketData);
        setEvents(events);
        
        if (marketData.properties && marketData.properties.length > 0) {
          setSelectedProperty(marketData.properties[0]);
        }
      } catch (err) {
        setError(`Error loading market data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
  }, [gameId]);

  useEffect(() => {
    const fetchPropertyHistory = async () => {
      if (!selectedProperty) return;

      try {
        setLoading(true);
        const history = await GameModeService.getPropertyValueHistory(gameId, selectedProperty.id);
        setPropertyHistory(history);
      } catch (err) {
        setError(`Error loading property history: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchPropertyHistory();
  }, [gameId, selectedProperty]);

  if (loading) return <div>Loading market data...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!marketData) return <div>No market data available</div>;

  return (
    <div className="market-crash-display">
      <div className="market-overview">
        <h2>Market Overview</h2>
        <div className="market-stats">
          <div className="stat">
            <span className="label">Market Volatility:</span>
            <span className="value">{marketData.volatility.toFixed(2)}</span>
          </div>
          <div className="stat">
            <span className="label">Properties in Crash:</span>
            <span className="value">{marketData.propertiesInCrash}</span>
          </div>
          <div className="stat">
            <span className="label">Total Crashes:</span>
            <span className="value">{marketData.totalCrashes}</span>
          </div>
        </div>
      </div>

      <div className="property-selector">
        <h3>Select Property</h3>
        <select 
          value={selectedProperty?.id || ''} 
          onChange={(e) => {
            const prop = marketData.properties.find(p => p.id === e.target.value);
            setSelectedProperty(prop);
          }}
        >
          {marketData.properties.map(prop => (
            <option key={prop.id} value={prop.id}>
              {prop.name} (${prop.currentPrice})
            </option>
          ))}
        </select>
      </div>

      {selectedProperty && (
        <div className="property-details">
          <h3>{selectedProperty.name} Value History</h3>
          <div className="chart-container">
            <LineChart width={600} height={300} data={propertyHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="turn" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </div>
        </div>
      )}

      <div className="recent-events">
        <h3>Recent Market Events</h3>
        <ul>
          {events.map((event, index) => (
            <li key={index} className={`event ${event.type}`}>
              <span className="turn">Turn {event.turn}:</span>
              <span className="description">{event.description}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default MarketCrashDisplay; 