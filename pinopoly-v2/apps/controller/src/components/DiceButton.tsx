import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DiceButtonProps {
  onRoll: () => void;
  disabled?: boolean;
}

export function DiceButton({ onRoll, disabled }: DiceButtonProps) {
  const [isRolling, setIsRolling] = useState(false);

  const handleRoll = () => {
    if (disabled || isRolling) return;

    setIsRolling(true);
    onRoll();

    // Reset after animation
    setTimeout(() => setIsRolling(false), 1000);
  };

  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      onClick={handleRoll}
      disabled={disabled || isRolling}
      className={`
        relative w-40 h-40 rounded-full
        flex items-center justify-center
        text-6xl shadow-2xl
        transition-colors
        ${disabled
          ? 'bg-gray-600 cursor-not-allowed'
          : 'bg-gradient-to-br from-red-500 to-red-700 cursor-pointer'
        }
      `}
    >
      {/* Pulse animation when active */}
      {!disabled && !isRolling && (
        <motion.div
          className="absolute inset-0 rounded-full bg-white"
          initial={{ opacity: 0, scale: 1 }}
          animate={{
            opacity: [0.3, 0],
            scale: [1, 1.3],
          }}
          transition={{
            repeat: Infinity,
            duration: 1.5,
            ease: 'easeOut',
          }}
        />
      )}

      {/* Rolling animation */}
      <AnimatePresence mode="wait">
        {isRolling ? (
          <motion.div
            key="rolling"
            initial={{ rotate: 0 }}
            animate={{ rotate: 360 }}
            transition={{
              repeat: 2,
              duration: 0.3,
              ease: 'linear',
            }}
            className="flex gap-2"
          >
            <span>🎲</span>
            <span>🎲</span>
          </motion.div>
        ) : (
          <motion.div
            key="static"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            className="flex flex-col items-center"
          >
            <span className="text-5xl mb-1">🎲</span>
            <span className="text-lg font-bold text-white">ROLL</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Glow effect */}
      {!disabled && (
        <div className="absolute inset-0 rounded-full bg-red-500 blur-xl opacity-30 -z-10" />
      )}
    </motion.button>
  );
}
