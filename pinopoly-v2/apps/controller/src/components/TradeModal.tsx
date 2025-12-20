import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { GameState, PlayerState, TradeState } from '@pinopoly/game-engine';

// =============================================================================
// TRADE PROPOSAL MODAL
// =============================================================================

interface TradeProposalModalProps {
  gameState: GameState;
  myPlayer: PlayerState;
  onClose: () => void;
  onPropose: (recipientId: string, offer: TradeOffer, request: TradeOffer) => void;
}

interface TradeOffer {
  money: number;
  propertyIds: number[];
  getOutOfJailCards: number;
}

export function TradeProposalModal({
  gameState,
  myPlayer,
  onClose,
  onPropose,
}: TradeProposalModalProps) {
  const [selectedRecipient, setSelectedRecipient] = useState<string | null>(null);
  const [offerMoney, setOfferMoney] = useState(0);
  const [requestMoney, setRequestMoney] = useState(0);
  const [offerProperties, setOfferProperties] = useState<number[]>([]);
  const [requestProperties, setRequestProperties] = useState<number[]>([]);
  const [offerCards, setOfferCards] = useState(0);
  const [requestCards, setRequestCards] = useState(0);

  // Get other players
  const otherPlayers = Object.values(gameState.players).filter(
    (p) => p.id !== myPlayer.id && !p.isBankrupt
  );

  // Get my properties
  const myProperties = Object.entries(gameState.properties)
    .filter(([_, prop]) => prop.ownerId === myPlayer.id && !prop.isMortgaged)
    .map(([pos, prop]) => ({ position: parseInt(pos), ...prop }));

  // Get recipient's properties
  const recipientProperties = selectedRecipient
    ? Object.entries(gameState.properties)
        .filter(([_, prop]) => prop.ownerId === selectedRecipient && !prop.isMortgaged)
        .map(([pos, prop]) => ({ position: parseInt(pos), ...prop }))
    : [];

  const recipient = selectedRecipient ? gameState.players[selectedRecipient] : null;

  const handleSubmit = () => {
    if (!selectedRecipient) return;

    const offer: TradeOffer = {
      money: offerMoney,
      propertyIds: offerProperties,
      getOutOfJailCards: offerCards,
    };

    const request: TradeOffer = {
      money: requestMoney,
      propertyIds: requestProperties,
      getOutOfJailCards: requestCards,
    };

    onPropose(selectedRecipient, offer, request);
  };

  const toggleOfferProperty = (pos: number) => {
    setOfferProperties((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };

  const toggleRequestProperty = (pos: number) => {
    setRequestProperties((prev) =>
      prev.includes(pos) ? prev.filter((p) => p !== pos) : [...prev, pos]
    );
  };

  const hasOffer =
    offerMoney > 0 || offerProperties.length > 0 || offerCards > 0 ||
    requestMoney > 0 || requestProperties.length > 0 || requestCards > 0;

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/70 z-50"
      />

      {/* Modal */}
      <motion.div
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className="fixed bottom-0 left-0 right-0 bg-slate-800 rounded-t-3xl z-50 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-slate-800 p-4 border-b border-white/10">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white">Propose Trade</h2>
            <button
              onClick={onClose}
              className="p-2 text-white/60 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="p-4 space-y-6">
          {/* Step 1: Select Recipient */}
          {!selectedRecipient ? (
            <div className="space-y-3">
              <p className="text-white/60 text-sm">Select a player to trade with:</p>
              {otherPlayers.map((player) => (
                <button
                  key={player.id}
                  onClick={() => setSelectedRecipient(player.id)}
                  className="w-full flex items-center justify-between p-4 bg-white/10 hover:bg-white/20 rounded-xl transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-8 h-8 rounded-full"
                      style={{ backgroundColor: player.color }}
                    />
                    <span className="text-white font-medium">{player.name}</span>
                  </div>
                  <span className="text-green-400">${player.money}</span>
                </button>
              ))}
            </div>
          ) : (
            <>
              {/* Trade Recipient Header */}
              <div className="flex items-center justify-between bg-white/10 rounded-xl p-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-full"
                    style={{ backgroundColor: recipient?.color }}
                  />
                  <span className="text-white font-medium">Trading with {recipient?.name}</span>
                </div>
                <button
                  onClick={() => setSelectedRecipient(null)}
                  className="text-white/60 hover:text-white text-sm"
                >
                  Change
                </button>
              </div>

              {/* What You Offer */}
              <div className="space-y-3">
                <h3 className="text-white font-bold">You Offer:</h3>

                {/* Money */}
                <div className="bg-white/10 rounded-xl p-3">
                  <label className="text-white/60 text-sm block mb-2">Money</label>
                  <input
                    type="number"
                    value={offerMoney}
                    onChange={(e) => setOfferMoney(Math.min(myPlayer.money, Math.max(0, parseInt(e.target.value) || 0)))}
                    max={myPlayer.money}
                    min={0}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                  />
                  <p className="text-white/40 text-xs mt-1">Available: ${myPlayer.money}</p>
                </div>

                {/* Properties */}
                {myProperties.length > 0 && (
                  <div className="bg-white/10 rounded-xl p-3">
                    <label className="text-white/60 text-sm block mb-2">Properties</label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {myProperties.map((prop) => (
                        <label
                          key={prop.position}
                          className="flex items-center gap-2 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={offerProperties.includes(prop.position)}
                            onChange={() => toggleOfferProperty(prop.position)}
                            className="rounded"
                          />
                          <span className="text-white text-sm">
                            {prop.name || `Property ${prop.position}`}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* GOJF Cards */}
                {myPlayer.getOutOfJailCards > 0 && (
                  <div className="bg-white/10 rounded-xl p-3">
                    <label className="text-white/60 text-sm block mb-2">Get Out of Jail Cards</label>
                    <input
                      type="number"
                      value={offerCards}
                      onChange={(e) => setOfferCards(Math.min(myPlayer.getOutOfJailCards, Math.max(0, parseInt(e.target.value) || 0)))}
                      max={myPlayer.getOutOfJailCards}
                      min={0}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                    />
                    <p className="text-white/40 text-xs mt-1">Available: {myPlayer.getOutOfJailCards}</p>
                  </div>
                )}
              </div>

              {/* What You Request */}
              <div className="space-y-3">
                <h3 className="text-white font-bold">You Request:</h3>

                {/* Money */}
                <div className="bg-white/10 rounded-xl p-3">
                  <label className="text-white/60 text-sm block mb-2">Money</label>
                  <input
                    type="number"
                    value={requestMoney}
                    onChange={(e) => setRequestMoney(Math.min(recipient?.money || 0, Math.max(0, parseInt(e.target.value) || 0)))}
                    max={recipient?.money || 0}
                    min={0}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                  />
                  <p className="text-white/40 text-xs mt-1">They have: ${recipient?.money || 0}</p>
                </div>

                {/* Properties */}
                {recipientProperties.length > 0 && (
                  <div className="bg-white/10 rounded-xl p-3">
                    <label className="text-white/60 text-sm block mb-2">Properties</label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {recipientProperties.map((prop) => (
                        <label
                          key={prop.position}
                          className="flex items-center gap-2 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={requestProperties.includes(prop.position)}
                            onChange={() => toggleRequestProperty(prop.position)}
                            className="rounded"
                          />
                          <span className="text-white text-sm">
                            {prop.name || `Property ${prop.position}`}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* GOJF Cards */}
                {(recipient?.getOutOfJailCards || 0) > 0 && (
                  <div className="bg-white/10 rounded-xl p-3">
                    <label className="text-white/60 text-sm block mb-2">Get Out of Jail Cards</label>
                    <input
                      type="number"
                      value={requestCards}
                      onChange={(e) => setRequestCards(Math.min(recipient?.getOutOfJailCards || 0, Math.max(0, parseInt(e.target.value) || 0)))}
                      max={recipient?.getOutOfJailCards || 0}
                      min={0}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                    />
                    <p className="text-white/40 text-xs mt-1">They have: {recipient?.getOutOfJailCards || 0}</p>
                  </div>
                )}
              </div>

              {/* Submit */}
              <button
                onClick={handleSubmit}
                disabled={!hasOffer}
                className="w-full py-4 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-colors"
              >
                Propose Trade
              </button>
            </>
          )}
        </div>
      </motion.div>
    </>
  );
}

// =============================================================================
// TRADE RESPONSE MODAL
// =============================================================================

interface TradeResponseModalProps {
  trade: TradeState;
  gameState: GameState;
  myPlayerId: string;
  onAccept: () => void;
  onReject: () => void;
  onClose: () => void;
}

export function TradeResponseModal({
  trade,
  gameState,
  myPlayerId,
  onAccept,
  onReject,
  onClose,
}: TradeResponseModalProps) {
  const proposer = gameState.players[trade.proposerId];
  const isProposer = trade.proposerId === myPlayerId;

  const getPropertyName = (propId: number) => {
    const prop = gameState.properties[propId];
    return prop?.name || `Property ${propId}`;
  };

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/70 z-50"
      />

      {/* Modal */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="fixed inset-4 m-auto max-w-md max-h-[80vh] bg-slate-800 rounded-2xl z-50 overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-slate-800 p-4 border-b border-white/10">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white">
              {isProposer ? 'Your Trade Offer' : 'Trade Offer'}
            </h2>
            <button
              onClick={onClose}
              className="p-2 text-white/60 hover:text-white"
            >
              ✕
            </button>
          </div>
          <p className="text-white/60 text-sm mt-1">
            {isProposer
              ? 'Waiting for response...'
              : `From ${proposer?.name || 'Unknown'}`}
          </p>
        </div>

        <div className="p-4 space-y-4">
          {/* What They Offer (you receive) */}
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
            <h3 className="text-green-400 font-bold mb-3">You Receive:</h3>
            <div className="space-y-2">
              {trade.offer.money > 0 && (
                <p className="text-white">${trade.offer.money}</p>
              )}
              {trade.offer.propertyIds.map((propId) => (
                <p key={propId} className="text-white">{getPropertyName(propId)}</p>
              ))}
              {trade.offer.getOutOfJailCards > 0 && (
                <p className="text-white">
                  {trade.offer.getOutOfJailCards} Get Out of Jail Card(s)
                </p>
              )}
              {trade.offer.money === 0 &&
                trade.offer.propertyIds.length === 0 &&
                trade.offer.getOutOfJailCards === 0 && (
                <p className="text-white/50">Nothing</p>
              )}
            </div>
          </div>

          {/* What They Request (you give) */}
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
            <h3 className="text-red-400 font-bold mb-3">You Give:</h3>
            <div className="space-y-2">
              {trade.request.money > 0 && (
                <p className="text-white">${trade.request.money}</p>
              )}
              {trade.request.propertyIds.map((propId) => (
                <p key={propId} className="text-white">{getPropertyName(propId)}</p>
              ))}
              {trade.request.getOutOfJailCards > 0 && (
                <p className="text-white">
                  {trade.request.getOutOfJailCards} Get Out of Jail Card(s)
                </p>
              )}
              {trade.request.money === 0 &&
                trade.request.propertyIds.length === 0 &&
                trade.request.getOutOfJailCards === 0 && (
                <p className="text-white/50">Nothing</p>
              )}
            </div>
          </div>

          {/* Actions */}
          {!isProposer ? (
            <div className="flex gap-3">
              <button
                onClick={onAccept}
                className="flex-1 py-3 bg-green-500 hover:bg-green-600 text-white font-bold rounded-xl transition-colors"
              >
                Accept
              </button>
              <button
                onClick={onReject}
                className="flex-1 py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl transition-colors"
              >
                Reject
              </button>
            </div>
          ) : (
            <button
              onClick={onReject}
              className="w-full py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl transition-colors"
            >
              Cancel Trade
            </button>
          )}
        </div>
      </motion.div>
    </>
  );
}

// =============================================================================
// TRADE NOTIFICATION BADGE
// =============================================================================

interface TradeBadgeProps {
  count: number;
  onClick: () => void;
}

export function TradeBadge({ count, onClick }: TradeBadgeProps) {
  if (count === 0) return null;

  return (
    <button
      onClick={onClick}
      className="fixed bottom-24 right-4 bg-yellow-500 text-black font-bold rounded-full w-12 h-12 flex items-center justify-center shadow-lg z-40 animate-pulse"
    >
      {count}
    </button>
  );
}
