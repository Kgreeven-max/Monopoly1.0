import { motion } from 'framer-motion';

interface Token {
  id: string;
  name: string;
  emoji: string;
  color: string;
}

interface TokenPickerProps {
  tokens: Token[];
  selected: string;
  onSelect: (tokenId: string) => void;
  disabledTokens?: string[];
}

export function TokenPicker({
  tokens,
  selected,
  onSelect,
  disabledTokens = [],
}: TokenPickerProps) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {tokens.map((token) => {
        const isSelected = selected === token.id;
        const isDisabled = disabledTokens.includes(token.id);

        return (
          <motion.button
            key={token.id}
            whileTap={{ scale: 0.95 }}
            onClick={() => !isDisabled && onSelect(token.id)}
            disabled={isDisabled}
            className={`
              relative aspect-square rounded-xl flex flex-col items-center justify-center
              transition-all duration-200
              ${isSelected
                ? 'ring-4 ring-white scale-105'
                : 'ring-2 ring-transparent hover:ring-white/30'
              }
              ${isDisabled
                ? 'opacity-40 cursor-not-allowed'
                : 'cursor-pointer'
              }
            `}
            style={{ backgroundColor: token.color + '40' }}
          >
            {/* Selection indicator */}
            {isSelected && (
              <motion.div
                layoutId="token-selection"
                className="absolute inset-0 rounded-xl border-2 border-white"
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}

            {/* Token emoji */}
            <span className="text-3xl mb-1">{token.emoji}</span>

            {/* Token name */}
            <span className="text-[10px] text-white/80 font-medium">
              {token.name}
            </span>

            {/* Taken indicator */}
            {isDisabled && (
              <div className="absolute top-1 right-1">
                <span className="text-xs">🚫</span>
              </div>
            )}
          </motion.button>
        );
      })}
    </div>
  );
}
