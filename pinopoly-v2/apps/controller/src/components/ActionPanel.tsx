import { useState } from 'react';
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
  onBuildHouse?: (propertyId: number) => void;
  onUseJailCard?: () => void;
  onExecuteCard?: () => void;
  onPlaceBid?: (amount: number) => void;
  onPassAuction?: () => void;
  onDeclareBankruptcy?: () => void;
  onMortgage?: (propertyId: number) => void;
}

export function ActionPanel({
  gameState,
  player,
  phase,
  onRoll,
  onBuy,
  onEndTurn,
  onPayJailFine,
  onBuildHouse,
  onUseJailCard,
  onExecuteCard,
  onPlaceBid,
  onPassAuction,
  onDeclareBankruptcy,
  onMortgage,
}: ActionPanelProps) {
  const currentProperty = gameState.properties[player.position];
  const canBuyProperty = currentProperty &&
    !currentProperty.ownerId &&
    currentProperty.price &&
    player.money >= currentProperty.price;

  // Render different actions based on phase (using snake_case from game engine)
  const renderActions = () => {
    switch (phase) {
      case 'jail':
      case 'jail_decision':
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
            {player.getOutOfJailCards && player.getOutOfJailCards > 0 && onUseJailCard && (
              <button
                onClick={onUseJailCard}
                className="btn-action bg-yellow-500 hover:bg-yellow-600 text-black"
              >
                Use Get Out of Jail Card ({player.getOutOfJailCards})
              </button>
            )}
          </div>
        );

      case 'buy_decision':
      case 'landed':
      case 'turn_end':
        return (
          <div className="space-y-3">
            {canBuyProperty && phase === 'buy_decision' && (
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

      case 'pre_roll':
        return (
          <div className="space-y-3">
            <BuildingActions
              gameState={gameState}
              player={player}
              onBuildHouse={onBuildHouse}
            />
          </div>
        );

      case 'card_action':
        return (
          <div className="space-y-3">
            <div className="bg-purple-500/20 border border-purple-500 rounded-2xl p-4 text-center">
              <p className="text-purple-400 text-lg font-bold mb-2">Card Action</p>
              <p className="text-white/60 text-sm mb-4">Execute the card effect</p>
              {onExecuteCard && (
                <button
                  onClick={onExecuteCard}
                  className="btn-action btn-primary"
                >
                  Execute Card
                </button>
              )}
            </div>
          </div>
        );

      case 'auction':
        return (
          <AuctionPanel
            gameState={gameState}
            player={player}
            onPlaceBid={onPlaceBid}
            onPassAuction={onPassAuction}
          />
        );

      case 'bankruptcy':
        return (
          <BankruptcyPanel
            gameState={gameState}
            player={player}
            onDeclareBankruptcy={onDeclareBankruptcy}
            onMortgage={onMortgage}
          />
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
  onBuildHouse?: (propertyId: number) => void;
}

function BuildingActions({ gameState, player, onBuildHouse }: BuildingActionsProps) {
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
            <button
              onClick={() => onBuildHouse?.(prop.position)}
              disabled={!onBuildHouse}
              className="px-3 py-1 bg-yellow-500 hover:bg-yellow-600 text-black text-sm font-bold rounded-lg disabled:opacity-50"
            >
              Build
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// AUCTION PANEL
// =============================================================================

interface AuctionPanelProps {
  gameState: GameState;
  player: PlayerState;
  onPlaceBid?: (amount: number) => void;
  onPassAuction?: () => void;
}

function AuctionPanel({ gameState, player, onPlaceBid, onPassAuction }: AuctionPanelProps) {
  const auction = gameState.activeAuction;
  const [bidAmount, setBidAmount] = useState(auction ? auction.currentBid + 10 : 10);

  if (!auction) {
    return (
      <div className="bg-white/10 rounded-2xl p-4 text-center">
        <p className="text-white/60">No active auction</p>
      </div>
    );
  }

  const property = gameState.properties[auction.propertyId];
  const isParticipant = auction.participants.includes(player.id);
  const hasPassed = auction.passed.includes(player.id);
  const isHighestBidder = auction.highestBidderId === player.id;
  const canBid = isParticipant && !hasPassed && player.money >= bidAmount && bidAmount > auction.currentBid;

  const highestBidderName = auction.highestBidderId
    ? gameState.players[auction.highestBidderId]?.name || 'Unknown'
    : 'No bids yet';

  return (
    <div className="space-y-4">
      {/* Auction Header */}
      <div className="bg-yellow-500/20 border border-yellow-500 rounded-2xl p-4 text-center">
        <p className="text-yellow-400 text-lg font-bold mb-1">AUCTION</p>
        <p className="text-white font-bold">{property?.name || `Property ${auction.propertyId}`}</p>
        <p className="text-white/60 text-sm capitalize">{property?.colorGroup || property?.type}</p>
      </div>

      {/* Current Bid */}
      <div className="bg-white/10 rounded-2xl p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-white/60">Current Bid</span>
          <span className="text-green-400 font-bold text-2xl">${auction.currentBid}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-white/60 text-sm">Highest Bidder</span>
          <span className={`text-sm font-medium ${isHighestBidder ? 'text-green-400' : 'text-white'}`}>
            {isHighestBidder ? 'You!' : highestBidderName}
          </span>
        </div>
      </div>

      {/* Bid Controls */}
      {isParticipant && !hasPassed && (
        <div className="bg-white/10 rounded-2xl p-4 space-y-3">
          <div>
            <label className="text-white/60 text-sm block mb-2">Your Bid</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={bidAmount}
                onChange={(e) => setBidAmount(Math.max(auction.currentBid + 1, parseInt(e.target.value) || 0))}
                min={auction.currentBid + 1}
                max={player.money}
                className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-lg font-bold focus:outline-none focus:border-yellow-500"
              />
            </div>
          </div>

          {/* Quick bid buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => setBidAmount(auction.currentBid + 10)}
              className="flex-1 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm"
            >
              +$10
            </button>
            <button
              onClick={() => setBidAmount(auction.currentBid + 50)}
              className="flex-1 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm"
            >
              +$50
            </button>
            <button
              onClick={() => setBidAmount(auction.currentBid + 100)}
              className="flex-1 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm"
            >
              +$100
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => onPlaceBid?.(bidAmount)}
              disabled={!canBid}
              className="flex-1 py-3 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-colors"
            >
              Bid ${bidAmount}
            </button>
            <button
              onClick={onPassAuction}
              className="flex-1 py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl transition-colors"
            >
              Pass
            </button>
          </div>

          {bidAmount > player.money && (
            <p className="text-red-400 text-xs text-center">
              Bid exceeds your available funds (${player.money})
            </p>
          )}
        </div>
      )}

      {hasPassed && (
        <div className="bg-red-500/20 border border-red-500 rounded-2xl p-4 text-center">
          <p className="text-red-400">You have passed on this auction</p>
        </div>
      )}

      {!isParticipant && (
        <div className="bg-white/10 rounded-2xl p-4 text-center">
          <p className="text-white/60">You are not participating in this auction</p>
        </div>
      )}

      {/* Remaining bidders */}
      <div className="text-white/50 text-xs text-center">
        {auction.participants.length - auction.passed.length} bidders remaining
      </div>
    </div>
  );
}

// =============================================================================
// BANKRUPTCY PANEL
// =============================================================================

interface BankruptcyPanelProps {
  gameState: GameState;
  player: PlayerState;
  onDeclareBankruptcy?: () => void;
  onMortgage?: (propertyId: number) => void;
}

function BankruptcyPanel({ gameState, player, onDeclareBankruptcy, onMortgage }: BankruptcyPanelProps) {
  // Find mortgageable properties
  const mortgageableProperties = Object.entries(gameState.properties)
    .filter(([_, prop]) => {
      return prop.ownerId === player.id && !prop.isMortgaged && (prop.houses || 0) === 0;
    })
    .map(([pos, prop]) => ({ position: parseInt(pos), ...prop }));

  return (
    <div className="space-y-4">
      {/* Bankruptcy Warning */}
      <div className="bg-red-500/20 border border-red-500 rounded-2xl p-4 text-center">
        <p className="text-red-400 text-lg font-bold mb-2">BANKRUPTCY WARNING</p>
        <p className="text-white/60 text-sm">
          You cannot afford your current debt. Mortgage properties or declare bankruptcy.
        </p>
      </div>

      {/* Current Status */}
      <div className="bg-white/10 rounded-2xl p-4">
        <div className="flex justify-between items-center">
          <span className="text-white/60">Your Cash</span>
          <span className="text-red-400 font-bold">${player.money}</span>
        </div>
      </div>

      {/* Mortgageable Properties */}
      {mortgageableProperties.length > 0 && (
        <div className="bg-white/10 rounded-2xl p-4">
          <p className="text-white/60 text-sm mb-3">Mortgage to Raise Cash</p>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {mortgageableProperties.map((prop) => (
              <div
                key={prop.position}
                className="flex items-center justify-between bg-white/5 rounded-xl p-3"
              >
                <div>
                  <p className="text-white text-sm font-medium">
                    {prop.name || `Property ${prop.position}`}
                  </p>
                  <p className="text-green-400 text-xs">
                    +${Math.floor((prop.price || 0) / 2)}
                  </p>
                </div>
                <button
                  onClick={() => onMortgage?.(prop.position)}
                  className="px-3 py-1 bg-yellow-500 hover:bg-yellow-600 text-black text-sm font-bold rounded-lg"
                >
                  Mortgage
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {mortgageableProperties.length === 0 && (
        <div className="bg-white/10 rounded-2xl p-4 text-center">
          <p className="text-white/50 text-sm">No properties available to mortgage</p>
        </div>
      )}

      {/* Declare Bankruptcy */}
      <button
        onClick={onDeclareBankruptcy}
        className="w-full py-4 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl transition-colors"
      >
        Declare Bankruptcy
      </button>

      <p className="text-white/40 text-xs text-center">
        Declaring bankruptcy will forfeit all your properties and eliminate you from the game.
      </p>
    </div>
  );
}
