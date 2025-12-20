import { motion } from 'framer-motion';
import type { GameState, PlayerState } from '@pinopoly/game-engine';

interface ActionPanelProps {
  gameState: GameState;
  player: PlayerState;
  phase: string | null;
  onRoll: () => void;
  onBuy: () => void;
  onEndTurn: () => void;
  onPayJailFine: () => void;
}

export function ActionPanel({
  gameState,
  player,
  phase,
  onRoll,
  onBuy,
  onEndTurn,
  onPayJailFine,
}: ActionPanelProps) {
  const currentProperty = gameState.properties[player.position];
  const canBuyProperty = currentProperty &&
    !currentProperty.ownerId &&
    currentProperty.price &&
    player.money >= currentProperty.price;

  // Render different actions based on phase
  const renderActions = () => {
    switch (phase) {
      case 'jail':
        return (
          <div className="space-y-3">
            <p className="text-orange-400 text-center mb-4">
              You're in jail! ({player.jailTurns}/3 turns)
            </p>
            <button
              onClick={onPayJailFine}
              disabled={player.money < 50}
              className="btn-action btn-primary disabled:btn-disabled"
            >
              Pay $50 Fine
            </button>
            <button onClick={onRoll} className="btn-action btn-secondary">
              Try to Roll Doubles
            </button>
            {player.getOutOfJailCards && player.getOutOfJailCards > 0 && (
              <button className="btn-action bg-yellow-500 hover:bg-yellow-600 text-black">
                Use Get Out of Jail Card ({player.getOutOfJailCards})
              </button>
            )}
          </div>
        );

      case 'postRoll':
        return (
          <div className="space-y-3">
            {canBuyProperty && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <PropertyBuyCard
                  property={currentProperty}
                  playerMoney={player.money}
                  onBuy={onBuy}
                />
              </motion.div>
            )}

            <button onClick={onEndTurn} className="btn-action btn-secondary">
              End Turn
            </button>
          </div>
        );

      case 'preRoll':
        return (
          <div className="space-y-3">
            <BuildingActions
              gameState={gameState}
              player={player}
            />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      {renderActions()}
    </motion.div>
  );
}

interface PropertyBuyCardProps {
  property: any;
  playerMoney: number;
  onBuy: () => void;
}

function PropertyBuyCard({ property, playerMoney, onBuy }: PropertyBuyCardProps) {
  const canAfford = playerMoney >= (property.price || 0);

  return (
    <div className="bg-white/10 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-white font-bold">{property.name || 'Property'}</p>
          <p className="text-white/60 text-sm capitalize">
            {property.colorGroup || property.type}
          </p>
        </div>
        <div className="text-right">
          <p className="text-green-400 font-bold text-xl">
            ${property.price}
          </p>
        </div>
      </div>

      <button
        onClick={onBuy}
        disabled={!canAfford}
        className="btn-action btn-primary disabled:btn-disabled"
      >
        {canAfford ? 'Buy Property' : 'Cannot Afford'}
      </button>

      {canAfford && (
        <p className="text-white/50 text-xs text-center mt-2">
          After purchase: ${(playerMoney - property.price).toLocaleString()}
        </p>
      )}
    </div>
  );
}

interface BuildingActionsProps {
  gameState: GameState;
  player: PlayerState;
}

function BuildingActions({ gameState, player }: BuildingActionsProps) {
  // Find properties where player can build
  const buildableProperties = Object.entries(gameState.properties)
    .filter(([_, prop]) => {
      if (prop.ownerId !== player.id) return false;
      if (!prop.colorGroup) return false;
      if ((prop.houses || 0) >= 5) return false;

      // Check if player owns all properties in color group
      const sameColor = Object.values(gameState.properties)
        .filter(p => p.colorGroup === prop.colorGroup);
      const allOwned = sameColor.every(p => p.ownerId === player.id);

      return allOwned && player.money >= (prop.houseCost || 0);
    })
    .map(([pos, prop]) => ({ position: parseInt(pos), ...prop }));

  if (buildableProperties.length === 0) {
    return (
      <p className="text-white/50 text-center text-sm">
        No building options available
      </p>
    );
  }

  return (
    <div className="bg-white/10 rounded-2xl p-4">
      <p className="text-white/60 text-sm mb-3">Build Houses</p>
      <div className="space-y-2">
        {buildableProperties.slice(0, 3).map((prop) => (
          <div
            key={prop.position}
            className="flex items-center justify-between bg-white/5 rounded-xl p-3"
          >
            <div>
              <p className="text-white text-sm font-medium">
                {prop.name || `Property ${prop.position}`}
              </p>
              <p className="text-white/50 text-xs">
                {prop.houses || 0} houses • ${prop.houseCost}/house
              </p>
            </div>
            <button className="px-3 py-1 bg-yellow-500 text-black text-sm font-bold rounded-lg">
              Build
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
