import { motion, AnimatePresence } from 'framer-motion';
import { usePlayerStore, useMyPlayer, useIsMyTurn, useCurrentPhase } from '../store/playerStore';
import { useSocket } from '../hooks/useSocket';
import { SocketEvents } from '@pinopoly/shared';
import { ActionPanel } from '../components/ActionPanel';
import { StatusBar } from '../components/StatusBar';
import { PropertySheet } from '../components/PropertySheet';
import { DiceButton } from '../components/DiceButton';

export function GameScreen() {
  const { gameState, showPropertyDetails, showProperty } = usePlayerStore();
  const myPlayer = useMyPlayer();
  const isMyTurn = useIsMyTurn();
  const phase = useCurrentPhase();
  const { emit } = useSocket();

  if (!gameState || !myPlayer) return null;

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
            onRoll={() => emit(SocketEvents.ROLL_DICE, { playerId: myPlayer.id })}
            onBuy={() => emit(SocketEvents.BUY_PROPERTY, {
              playerId: myPlayer.id,
              propertyPosition: myPlayer.position,
            })}
            onEndTurn={() => emit(SocketEvents.END_TURN, { playerId: myPlayer.id })}
            onPayJailFine={() => emit(SocketEvents.PAY_JAIL_FINE, { playerId: myPlayer.id })}
          />
        )}

        {/* Dice button for rolling */}
        {isMyTurn && (phase === 'roll' || phase === 'preRoll') && (
          <div className="flex-1 flex items-center justify-center">
            <DiceButton
              onRoll={() => emit(SocketEvents.ROLL_DICE, { playerId: myPlayer.id })}
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
            onClose={() => showProperty(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function getPhaseInstruction(phase: string | null): string {
  switch (phase) {
    case 'preRoll':
      return 'Build houses or roll the dice';
    case 'roll':
      return 'Roll the dice!';
    case 'postRoll':
      return 'Buy property or end your turn';
    case 'jail':
      return 'Pay fine or try to roll doubles';
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
