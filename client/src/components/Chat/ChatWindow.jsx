import React, { useState, useEffect, useRef } from 'react';
import { useSocket } from '../../contexts/SocketContext';
import { usePlayer } from '../../contexts/PlayerContext';
import ChatHeader from './ChatHeader';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ChannelList from './ChannelList';
import './ChatWindow.css';

const ChatWindow = () => {
  const { socket } = useSocket();
  const { player } = usePlayer();
  const [channels, setChannels] = useState([]);
  const [currentChannel, setCurrentChannel] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState({});
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef({});

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (!socket || !player) return;

    // Load channels
    socket.emit('get_channels', {
      player_id: player.id,
      pin: player.pin
    });

    // Listen for channel list
    const handleChannels = (data) => {
      setChannels(data.channels);
      // Set current channel to Global if not set
      if (!currentChannel) {
        const globalChannel = data.channels.find(c => c.name === 'Global');
        if (globalChannel) {
          setCurrentChannel(globalChannel);
          loadChannelMessages(globalChannel.id);
        }
      }
    };

    // Listen for new messages
    const handleMessage = (data) => {
      if (data.channel_id === currentChannel?.id) {
        setMessages(prev => [...prev, data]);
        scrollToBottom();
      }
    };

    // Listen for typing indicators
    const handleTyping = (data) => {
      if (data.channel_id === currentChannel?.id && data.player_id !== player.id) {
        setIsTyping(prev => ({
          ...prev,
          [data.player_id]: {
            player_name: data.player_name,
            timestamp: Date.now()
          }
        }));

        // Clear typing indicator after 3 seconds
        if (typingTimeoutRef.current[data.player_id]) {
          clearTimeout(typingTimeoutRef.current[data.player_id]);
        }
        typingTimeoutRef.current[data.player_id] = setTimeout(() => {
          setIsTyping(prev => {
            const newState = { ...prev };
            delete newState[data.player_id];
            return newState;
          });
        }, 3000);
      }
    };

    // Register event listeners
    socket.on('channels_list', handleChannels);
    socket.on('chat_message', handleMessage);
    socket.on('channel_typing', handleTyping);

    // Clean up
    return () => {
      socket.off('channels_list', handleChannels);
      socket.off('chat_message', handleMessage);
      socket.off('channel_typing', handleTyping);
      // Clear typing timeouts
      Object.values(typingTimeoutRef.current).forEach(timeout => clearTimeout(timeout));
    };
  }, [socket, player, currentChannel]);

  // Load messages for a channel
  const loadChannelMessages = (channelId) => {
    if (!socket || !player) return;

    socket.emit('get_channel_messages', {
      channel_id: channelId,
      player_id: player.id,
      pin: player.pin
    });
  };

  // Handle channel switch
  const handleChannelSwitch = (channel) => {
    setCurrentChannel(channel);
    setMessages([]);
    loadChannelMessages(channel.id);
  };

  // Handle message send
  const handleSendMessage = (content) => {
    if (!socket || !player || !currentChannel || !content.trim()) return;

    socket.emit('chat_message', {
      channel_id: currentChannel.id,
      sender_id: player.id,
      pin: player.pin,
      content: content.trim(),
      message_type: 'text'
    });
  };

  // Handle typing indicator
  const handleTypingIndicator = (isTyping) => {
    if (!socket || !player || !currentChannel) return;

    socket.emit('channel_typing', {
      channel_id: currentChannel.id,
      player_id: player.id,
      pin: player.pin,
      typing: isTyping
    });
  };

  return (
    <div className="chat-window">
      <div className="chat-sidebar">
        <ChannelList
          channels={channels}
          currentChannel={currentChannel}
          onChannelSelect={handleChannelSwitch}
        />
      </div>
      
      <div className="chat-main">
        <ChatHeader
          channel={currentChannel}
          typingUsers={Object.entries(isTyping).map(([id, data]) => data.player_name)}
        />
        
        <div className="chat-messages">
          {messages.map((message, index) => (
            <ChatMessage
              key={message.id || index}
              message={message}
              isOwnMessage={message.sender_id === player?.id}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        <ChatInput
          onSendMessage={handleSendMessage}
          onTyping={handleTypingIndicator}
        />
      </div>
    </div>
  );
};

export default ChatWindow; 