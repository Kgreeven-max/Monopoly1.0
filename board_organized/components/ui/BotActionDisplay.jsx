import React, { useState, useEffect } from 'react';
import { socket } from '../services/socket';
import '../styles/BotActionDisplay.css';

const BotActionDisplay = () => {
  const [actions, setActions] = useState([]);
  const maxActionsToShow = 10;

  useEffect(() => {
    // Listen for bot actions
    const handleBotAction = (data) => {
      // Handle both regular actions and event triggers
      setActions(prevActions => {
        // Add the new action with timestamp
        const newAction = {
          ...data,
          timestamp: new Date()
        };
        
        // Keep only the latest actions (limited by maxActionsToShow)
        const updatedActions = [newAction, ...prevActions].slice(0, maxActionsToShow);
        return updatedActions;
      });
    };

    // Register event listeners
    socket.on('bot_action', handleBotAction);
    
    // Clean up event listeners
    return () => {
      socket.off('bot_action', handleBotAction);
    };
  }, []);

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Get appropriate icon for the action
  const getActionIcon = (action) => {
    switch (action) {
      case 'roll_dice':
        return '🎲';
      case 'buy_property':
        return '🏠';
      case 'decline_property':
        return '❌';
      case 'pay_rent':
        return '💸';
      case 'receive_money':
        return '💰';
      case 'pass_go':
        return '🔄';
      case 'draw_card':
        return '🃏';
      case 'go_to_jail':
        return '🚓';
      case 'get_out_of_jail':
        return '🔓';
      case 'improve_property':
        return '🏗️';
      case 'mortgage_property':
        return '📝';
      case 'unmortgage_property':
        return '✅';
      case 'trigger_event':
        return '✨'; // Default event icon
      default:
        return '🤖';
    }
  };

  // Get appropriate icon for event types
  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'trade_proposal':
        return '🤝';
      case 'property_auction':
        return '🔨';
      case 'market_crash':
        return '📉';
      case 'economic_boom':
        return '📈';
      case 'bot_challenge':
        return '🎯';
      default:
        return '✨';
    }
  };

  // Get appropriate CSS class for action type
  const getActionClass = (action, eventType) => {
    switch (action) {
      case 'roll_dice':
        return 'dice-action';
      case 'buy_property':
      case 'improve_property':
        return 'buy-action';
      case 'decline_property':
      case 'go_to_jail':
        return 'negative-action';
      case 'pay_rent':
        return 'pay-action';
      case 'receive_money':
      case 'pass_go':
      case 'get_out_of_jail':
        return 'positive-action';
      case 'draw_card':
        return 'card-action';
      case 'mortgage_property':
        return 'mortgage-action';
      case 'unmortgage_property':
        return 'unmortgage-action';
      case 'trigger_event':
        return `event-action ${getEventClass(eventType)}`;
      default:
        return '';
    }
  };

  // Get appropriate CSS class for event type
  const getEventClass = (eventType) => {
    switch (eventType) {
      case 'trade_proposal':
        return 'trade-event';
      case 'property_auction':
        return 'auction-event';
      case 'market_crash':
        return 'crash-event';
      case 'economic_boom':
        return 'boom-event';
      case 'bot_challenge':
        return 'challenge-event';
      default:
        return '';
    }
  };

  // Render a single action
  const renderAction = (action, index) => {
    return (
      <div 
        key={index} 
        className={`bot-action ${getActionClass(action.action, action.event_type)}`}
      >
        <div className="action-icon">
          {action.action === 'trigger_event' 
            ? getEventIcon(action.event_type) 
            : getActionIcon(action.action)}
        </div>
        <div className="action-content">
          <div className="action-header">
            <span className="bot-name">{action.bot_name}</span>
            <span className="action-time">{formatTime(action.timestamp)}</span>
          </div>
          <div className="action-message">{action.message}</div>
          {action.action === 'roll_dice' && action.data && (
            <div className="dice-result">
              Rolled: {action.data.dice1} + {action.data.dice2} = {action.data.dice1 + action.data.dice2}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bot-action-display">
      <h3>Bot Activities</h3>
      <div className="bot-actions-list">
        {actions.length === 0 ? (
          <div className="no-actions">No bot actions yet</div>
        ) : (
          actions.map((action, index) => renderAction(action, index))
        )}
      </div>
    </div>
  );
};

export default BotActionDisplay; 