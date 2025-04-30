import React from 'react';
import './ChatHeader.css';

const ChatHeader = ({ channel, typingUsers }) => {
  if (!channel) {
    return (
      <div className="chat-header">
        <div className="channel-info">
          <h3>Select a channel</h3>
        </div>
      </div>
    );
  }

  // Get channel icon based on type
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

  // Format typing indicator text
  const getTypingText = () => {
    if (!typingUsers || typingUsers.length === 0) return null;

    if (typingUsers.length === 1) {
      return `${typingUsers[0]} is typing...`;
    } else if (typingUsers.length === 2) {
      return `${typingUsers[0]} and ${typingUsers[1]} are typing...`;
    } else {
      return `${typingUsers.length} people are typing...`;
    }
  };

  return (
    <div className="chat-header">
      <div className="channel-info">
        <span className="channel-icon">{getChannelIcon(channel.type)}</span>
        <h3 className="channel-name">{channel.name}</h3>
        {channel.description && (
          <span className="channel-description" title={channel.description}>
            {channel.description}
          </span>
        )}
      </div>
      
      {/* Member count */}
      {channel.member_count && (
        <div className="member-count" title="Members">
          👥 {channel.member_count}
        </div>
      )}

      {/* Typing indicator */}
      {getTypingText() && (
        <div className="typing-indicator">
          {getTypingText()}
        </div>
      )}
    </div>
  );
};

export default ChatHeader; 