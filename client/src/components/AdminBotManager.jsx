import React, { useState, useEffect } from 'react';
import { useSocket } from '../contexts/SocketContext';
import '../styles/AdminBotManager.css';

const BOT_TYPES = [
  { id: 'conservative', name: 'Conservative', description: 'Prioritizes cash reserves and safe investments' },
  { id: 'aggressive', name: 'Aggressive', description: 'Focuses on acquiring and developing properties' },
  { id: 'strategic', name: 'Strategic', description: 'Specializes in completing property groups' }
];

const DIFFICULTIES = [
  { id: 'easy', name: 'Easy', description: 'Makes more mistakes and less optimal decisions' },
  { id: 'normal', name: 'Normal', description: 'Balanced decision making with occasional mistakes' },
  { id: 'hard', name: 'Hard', description: 'Makes optimal decisions most of the time' }
];

const AdminBotManager = ({ adminKey }) => {
  const { socket } = useSocket();
  const [activeBots, setActiveBots] = useState([]);
  const [newBotName, setNewBotName] = useState('');
  const [selectedType, setSelectedType] = useState(BOT_TYPES[0].id);
  const [selectedDifficulty, setSelectedDifficulty] = useState(DIFFICULTIES[1].id);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (!socket) return;

    // Listen for bot added events
    const botAddedListener = (data) => {
      setActiveBots(prev => [...prev, data]);
      showNotification(`Bot ${data.name} added successfully`);
    };

    // Listen for bot removed events
    const botRemovedListener = (data) => {
      setActiveBots(prev => prev.filter(bot => bot.id !== data.bot_id));
      showNotification(data.message);
    };

    // Listen for bot updated events
    const botUpdatedListener = (data) => {
      setActiveBots(prev => 
        prev.map(bot => 
          bot.id === data.bot_id 
            ? { ...bot, difficulty: data.difficulty } 
            : bot
        )
      );
      showNotification(`Bot difficulty updated to ${data.difficulty}`);
    };

    // Listen for bot errors
    const botErrorListener = (data) => {
      showNotification(`Error: ${data.error}`, 'error');
    };

    // Listen for player joined events (to catch bots added elsewhere)
    const playerJoinedListener = (data) => {
      if (data.is_bot && !activeBots.some(bot => bot.id === data.player_id)) {
        setActiveBots(prev => [...prev, {
          id: data.player_id,
          name: data.player_name,
          type: 'unknown', // We don't know the type from this event
          difficulty: 'normal' // Assume normal as default
        }]);
      }
    };

    // Listen for player left events
    const playerLeftListener = (data) => {
      if (data.is_bot) {
        setActiveBots(prev => prev.filter(bot => bot.id !== data.player_id));
      }
    };

    socket.on('bot_added', botAddedListener);
    socket.on('bot_removed', botRemovedListener);
    socket.on('bot_updated', botUpdatedListener);
    socket.on('bot_error', botErrorListener);
    socket.on('player_joined', playerJoinedListener);
    socket.on('player_left', playerLeftListener);

    return () => {
      socket.off('bot_added', botAddedListener);
      socket.off('bot_removed', botRemovedListener);
      socket.off('bot_updated', botUpdatedListener);
      socket.off('bot_error', botErrorListener);
      socket.off('player_joined', playerJoinedListener);
      socket.off('player_left', playerLeftListener);
    };
  }, [socket, activeBots]);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const addBot = () => {
    if (!socket) return;

    socket.emit('add_bot', {
      admin_key: adminKey,
      name: newBotName || undefined,
      type: selectedType,
      difficulty: selectedDifficulty
    });

    // Clear the form
    setNewBotName('');
  };

  const removeBot = (botId) => {
    if (!socket) return;

    socket.emit('remove_bot', {
      admin_key: adminKey,
      bot_id: botId
    });
  };

  const changeBotDifficulty = (botId, difficulty) => {
    if (!socket) return;

    socket.emit('set_bot_difficulty', {
      admin_key: adminKey,
      bot_id: botId,
      difficulty: difficulty
    });
  };

  const getBotTypeInfo = (typeId) => {
    return BOT_TYPES.find(type => type.id === typeId) || { name: 'Unknown', description: '' };
  };

  return (
    <div className="admin-bot-manager">
      <h2>Bot Player Management</h2>
      
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}
      
      <div className="add-bot-form">
        <h3>Add New Bot</h3>
        <div className="form-row">
          <label>
            Name:
            <input 
              type="text" 
              value={newBotName} 
              onChange={(e) => setNewBotName(e.target.value)}
              placeholder="Bot Name (optional)"
            />
          </label>
        </div>
        
        <div className="form-row">
          <label>
            Bot Type:
            <select 
              value={selectedType} 
              onChange={(e) => setSelectedType(e.target.value)}
            >
              {BOT_TYPES.map(type => (
                <option key={type.id} value={type.id}>{type.name}</option>
              ))}
            </select>
          </label>
          
          <p className="type-description">
            {getBotTypeInfo(selectedType).description}
          </p>
        </div>
        
        <div className="form-row">
          <label>
            Difficulty:
            <select 
              value={selectedDifficulty} 
              onChange={(e) => setSelectedDifficulty(e.target.value)}
            >
              {DIFFICULTIES.map(diff => (
                <option key={diff.id} value={diff.id}>{diff.name}</option>
              ))}
            </select>
          </label>
        </div>
        
        <button className="add-bot-button" onClick={addBot}>
          Add Bot Player
        </button>
      </div>
      
      <div className="active-bots">
        <h3>Active Bot Players</h3>
        {activeBots.length === 0 ? (
          <p className="no-bots">No active bots. Add some!</p>
        ) : (
          <ul className="bot-list">
            {activeBots.map(bot => (
              <li key={bot.id} className="bot-item">
                <div className="bot-info">
                  <div className="bot-name">
                    <span className="bot-icon">🤖</span> {bot.name}
                  </div>
                  <div className="bot-details">
                    {bot.type !== 'unknown' && (
                      <span className="bot-type">
                        Type: {getBotTypeInfo(bot.type).name}
                      </span>
                    )}
                    <span className="bot-difficulty">
                      Difficulty: 
                      <select 
                        value={bot.difficulty} 
                        onChange={(e) => changeBotDifficulty(bot.id, e.target.value)}
                      >
                        {DIFFICULTIES.map(diff => (
                          <option key={diff.id} value={diff.id}>{diff.name}</option>
                        ))}
                      </select>
                    </span>
                  </div>
                </div>
                <button 
                  className="remove-bot-button"
                  onClick={() => removeBot(bot.id)}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default AdminBotManager; 