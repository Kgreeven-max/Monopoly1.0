import React, { useState, useEffect } from 'react';
import { socket } from '../services/socket';
import '../styles/BotEventDisplay.css';

const BotEventDisplay = ({ playerId, playerPin }) => {
  const [activeEvents, setActiveEvents] = useState([]);
  const [marketEvents, setMarketEvents] = useState({});
  const [challengeResponses, setChallengeResponses] = useState({});
  
  useEffect(() => {
    // Listen for trade proposals from bots
    const handleTradeProposal = (data) => {
      setActiveEvents(prev => [...prev, {
        type: 'trade_proposal',
        id: data.event_id,
        botId: data.bot_id,
        botName: data.bot_name,
        message: data.message,
        offeredProperties: data.offered_properties || [],
        requestedProperties: data.requested_properties || [],
        cashAmount: data.cash_amount || 0,
        cashDirection: data.cash_direction || 'pay',
        timestamp: new Date()
      }]);
    };
    
    // Listen for challenges from bots
    const handleBotChallenge = (data) => {
      setActiveEvents(prev => [...prev, {
        type: 'challenge',
        id: data.event_id,
        botId: data.bot_id,
        botName: data.bot_name,
        message: data.message,
        challengeData: data.challenge_data,
        timestamp: new Date()
      }]);
    };
    
    // Listen for market events
    const handleMarketEvent = (data) => {
      // Add a notification for the event
      setActiveEvents(prev => [...prev, {
        type: data.event_type,
        id: data.event_id,
        message: data.event_data.message,
        affectedGroups: data.event_data.affected_groups,
        percentage: data.event_data.crash_percentage || data.event_data.boom_percentage,
        timestamp: new Date()
      }]);
      
      // Refresh market events info
      requestMarketEventsInfo();
    };
    
    // Listen for event results
    const handleTradeResult = (data) => {
      // Remove the trade from active events
      setActiveEvents(prev => prev.filter(event => 
        !(event.type === 'trade_proposal' && event.id === data.trade_id)
      ));
    };
    
    const handleChallengeResult = (data) => {
      // Remove the challenge from active events
      setActiveEvents(prev => prev.filter(event => 
        !(event.type === 'challenge' && event.id === data.challenge_id)
      ));
    };
    
    const handleEventExpired = (data) => {
      // Remove the expired event
      setActiveEvents(prev => prev.filter(event => event.id !== data.event_id));
    };
    
    const handleMarketRestoration = (data) => {
      // Add a notification for restoration
      setActiveEvents(prev => [...prev, {
        type: 'market_restored',
        id: `restore-${Date.now()}`,
        message: `Market prices have been restored for: ${data.affected_groups.join(', ')}`,
        timestamp: new Date()
      }]);
      
      // Refresh market events info
      requestMarketEventsInfo();
    };
    
    // Register event listeners
    socket.on('bot_trade_proposal', handleTradeProposal);
    socket.on('bot_challenge', handleBotChallenge);
    socket.on('market_event', handleMarketEvent);
    socket.on('trade_proposal_result', handleTradeResult);
    socket.on('challenge_result', handleChallengeResult);
    socket.on('trade_proposal_expired', handleEventExpired);
    socket.on('challenge_expired', handleEventExpired);
    socket.on('market_prices_restored', handleMarketRestoration);
    socket.on('market_events_info', (data) => {
      setMarketEvents(data.market_events || {});
    });
    
    // Request initial market events info
    requestMarketEventsInfo();
    
    // Clean up listeners on unmount
    return () => {
      socket.off('bot_trade_proposal', handleTradeProposal);
      socket.off('bot_challenge', handleBotChallenge);
      socket.off('market_event', handleMarketEvent);
      socket.off('trade_proposal_result', handleTradeResult);
      socket.off('challenge_result', handleChallengeResult);
      socket.off('trade_proposal_expired', handleEventExpired);
      socket.off('challenge_expired', handleEventExpired);
      socket.off('market_prices_restored', handleMarketRestoration);
      socket.off('market_events_info');
    };
  }, [playerId]);
  
  // Request current market events info
  const requestMarketEventsInfo = () => {
    if (playerId && playerPin) {
      socket.emit('market_event_info', {
        player_id: playerId,
        pin: playerPin
      });
    }
  };
  
  // Respond to a trade proposal
  const handleTradeResponse = (tradeId, accept) => {
    socket.emit('respond_to_trade_proposal', {
      player_id: playerId,
      pin: playerPin,
      trade_id: tradeId,
      accept: accept
    });
  };
  
  // Update challenge response field
  const updateChallengeResponse = (challengeId, value) => {
    setChallengeResponses({
      ...challengeResponses,
      [challengeId]: value
    });
  };
  
  // Submit a challenge response
  const submitChallengeResponse = (challengeId, challengeType) => {
    const response = challengeResponses[challengeId];
    if (response === undefined) return;
    
    let answer;
    
    // Process the response based on challenge type
    if (challengeType === 'price_guess' || challengeType === 'quick_calculation') {
      answer = parseInt(response, 10);
      if (isNaN(answer)) return;
    } else {
      answer = response;
    }
    
    socket.emit('respond_to_challenge', {
      player_id: playerId,
      pin: playerPin,
      challenge_id: challengeId,
      answer: answer
    });
  };
  
  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Render trade proposal
  const renderTradeProposal = (event) => {
    return (
      <div className="bot-event-card trade-proposal">
        <div className="event-header">
          <h4>Trade Offer from {event.botName}</h4>
          <span className="event-time">{formatTime(event.timestamp)}</span>
        </div>
        <p>{event.message}</p>
        
        <div className="trade-details">
          <div className="trade-properties">
            <div className="offered-properties">
              <h5>Bot Offers:</h5>
              <ul>
                {event.offeredProperties.map(prop => (
                  <li key={`offered-${prop.id}`}>{prop.name}</li>
                ))}
                {event.cashDirection === 'receive' && event.cashAmount > 0 && (
                  <li className="cash-item">${event.cashAmount}</li>
                )}
                {event.offeredProperties.length === 0 && event.cashDirection !== 'receive' && (
                  <li className="no-items">Nothing</li>
                )}
              </ul>
            </div>
            
            <div className="requested-properties">
              <h5>Bot Requests:</h5>
              <ul>
                {event.requestedProperties.map(prop => (
                  <li key={`requested-${prop.id}`}>{prop.name}</li>
                ))}
                {event.cashDirection === 'pay' && event.cashAmount > 0 && (
                  <li className="cash-item">${event.cashAmount}</li>
                )}
                {event.requestedProperties.length === 0 && event.cashDirection !== 'pay' && (
                  <li className="no-items">Nothing</li>
                )}
              </ul>
            </div>
          </div>
        </div>
        
        <div className="event-actions">
          <button 
            className="accept-button"
            onClick={() => handleTradeResponse(event.id, true)}
          >
            Accept
          </button>
          <button 
            className="decline-button"
            onClick={() => handleTradeResponse(event.id, false)}
          >
            Decline
          </button>
        </div>
      </div>
    );
  };
  
  // Render challenge
  const renderChallenge = (event) => {
    const challenge = event.challengeData;
    if (!challenge) return null;
    
    return (
      <div className="bot-event-card challenge">
        <div className="event-header">
          <h4>Challenge from {event.botName}</h4>
          <span className="event-time">{formatTime(event.timestamp)}</span>
        </div>
        <p>{event.message}</p>
        
        <div className="challenge-details">
          <div className="challenge-question">
            <h5>Question:</h5>
            <p>{challenge.question}</p>
          </div>
          
          <div className="challenge-reward">
            <h5>Reward:</h5>
            <p>
              {challenge.reward.type === 'cash' ? 
                `$${challenge.reward.amount}` : 
                challenge.reward.description}
            </p>
          </div>
          
          <div className="challenge-response">
            <h5>Your Answer:</h5>
            {challenge.challenge_type === 'dice_prediction' ? (
              <select 
                value={challengeResponses[event.id] || ''}
                onChange={e => updateChallengeResponse(event.id, parseInt(e.target.value, 10))}
              >
                <option value="">Select a number</option>
                {[...Array(11)].map((_, i) => (
                  <option key={i+2} value={i+2}>{i+2}</option>
                ))}
              </select>
            ) : (
              <input 
                type="text" 
                value={challengeResponses[event.id] || ''}
                onChange={e => updateChallengeResponse(event.id, e.target.value)}
                placeholder="Enter your answer"
              />
            )}
          </div>
        </div>
        
        <div className="event-actions">
          <button 
            className="submit-button"
            onClick={() => submitChallengeResponse(event.id, challenge.challenge_type)}
            disabled={challengeResponses[event.id] === undefined}
          >
            Submit Answer
          </button>
          <button 
            className="decline-button"
            onClick={() => submitChallengeResponse(event.id, null)}
          >
            Skip Challenge
          </button>
        </div>
      </div>
    );
  };
  
  // Render market event notification
  const renderMarketEvent = (event) => {
    const isMarketCrash = event.type === 'market_crash';
    const isBoom = event.type === 'economic_boom';
    const isRestored = event.type === 'market_restored';
    
    return (
      <div className={`bot-event-card market-event ${event.type}`}>
        <div className="event-header">
          <h4>
            {isMarketCrash ? 'Market Crash!' : 
             isBoom ? 'Economic Boom!' : 
             'Market Update'}
          </h4>
          <span className="event-time">{formatTime(event.timestamp)}</span>
        </div>
        <p>{event.message}</p>
        
        {!isRestored && event.affectedGroups && (
          <div className="affected-properties">
            <h5>Affected Property Groups:</h5>
            <ul>
              {event.affectedGroups.map(group => (
                <li key={group}>{group} ({event.percentage}%)</li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="event-actions">
          <button 
            className="info-button"
            onClick={requestMarketEventsInfo}
          >
            View Property Prices
          </button>
        </div>
      </div>
    );
  };
  
  // Render market prices info
  const renderMarketInfo = () => {
    if (Object.keys(marketEvents).length === 0) {
      return null;
    }
    
    return (
      <div className="market-info-section">
        <h3>Current Market Events</h3>
        {Object.entries(marketEvents).map(([group, data]) => (
          <div key={group} className={`market-group-info ${data.type}`}>
            <h4>{group} - {data.type === 'crash' ? 'Market Crash' : 'Economic Boom'} ({data.percentage}%)</h4>
            <ul className="property-price-list">
              {data.properties.map(prop => (
                <li key={prop.id}>
                  {prop.name}: ${prop.current_price} 
                  <span className={data.type === 'crash' ? 'price-down' : 'price-up'}>
                    ({data.type === 'crash' ? '-' : '+'}${data.type === 'crash' ? prop.discount : prop.premium})
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    );
  };
  
  // Main render
  return (
    <div className="bot-event-display">
      <h3>Bot Events</h3>
      
      {/* Market Info Section */}
      {Object.keys(marketEvents).length > 0 && renderMarketInfo()}
      
      {/* Active Events */}
      <div className="active-events">
        {activeEvents.length === 0 ? (
          <p className="no-events">No active events</p>
        ) : (
          activeEvents
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .map(event => (
              <div key={event.id} className="event-wrapper">
                {event.type === 'trade_proposal' && renderTradeProposal(event)}
                {event.type === 'challenge' && renderChallenge(event)}
                {(event.type === 'market_crash' || event.type === 'economic_boom' || event.type === 'market_restored') && 
                  renderMarketEvent(event)}
              </div>
            ))
        )}
      </div>
    </div>
  );
};

export default BotEventDisplay; 