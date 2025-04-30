import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';

const ChatInput = ({ onSendMessage, onTyping }) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const typingTimeoutRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Clean up typing timeout on unmount
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  const handleTyping = () => {
    onTyping(true);

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set new timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      onTyping(false);
    }, 2000);
  };

  const handleChange = (e) => {
    setMessage(e.target.value);
    handleTyping();
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Don't send if still composing IME (for languages like Chinese, Japanese)
    if (isComposing) return;

    const trimmedMessage = message.trim();
    if (trimmedMessage) {
      onSendMessage(trimmedMessage);
      setMessage('');
      // Clear typing indicator
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      onTyping(false);
      // Focus input after sending
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    // Send message on Enter (but not with Shift+Enter)
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };

  return (
    <form className="chat-input" onSubmit={handleSubmit}>
      <textarea
        ref={inputRef}
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder="Type a message..."
        rows={1}
        maxLength={1000}
      />
      <button
        type="submit"
        className="send-button"
        disabled={!message.trim() || isComposing}
      >
        Send
      </button>
    </form>
  );
};

export default ChatInput; 