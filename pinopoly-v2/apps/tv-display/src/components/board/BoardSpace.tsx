import { motion } from 'framer-motion';
import type { PropertyState } from '@pinopoly/game-engine';

interface SpaceDefinition {
  name: string;
  type: 'property' | 'railroad' | 'utility' | 'chance' | 'community' | 'tax' | 'corner';
  colorGroup?: string;
  price?: number;
}

interface BoardSpaceProps {
  space: SpaceDefinition;
  property?: PropertyState;
  position: { x: number; y: number; rotation: number };
  index: number;
}

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

export function BoardSpace({ space, property, position, index }: BoardSpaceProps) {
  const isCorner = index === 0 || index === 10 || index === 20 || index === 30;

  // Size based on whether it's a corner
  const width = isCorner ? '12%' : '8.67%';
  const height = isCorner ? '12%' : '12%';

  return (
    <motion.div
      className="absolute bg-[#e8f5e9] border border-gray-400 flex flex-col overflow-hidden"
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
        width,
        height,
        transform: `translate(-50%, -50%) rotate(${position.rotation}deg)`,
      }}
      whileHover={{ scale: 1.05, zIndex: 10 }}
    >
      {/* Color bar for properties */}
      {space.colorGroup && (
        <div className={`h-[25%] ${COLOR_CLASSES[space.colorGroup] || 'bg-gray-400'}`}>
          {/* Houses/Hotels */}
          {property && (property.houses || 0) > 0 && (
            <div className="flex justify-center gap-0.5 pt-0.5">
              {(property.houses || 0) >= 5 ? (
                <div className="w-3 h-2 bg-red-700 rounded-sm" title="Hotel" />
              ) : (
                Array.from({ length: property.houses || 0 }).map((_, i) => (
                  <div key={i} className="w-1.5 h-1.5 bg-green-700 rounded-sm" title="House" />
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Space content */}
      <div className="flex-1 flex flex-col items-center justify-center p-0.5 text-center"
           style={{ transform: `rotate(${-position.rotation}deg)` }}>
        <SpaceContent space={space} property={property} index={index} />
      </div>

      {/* Ownership indicator */}
      {property?.ownerId && (
        <div
          className="absolute bottom-0 left-0 right-0 h-1"
          style={{ backgroundColor: getOwnerColor(property.ownerId) }}
        />
      )}
    </motion.div>
  );
}

interface SpaceContentProps {
  space: SpaceDefinition;
  property?: PropertyState;
  index: number;
}

function SpaceContent({ space, property, index }: SpaceContentProps) {
  switch (space.type) {
    case 'corner':
      return <CornerContent index={index} />;
    case 'chance':
      return (
        <div className="text-center">
          <span className="text-2xl">❓</span>
          <p className="text-[6px] font-bold">CHANCE</p>
        </div>
      );
    case 'community':
      return (
        <div className="text-center">
          <span className="text-2xl">🏠</span>
          <p className="text-[6px] font-bold">COMMUNITY</p>
        </div>
      );
    case 'tax':
      return (
        <div className="text-center">
          <span className="text-lg">💰</span>
          <p className="text-[6px] font-bold">{space.name}</p>
          {space.price && <p className="text-[5px]">${space.price}</p>}
        </div>
      );
    case 'railroad':
      return (
        <div className="text-center">
          <span className="text-lg">🚂</span>
          <p className="text-[5px] font-bold leading-tight">{space.name}</p>
          {space.price && <p className="text-[5px]">${space.price}</p>}
        </div>
      );
    case 'utility':
      return (
        <div className="text-center">
          <span className="text-lg">{index === 12 ? '💡' : '🚰'}</span>
          <p className="text-[5px] font-bold leading-tight">{space.name}</p>
          {space.price && <p className="text-[5px]">${space.price}</p>}
        </div>
      );
    default:
      return (
        <div className="text-center">
          <p className="text-[5px] font-bold leading-tight">{space.name}</p>
          {space.price && <p className="text-[5px]">${space.price}</p>}
        </div>
      );
  }
}

function CornerContent({ index }: { index: number }) {
  switch (index) {
    case 0:
      return (
        <div className="text-center">
          <span className="text-3xl">➡️</span>
          <p className="text-xs font-bold">GO</p>
          <p className="text-[8px]">Collect $200</p>
        </div>
      );
    case 10:
      return (
        <div className="text-center">
          <span className="text-3xl">🔒</span>
          <p className="text-[8px] font-bold">JAIL</p>
        </div>
      );
    case 20:
      return (
        <div className="text-center">
          <span className="text-3xl">🅿️</span>
          <p className="text-[8px] font-bold">FREE</p>
          <p className="text-[8px] font-bold">PARKING</p>
        </div>
      );
    case 30:
      return (
        <div className="text-center">
          <span className="text-3xl">👮</span>
          <p className="text-[8px] font-bold">GO TO</p>
          <p className="text-[8px] font-bold">JAIL</p>
        </div>
      );
    default:
      return null;
  }
}

function getOwnerColor(ownerId: string): string {
  // Simple hash to color
  let hash = 0;
  for (let i = 0; i < ownerId.length; i++) {
    hash = ((hash << 5) - hash) + ownerId.charCodeAt(i);
  }
  const colors = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12', '#1abc9c', '#e91e63', '#00bcd4'];
  return colors[Math.abs(hash) % colors.length];
}
