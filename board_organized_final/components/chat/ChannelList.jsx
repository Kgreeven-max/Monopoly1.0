import React, { useState } from 'react';
import { useSocket } from '../../contexts/SocketContext';
import { usePlayer } from '../../contexts/PlayerContext';
import './ChannelList.css';

const ChannelList = ({ channels, currentChannel, onChannelSelect }) => {
  const { socket } = useSocket();
  const { player } = usePlayer();
  const [showNewChannelForm, setShowNewChannelForm] = useState(false);
  const [newChannelName, setNewChannelName] = useState('');
  const [error, setError] = useState('');

  const handleCreateChannel = (e) => {
    e.preventDefault();
    if (!socket || !player) return;

    const trimmedName = newChannelName.trim();
    if (!trimmedName) {
      setError('Channel name is required');
      return;
    }

    socket.emit('create_channel', {
      creator_id: player.id,
      pin: player.pin,
      name: trimmedName,
      type: 'public'
    });

    // Reset form
    setNewChannelName('');
    setShowNewChannelForm(false);
    setError('');
  };

  const handleJoinChannel = (channel) => {
    if (!socket || !player) return;

    if (channel.type === 'public') {
      socket.emit('join_channel', {
        player_id: player.id,
        pin: player.pin,
        channel_id: channel.id
      });
    }

    onChannelSelect(channel);
  };

  const getChannelIcon = (type) => {
    switch (type) {
      case 'public':
        return '🌐';
      case 'private':
        return '🔒';
      case 'group':
        return '👥';
      default:
        return '#';
    }
  };

  return (
    <div className="channel-list">
      <div className="channel-list-header">
        <h3>Channels</h3>
        <button
          className="new-channel-button"
          onClick={() => setShowNewChannelForm(!showNewChannelForm)}
          title="Create new channel"
        >
          +
        </button>
      </div>

      {/* New channel form */}
      {showNewChannelForm && (
        <form className="new-channel-form" onSubmit={handleCreateChannel}>
          <input
            type="text"
            value={newChannelName}
            onChange={(e) => setNewChannelName(e.target.value)}
            placeholder="Channel name"
            maxLength={100}
          />
          {error && <div className="error-message">{error}</div>}
          <div className="form-actions">
            <button type="submit">Create</button>
            <button
              type="button"
              onClick={() => {
                setShowNewChannelForm(false);
                setNewChannelName('');
                setError('');
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Channel list */}
      <div className="channels">
        {channels.map(channel => (
          <button
            key={channel.id}
            className={`channel-item ${channel.id === currentChannel?.id ? 'active' : ''}`}
            onClick={() => handleJoinChannel(channel)}
          >
            <span className="channel-icon">{getChannelIcon(channel.type)}</span>
            <span className="channel-name">{channel.name}</span>
            {channel.unread_count > 0 && (
              <span className="unread-badge">{channel.unread_count}</span>
            )}
          </button>
        ))}

        {channels.length === 0 && (
          <div className="no-channels">
            No channels available
          </div>
        )}
      </div>
    </div>
  );
};

export default ChannelList; 