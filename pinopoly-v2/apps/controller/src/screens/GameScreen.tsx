import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePlayerStore, useMyPlayer, useIsMyTurn, useCurrentPhase } from '../store/playerStore';
import { useSocket } from '../hooks/useSocket';
import { SocketEvents } from '@pinopoly/shared';
import { ActionPanel } from '../components/ActionPanel';
import { StatusBar } from '../components/StatusBar';
import { PropertySheet } from '../components/PropertySheet';
import { DiceButton } from '../components/DiceButton';
import { TradeProposalModal, TradeResponseModal, TradeBadge } from '../components/TradeModal';

export function GameScreen() {
  const { gameState, showPropertyDetails, showProperty } = usePlayerStore();
  const myPlayer = useMyPlayer();
  const isMyTurn = useIsMyTurn();
  const phase = useCurrentPhase();
  const { emit } = useSocket();
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<string | null>(null);

  if (!gameState || !myPlayer) return null;

  // Get pending trades for this player
  const myPendingTrades = gameState.activeTrades?.filter(
    (t) => t.recipientId === myPlayer.id && t.status === 'pending'
  ) || [];

  const myProposedTrades = gameState.activeTrades?.filter(
    (t) => t.proposerId === myPlayer.id && t.status === 'pending'
  ) || [];

  const activeTrade = selectedTrade
    ? gameState.activeTrades?.find((t) => t.id === selectedTrade)
    : myPendingTrades[0] || myProposedTrades[0] || null;

  // Get current space info
  const currentSpace = gameState.properties[myPlayer.position];
  const currentSpaceName = getSpaceName(myPlayer.position);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Status bar */}
      <StatusBar player={myPlayer} isMyTurn={isMyTurn} />

      {/* Main content */}
      <div className="flex-1 flex flex-col p-4">
        {/* Turn indicator */}
        <AnimatePresence mode="wait">
          {isMyTurn ? (
            <motion.div
              key="my-turn"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-green-500/20 border border-green-500 rounded-2xl p-4 mb-4 text-center"
            >
              <p className="text-green-400 text-xl font-bold">
                Your Turn!
              </p>
              <p className="text-white/60 text-sm">
                {getPhaseInstruction(phase)}
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="waiting"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-white/10 rounded-2xl p-4 mb-4 text-center"
            >
              <p className="text-white/60">
                Waiting for {getCurrentPlayerName(gameState)}...
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Current position */}
        <div className="bg-white/10 rounded-2xl p-4 mb-4">
          <p className="text-white/50 text-sm mb-1">Your Position</p>
          <p className="text-white text-xl font-bold">{currentSpaceName}</p>
          {currentSpace && currentSpace.ownerId && currentSpace.ownerId !== myPlayer.id && (
            <p className="text-red-400 text-sm mt-1">
              Owned by {getOwnerName(gameState, currentSpace.ownerId)}
            </p>
          )}
        </div>

        {/* Action area */}
        {isMyTurn && (
          <ActionPanel
            gameState={gameState}
            player={myPlayer}
            phase={phase}
            onRoll={() => emit(SocketEvents.ROLL_DICE)}
            onBuy={() => emit(SocketEvents.BUY_PROPERTY, {
              propertyId: myPlayer.position,
            })}
            onEndTurn={() => emit(SocketEvents.END_TURN)}
            onPayJailFine={() => emit(SocketEvents.PAY_JAIL_FINE)}
            onBuildHouse={(propertyId) => emit(SocketEvents.BUILD_HOUSE, { propertyId })}
            onUseJailCard={() => emit(SocketEvents.USE_JAIL_CARD)}
            onExecuteCard={() => emit(SocketEvents.EXECUTE_CARD)}
            onPlaceBid={(amount) => emit(SocketEvents.AUCTION_BID, {
              auctionId: gameState.activeAuction?.id,
              amount,
            })}
            onPassAuction={() => emit(SocketEvents.AUCTION_PASS, {
              auctionId: gameState.activeAuction?.id,
            })}
            onDeclareBankruptcy={() => emit(SocketEvents.GAME_DECLARE_BANKRUPTCY)}
            onMortgage={(propertyId) => emit(SocketEvents.GAME_MORTGAGE, { propertyId })}
          />
        )}

        {/* Dice button for rolling */}
        {isMyTurn && phase === 'pre_roll' && (
          <div className="flex-1 flex items-center justify-center">
            <DiceButton
              onRoll={() => emit(SocketEvents.ROLL_DICE)}
            />
          </div>
        )}

        {/* Money display */}
        <div className="mt-auto pt-4">
          <div className="bg-green-500/20 rounded-2xl p-4 text-center">
            <p className="text-green-400 text-4xl font-bold">
              ${myPlayer.money.toLocaleString()}
            </p>
            <p className="text-white/50 text-sm">Your Cash</p>
          </div>
        </div>
      </div>

      {/* Property sheet modal */}
      <AnimatePresence>
        {showPropertyDetails !== null && (
          <PropertySheet
            position={showPropertyDetails}
            gameState={gameState}
            playerId={myPlayer.id}
            onClose={() => showProperty(null)}
            onMortgage={(propertyId) => emit(SocketEvents.GAME_MORTGAGE, { propertyId })}
            onUnmortgage={(propertyId) => emit(SocketEvents.GAME_UNMORTGAGE, { propertyId })}
          />
        )}
      </AnimatePresence>

      {/* Trade button - floating */}
      {phase === 'pre_roll' && (
        <button
          onClick={() => setShowTradeModal(true)}
          className="fixed bottom-24 left-4 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-full w-12 h-12 flex items-center justify-center shadow-lg z-40"
        >
          💱
        </button>
      )}

      {/* Trade proposal modal */}
      <AnimatePresence>
        {showTradeModal && (
          <TradeProposalModal
            gameState={gameState}
            myPlayer={myPlayer}
            onClose={() => setShowTradeModal(false)}
            onPropose={(recipientId, offer, request) => {
              emit(SocketEvents.TRADE_PROPOSE, {
                recipientId,
                offer,
                request,
              });
              setShowTradeModal(false);
            }}
          />
        )}
      </AnimatePresence>

      {/* Trade response modal */}
      <AnimatePresence>
        {activeTrade && (
          <TradeResponseModal
            trade={activeTrade}
            gameState={gameState}
            myPlayerId={myPlayer.id}
            onAccept={() => {
              emit(SocketEvents.TRADE_ACCEPT, { tradeId: activeTrade.id });
              setSelectedTrade(null);
            }}
            onReject={() => {
              emit(SocketEvents.TRADE_REJECT, { tradeId: activeTrade.id });
              setSelectedTrade(null);
            }}
            onClose={() => setSelectedTrade(null)}
          />
        )}
      </AnimatePresence>

      {/* Trade notification badge */}
      <TradeBadge
        count={myPendingTrades.length}
        onClick={() => {
          if (myPendingTrades.length > 0) {
            setSelectedTrade(myPendingTrades[0].id);
          }
        }}
      />
    </div>
  );
}

