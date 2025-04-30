import React, { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext();

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((notification) => {
    const id = Date.now();
    const newNotification = {
      id,
      timestamp: new Date(),
      ...notification,
    };
    
    setNotifications((prev) => [...prev, newNotification]);
    
    // Auto-dismiss notifications if they have a duration
    if (notification.duration) {
      setTimeout(() => {
        dismissNotification(id);
      }, notification.duration);
    }
    
    return id;
  }, []);

  const dismissNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const value = {
    notifications,
    addNotification,
    dismissNotification,
    clearNotifications,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
} 