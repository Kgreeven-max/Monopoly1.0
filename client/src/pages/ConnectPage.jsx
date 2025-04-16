import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/ConnectPage.css';

const ConnectPage = () => {
  const navigate = useNavigate();
  const [tunnelInfo, setTunnelInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch tunnel information
    const fetchTunnelInfo = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/remote/info');
        
        if (!response.ok) {
          throw new Error('Failed to fetch remote play information');
        }
        
        const data = await response.json();
        setTunnelInfo(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching tunnel info:', err);
        setError(err.message || 'An error occurred while fetching connection information');
        setLoading(false);
      }
    };
    
    fetchTunnelInfo();
  }, []);

  const handleGoHome = () => {
    navigate('/');
  };

  // Function to generate URL for remote play
  const getRemoteUrl = () => {
    if (!tunnelInfo || !tunnelInfo.remote_url) return null;
    return `${tunnelInfo.remote_url}/remote`;
  };

  return (
    <div className="connect-page">
      <header className="connect-header">
        <h1>Pi-nopoly Remote Play</h1>
        <button className="back-button" onClick={handleGoHome}>Back to Home</button>
      </header>
      
      <div className="connect-container">
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading connection information...</p>
          </div>
        ) : error ? (
          <div className="error-message">
            <h2>Could Not Load Connection Information</h2>
            <p>{error}</p>
            <button onClick={handleGoHome}>Return to Home</button>
          </div>
        ) : !tunnelInfo.remote_enabled ? (
          <div className="not-enabled">
            <h2>Remote Play Not Enabled</h2>
            <p>Remote play is currently not enabled on this server.</p>
            <p>Please contact the game administrator to enable remote play.</p>
          </div>
        ) : !tunnelInfo.remote_url ? (
          <div className="not-running">
            <h2>Remote Server Not Running</h2>
            <p>The remote play server is not currently running.</p>
            <p>Please contact the game administrator to start the remote play server.</p>
          </div>
        ) : (
          <div className="connection-info">
            <h2>Connect to Game</h2>
            
            <div className="qr-container">
              <img 
                src={`/api/remote/qr?key=${new URLSearchParams(window.location.search).get('key') || ''}`} 
                alt="QR Code for connection" 
                className="qr-code"
              />
              <p>Scan this QR code with your mobile device</p>
            </div>
            
            <div className="connection-steps">
              <h3>Connection Steps:</h3>
              <ol>
                <li>Scan the QR code above or visit <a href={getRemoteUrl()} target="_blank" rel="noopener noreferrer">{getRemoteUrl()}</a></li>
                <li>Enter your 4-digit PIN provided when you joined the game</li>
                <li>Wait for connection to be established</li>
                <li>Play the game from your device!</li>
              </ol>
            </div>
            
            <div className="connection-details">
              <h3>Connection Details:</h3>
              <div className="detail-item">
                <span className="label">Status:</span>
                <span className="value success">Active</span>
              </div>
              <div className="detail-item">
                <span className="label">URL:</span>
                <span className="value">{tunnelInfo.remote_url}</span>
              </div>
            </div>
            
            <div className="troubleshooting">
              <h3>Troubleshooting:</h3>
              <ul>
                <li>Make sure you're using a modern web browser</li>
                <li>Ensure your PIN was entered correctly</li>
                <li>If you get disconnected, simply refresh the page</li>
                <li>For connection problems, contact the game administrator</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConnectPage; 