function getPhaseInstruction(phase: string | null): string {
  switch (phase) {
    case 'pre_roll':
      return 'Build houses or roll the dice';
    case 'rolling':
      return 'Rolling the dice...';
    case 'moving':
      return 'Moving...';
    case 'buy_decision':
      return 'Buy property or decline';
    case 'landed':
    case 'turn_end':
      return 'End your turn';
    case 'jail':
    case 'jail_decision':
      return 'Pay fine or try to roll doubles';
    case 'card_action':
      return 'Execute card action';
    default:
      return 'Take your action';
  }
}

function getCurrentPlayerName(gameState: any): string {
  const currentId = gameState.playerOrder[gameState.currentPlayerIndex];
  return gameState.players[currentId]?.name || 'Unknown';
}

function getOwnerName(gameState: any, ownerId: string): string {
  return gameState.players[ownerId]?.name || 'Unknown';
}

function getSpaceName(position: number): string {
  const names = [
    'GO', 'Mediterranean Ave', 'Community Chest', 'Baltic Ave', 'Income Tax',
    'Reading Railroad', 'Oriental Ave', 'Chance', 'Vermont Ave', 'Connecticut Ave',
    'Jail', 'St. Charles Place', 'Electric Company', 'States Ave', 'Virginia Ave',
    'Pennsylvania Railroad', 'St. James Place', 'Community Chest', 'Tennessee Ave', 'New York Ave',
    'Free Parking', 'Kentucky Ave', 'Chance', 'Indiana Ave', 'Illinois Ave',
    'B&O Railroad', 'Atlantic Ave', 'Ventnor Ave', 'Water Works', 'Marvin Gardens',
    'Go To Jail', 'Pacific Ave', 'North Carolina Ave', 'Community Chest', 'Pennsylvania Ave',
    'Short Line', 'Chance', 'Park Place', 'Luxury Tax', 'Boardwalk',
  ];
  return names[position] || `Space ${position}`;
}
