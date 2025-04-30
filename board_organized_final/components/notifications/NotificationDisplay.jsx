import React from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import './NotificationDisplay.css';

const NotificationDisplay = () => {
  const { notifications, dismissNotification } = useNotifications();

  if (!notifications || notifications.length === 0) {
    return null;
  }

  return (
    <div className="notification-container">
      {notifications.map((notification) => (
        <div 
          key={notification.id} 
          className={`notification notification-${notification.type || 'info'}`}
        >
          <div className="notification-content">
            {notification.title && (
              <div className="notification-title">{notification.title}</div>
            )}
            <div className="notification-message">{notification.message}</div>
          </div>
          <button 
            className="notification-dismiss" 
            onClick={() => dismissNotification(notification.id)}
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  );
};

export default NotificationDisplay; 