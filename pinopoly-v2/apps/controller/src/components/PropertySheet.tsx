import { motion } from 'framer-motion';
import type { GameState } from '@pinopoly/game-engine';

interface PropertySheetProps {
  position: number;
  gameState: GameState;
  playerId?: string;
  onClose: () => void;
  onMortgage?: (propertyId: number) => void;
  onUnmortgage?: (propertyId: number) => void;
}

const SPACE_NAMES = [
  'GO', 'Mediterranean Avenue', 'Community Chest', 'Baltic Avenue', 'Income Tax',
  'Reading Railroad', 'Oriental Avenue', 'Chance', 'Vermont Avenue', 'Connecticut Avenue',
  'Jail', 'St. Charles Place', 'Electric Company', 'States Avenue', 'Virginia Avenue',
  'Pennsylvania Railroad', 'St. James Place', 'Community Chest', 'Tennessee Avenue', 'New York Avenue',
  'Free Parking', 'Kentucky Avenue', 'Chance', 'Indiana Avenue', 'Illinois Avenue',
  'B&O Railroad', 'Atlantic Avenue', 'Ventnor Avenue', 'Water Works', 'Marvin Gardens',
  'Go To Jail', 'Pacific Avenue', 'North Carolina Avenue', 'Community Chest', 'Pennsylvania Avenue',
  'Short Line', 'Chance', 'Park Place', 'Luxury Tax', 'Boardwalk',
];

const COLOR_CLASSES: Record<string, string> = {
  brown: 'bg-[#8B4513]',
  lightBlue: 'bg-[#87CEEB]',
  pink: 'bg-[#FF69B4]',
  orange: 'bg-[#FFA500]',
  red: 'bg-[#FF0000]',
  yellow: 'bg-[#FFFF00]',
  green: 'bg-[#008000]',
  blue: 'bg-[#0000FF]',
};

export function PropertySheet({ position, gameState, playerId, onClose, onMortgage, onUnmortgage }: PropertySheetProps) {
  const property = gameState.properties[position];
  const spaceName = SPACE_NAMES[position] || `Space ${position}`;

  const owner = property?.ownerId
    ? gameState.players[property.ownerId]
    : null;

  // Check if current player owns this property
  const isOwner = playerId && property?.ownerId === playerId;
  const player = playerId ? gameState.players[playerId] : null;

  // Calculate mortgage/unmortgage values
  const mortgageValue = property ? Math.floor((property.price || 0) / 2) : 0;
  const unmortgageCost = Math.floor(mortgageValue * 1.1); // 10% interest

  return (
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
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed bottom-0 left-0 right-0 bg-slate-800 rounded-t-3xl z-50 max-h-[80vh] overflow-y-auto"
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-12 h-1 bg-white/30 rounded-full" />
        </div>

        {/* Color band */}
        {property?.colorGroup && (
          <div className={`h-4 ${COLOR_CLASSES[property.colorGroup]}`} />
        )}

        {/* Content */}
        <div className="p-6">
          {/* Title */}
          <h2 className="text-2xl font-bold text-white mb-2">{spaceName}</h2>

          {property ? (
            <>
              {/* Property details */}
              <div className="space-y-4">
                {/* Price and owner */}
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-white/50 text-sm">Price</p>
                    <p className="text-2xl font-bold text-green-400">
                      ${property.price}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-white/50 text-sm">Owner</p>
                    <p className="text-lg font-bold text-white">
                      {owner ? owner.name : 'Unowned'}
                    </p>
                  </div>
                </div>

                {/* Rent table */}
                {property.colorGroup && (
                  <div className="bg-white/10 rounded-xl p-4">
                    <p className="text-white/60 text-sm mb-3">Rent</p>
                    <div className="space-y-2 text-sm">
                      <RentRow label="Base rent" amount={property.rent?.[0] || 0} />
                      <RentRow label="1 house" amount={property.rent?.[1] || 0} />
                      <RentRow label="2 houses" amount={property.rent?.[2] || 0} />
                      <RentRow label="3 houses" amount={property.rent?.[3] || 0} />
                      <RentRow label="4 houses" amount={property.rent?.[4] || 0} />
                      <RentRow label="Hotel" amount={property.rent?.[5] || 0} highlight />
                    </div>
                  </div>
                )}

                {/* Houses */}
                {property.colorGroup && (
                  <div className="flex items-center justify-between bg-white/10 rounded-xl p-4">
                    <div>
                      <p className="text-white/60 text-sm">Buildings</p>
                      <p className="text-white font-bold">
                        {(property.houses || 0) >= 5
                          ? '1 Hotel'
                          : `${property.houses || 0} Houses`
                        }
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-white/60 text-sm">House Cost</p>
                      <p className="text-white font-bold">${property.houseCost}</p>
                    </div>
                  </div>
                )}

                {/* Mortgage */}
                <div className="flex items-center justify-between bg-white/10 rounded-xl p-4">
                  <div>
                    <p className="text-white/60 text-sm">Mortgage Value</p>
                    <p className="text-white font-bold">
                      ${mortgageValue}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-white/60 text-sm">Status</p>
                    <p className={`font-bold ${property.isMortgaged ? 'text-red-400' : 'text-green-400'}`}>
                      {property.isMortgaged ? 'Mortgaged' : 'Active'}
                    </p>
                  </div>
                </div>

                {/* Mortgage Actions - only show if player owns this property */}
                {isOwner && (
                  <div className="space-y-2">
                    {property.isMortgaged ? (
                      <button
                        onClick={() => onUnmortgage?.(position)}
                        disabled={!player || player.money < unmortgageCost}
                        className="w-full py-3 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 disabled:cursor-not-allowed text-white rounded-xl font-bold transition-colors"
                      >
                        Unmortgage (${unmortgageCost})
                      </button>
                    ) : (
                      <button
                        onClick={() => onMortgage?.(position)}
                        disabled={(property.houses || 0) > 0}
                        className="w-full py-3 bg-yellow-500 hover:bg-yellow-600 disabled:bg-yellow-500/50 disabled:cursor-not-allowed text-black rounded-xl font-bold transition-colors"
                      >
                        Mortgage (+${mortgageValue})
                      </button>
                    )}
                    {(property.houses || 0) > 0 && !property.isMortgaged && (
                      <p className="text-yellow-400 text-xs text-center">
                        Sell all houses before mortgaging
                      </p>
                    )}
                    {property.isMortgaged && player && player.money < unmortgageCost && (
                      <p className="text-red-400 text-xs text-center">
                        Need ${unmortgageCost - player.money} more to unmortgage
                      </p>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <p className="text-white/50">
              This is a special space with no property.
            </p>
          )}

          {/* Close button */}
          <button
            onClick={onClose}
            className="w-full mt-6 py-4 bg-white/10 hover:bg-white/20 text-white rounded-xl font-bold"
          >
            Close
          </button>
        </div>
      </motion.div>
    </>
  );
}

function RentRow({
  label,
  amount,
  highlight,
}: {
  label: string;
  amount: number;
  highlight?: boolean;
}) {
  return (
    <div className={`flex justify-between ${highlight ? 'text-yellow-400 font-bold' : 'text-white'}`}>
      <span>{label}</span>
      <span>${amount}</span>
    </div>
  );
}
