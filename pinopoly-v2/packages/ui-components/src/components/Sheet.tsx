import { useEffect, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../utils/cn';

export interface SheetProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  side?: 'bottom' | 'right';
  className?: string;
}

export function Sheet({ isOpen, onClose, children, side = 'bottom', className }: SheetProps) {
  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  const slideVariants = {
    bottom: {
      initial: { y: '100%' },
      animate: { y: 0 },
      exit: { y: '100%' },
    },
    right: {
      initial: { x: '100%' },
      animate: { x: 0 },
      exit: { x: '100%' },
    },
  };

  const positionClasses = {
    bottom: 'bottom-0 left-0 right-0 rounded-t-3xl max-h-[90vh]',
    right: 'top-0 right-0 bottom-0 w-full max-w-md',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 z-40"
          />

          {/* Sheet */}
          <motion.div
            initial={slideVariants[side].initial}
            animate={slideVariants[side].animate}
            exit={slideVariants[side].exit}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={cn(
              'fixed bg-slate-800 z-50 overflow-y-auto',
              positionClasses[side],
              className
            )}
          >
            {/* Handle for bottom sheet */}
            {side === 'bottom' && (
              <div className="flex justify-center pt-3 pb-2">
                <div className="w-12 h-1 bg-white/30 rounded-full" />
              </div>
            )}

            {children}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
