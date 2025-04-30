import React, { useState } from 'react';
import { useSocket } from '../../contexts/SocketContext';
import { usePlayer } from '../../contexts/PlayerContext';
import './ChatMessage.css';

const EMOJI_REACTIONS = ["👍", "👎", "😂", "😮", "😢", "🎉", "💰", "🏠", "🎲", "🚓"];

const ChatMessage = ({ message, isOwnMessage }) => {
  const { socket } = useSocket();
  const { player } = usePlayer();
  const [showReactions, setShowReactions] = useState(false);

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Handle reaction click
  const handleReaction = (emoji) => {
    if (!socket || !player) return;

    socket.emit('message_reaction', {
      message_id: message.id,
      player_id: player.id,
      pin: player.pin,
      emoji: emoji
    });

    setShowReactions(false);
  };

  // Get reaction counts
  const getReactionCounts = () => {
    const counts = {};
    Object.entries(message.reactions || {}).forEach(([emoji, users]) => {
      if (users.length > 0) {
        counts[emoji] = users.length;
      }
    });
    return counts;
  };

  // Check if current player has reacted with an emoji
  const hasReacted = (emoji) => {
    return message.reactions?.[emoji]?.includes(player?.id);
  };

  return (
    <div className={`chat-message ${isOwnMessage ? 'own-message' : ''}`}>
      {/* Message header */}
      <div className="message-header">
        <span className="sender-name">{message.sender_name}</span>
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>

      {/* Message content */}
      <div className="message-content">
        {message.content}
      </div>

      {/* Reactions */}
      <div className="message-reactions">
        {/* Existing reactions */}
        {Object.entries(getReactionCounts()).map(([emoji, count]) => (
          <button
            key={emoji}
            className={`reaction-badge ${hasReacted(emoji) ? 'reacted' : ''}`}
            onClick={() => handleReaction(emoji)}
            title={`${count} ${count === 1 ? 'reaction' : 'reactions'}`}
          >
            {emoji} {count}
          </button>
        ))}

        {/* Add reaction button */}
        <button
          className="add-reaction-button"
          onClick={() => setShowReactions(!showReactions)}
          title="Add reaction"
        >
          😀
        </button>

        {/* Reaction picker */}
        {showReactions && (
          <div className="reaction-picker">
            {EMOJI_REACTIONS.map(emoji => (
              <button
                key={emoji}
                className="emoji-button"
                onClick={() => handleReaction(emoji)}
              >
                {emoji}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage; 