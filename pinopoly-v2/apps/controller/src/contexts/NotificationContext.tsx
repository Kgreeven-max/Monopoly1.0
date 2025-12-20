import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

/**
 * Notification Context - Manages toast notifications for game events
 *
 * Replaces browser alert() calls with a proper toast notification system.
 * Notifications auto-dismiss after duration and support swipe-to-dismiss.
 */

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration: number; // ms
}

interface NotificationContextType {
  notifications: Notification[];
  notify: (notification: Omit<Notification, 'id' | 'duration'> & { duration?: number }) => void;
  dismiss: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

// Default durations by type
const DEFAULT_DURATIONS: Record<NotificationType, number> = {
  info: 4000,
  success: 3000,
  warning: 5000,
  error: 6000,
};

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const dismiss = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const notify = useCallback((notification: Omit<Notification, 'id' | 'duration'> & { duration?: number }) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const duration = notification.duration ?? DEFAULT_DURATIONS[notification.type];

    const newNotification: Notification = {
      id,
      type: notification.type,
      title: notification.title,
      message: notification.message,
      duration,
    };

    setNotifications(prev => [...prev, newNotification]);

    // Auto-dismiss after duration
    if (duration > 0) {
      setTimeout(() => {
        dismiss(id);
      }, duration);
    }
  }, [dismiss]);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        notify,
        dismiss,
        clearAll,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
}

// Convenience hooks for specific notification types
export function useNotify() {
  const { notify } = useNotification();

  return {
    info: (title: string, message?: string) => notify({ type: 'info', title, message }),
    success: (title: string, message?: string) => notify({ type: 'success', title, message }),
    warning: (title: string, message?: string) => notify({ type: 'warning', title, message }),
    error: (title: string, message?: string) => notify({ type: 'error', title, message }),
  };
}
