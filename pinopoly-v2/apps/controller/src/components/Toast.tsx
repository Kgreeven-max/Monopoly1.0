import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { useNotification, type Notification, type NotificationType } from '../contexts/NotificationContext';

const TYPE_STYLES: Record<NotificationType, { bg: string; border: string; icon: string }> = {
  info: {
    bg: 'bg-blue-500/90',
    border: 'border-blue-400',
    icon: 'ℹ️',
  },
  success: {
    bg: 'bg-green-500/90',
    border: 'border-green-400',
    icon: '✓',
  },
  warning: {
    bg: 'bg-yellow-500/90',
    border: 'border-yellow-400',
    icon: '⚠️',
  },
  error: {
    bg: 'bg-red-500/90',
    border: 'border-red-400',
    icon: '✕',
  },
};

interface ToastItemProps {
  notification: Notification;
  onDismiss: (id: string) => void;
}

function ToastItem({ notification, onDismiss }: ToastItemProps) {
  const style = TYPE_STYLES[notification.type];

  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    // Swipe to dismiss if dragged more than 100px horizontally
    if (Math.abs(info.offset.x) > 100) {
      onDismiss(notification.id);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.5}
      onDragEnd={handleDragEnd}
      className={`
        ${style.bg} ${style.border}
        border-l-4 rounded-lg shadow-lg
        px-4 py-3 min-w-[280px] max-w-[90vw]
        cursor-grab active:cursor-grabbing
        backdrop-blur-sm
      `}
      onClick={() => onDismiss(notification.id)}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <span className="text-lg flex-shrink-0">{style.icon}</span>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-white font-semibold text-sm">{notification.title}</p>
          {notification.message && (
            <p className="text-white/80 text-xs mt-0.5 line-clamp-2">{notification.message}</p>
          )}
        </div>

        {/* Dismiss hint */}
        <span className="text-white/50 text-xs flex-shrink-0">tap</span>
      </div>
    </motion.div>
  );
}

export function ToastContainer() {
  const { notifications, dismiss } = useNotification();

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 flex flex-col items-center gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {notifications.map(notification => (
          <div key={notification.id} className="pointer-events-auto">
            <ToastItem notification={notification} onDismiss={dismiss} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
}
