import { motion, AnimatePresence } from 'framer-motion';

interface DiceDisplayProps {
  dice: [number, number] | null;
  isRolling: boolean;
}

export function DiceDisplay({ dice, isRolling }: DiceDisplayProps) {
  if (!isRolling && !dice) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0, opacity: 0 }}
        className="flex gap-4"
      >
        <Die value={dice?.[0] || 1} isRolling={isRolling} />
        <Die value={dice?.[1] || 1} isRolling={isRolling} />
      </motion.div>
    </AnimatePresence>
  );
}

interface DieProps {
  value: number;
  isRolling: boolean;
}

function Die({ value, isRolling }: DieProps) {
  return (
    <motion.div
      animate={isRolling ? {
        rotateX: [0, 360, 720, 1080],
        rotateY: [0, 180, 360, 540],
      } : {}}
      transition={isRolling ? {
        duration: 0.8,
        ease: 'easeOut',
      } : {}}
      className="w-20 h-20 bg-white rounded-xl shadow-2xl flex items-center justify-center"
      style={{ perspective: 1000 }}
    >
      {isRolling ? (
        <motion.span
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ repeat: Infinity, duration: 0.2 }}
          className="text-4xl"
        >
          🎲
        </motion.span>
      ) : (
        <DiceFace value={value} />
      )}
    </motion.div>
  );
}

interface DiceFaceProps {
  value: number;
}

function DiceFace({ value }: DiceFaceProps) {
  const dotPositions: Record<number, [number, number][]> = {
    1: [[50, 50]],
    2: [[25, 25], [75, 75]],
    3: [[25, 25], [50, 50], [75, 75]],
    4: [[25, 25], [25, 75], [75, 25], [75, 75]],
    5: [[25, 25], [25, 75], [50, 50], [75, 25], [75, 75]],
    6: [[25, 25], [25, 50], [25, 75], [75, 25], [75, 50], [75, 75]],
  };

  const dots = dotPositions[value] || dotPositions[1];

  return (
    <svg viewBox="0 0 100 100" className="w-full h-full p-3">
      {dots.map(([x, y], index) => (
        <circle
          key={index}
          cx={x}
          cy={y}
          r={10}
          fill="#1a1a1a"
        />
      ))}
    </svg>
  );
}
