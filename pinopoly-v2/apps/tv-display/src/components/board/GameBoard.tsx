import { useMemo } from 'react';
import { motion } from 'framer-motion';
import type { GameState, PlayerState } from '@pinopoly/game-engine';
import { BoardSpace } from './BoardSpace';
import { PlayerToken } from './PlayerToken';
import { BOARD_LAYOUT } from './boardLayout';

interface GameBoardProps {
  gameState: GameState;
  players: PlayerState[];
}

export function GameBoard({ gameState, players }: GameBoardProps) {
  // Pre-calculate positions for all spaces
  const spacePositions = useMemo(() => {
    const positions: Record<number, { x: number; y: number; rotation: number }> = {};

    BOARD_LAYOUT.forEach((space, index) => {
      positions[index] = calculateSpacePosition(index);
    });

    return positions;
  }, []);

  // Group players by position for stacking
  const playersByPosition = useMemo(() => {
    const groups: Record<number, PlayerState[]> = {};

    players.forEach(player => {
      if (!player.isBankrupt) {
        if (!groups[player.position]) {
          groups[player.position] = [];
        }
        groups[player.position].push(player);
      }
    });

    return groups;
  }, [players]);

  return (
    <div className="relative" style={{ width: 'var(--board-size)', height: 'var(--board-size)' }}>
      {/* Board background */}
      <div className="absolute inset-0 bg-[#c8e6c9] rounded-lg shadow-2xl" />

      {/* Center area */}
      <div className="absolute inset-[12%] bg-[#c8e6c9] rounded flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-5xl font-display font-bold text-red-600 mb-2">
            PINOPOLY
          </h1>
          <p className="text-lg text-gray-600">Round {gameState.round}</p>
        </div>
      </div>

      {/* Board spaces */}
      {BOARD_LAYOUT.map((space, index) => {
        const position = spacePositions[index];
        const property = gameState.properties[index];

        return (
          <BoardSpace
            key={index}
            space={space}
            property={property}
            position={position}
            index={index}
          />
        );
      })}

      {/* Player tokens */}
      {Object.entries(playersByPosition).map(([posStr, playersAtPos]) => {
        const pos = parseInt(posStr);
        const spacePos = spacePositions[pos];

        return playersAtPos.map((player, stackIndex) => (
          <PlayerToken
            key={player.id}
            player={player}
            position={spacePos}
            stackIndex={stackIndex}
            totalAtPosition={playersAtPos.length}
          />
        ));
      })}
    </div>
  );
}

function calculateSpacePosition(index: number): { x: number; y: number; rotation: number } {
  const boardSize = 100; // Percentage
  const cornerSize = 12;
  const edgeSpaceWidth = (boardSize - cornerSize * 2) / 9;

  // Bottom row (0-10, GO to Jail/Visiting)
  if (index <= 10) {
    if (index === 0) {
      // GO (bottom-right corner)
      return { x: boardSize - cornerSize / 2, y: boardSize - cornerSize / 2, rotation: 0 };
    }
    if (index === 10) {
      // Jail (bottom-left corner)
      return { x: cornerSize / 2, y: boardSize - cornerSize / 2, rotation: 0 };
    }
    // Bottom edge (right to left)
    return {
      x: boardSize - cornerSize - (index - 0.5) * edgeSpaceWidth,
      y: boardSize - cornerSize / 2,
      rotation: 0,
    };
  }

  // Left column (11-19)
  if (index <= 19) {
    const leftIndex = index - 10;
    return {
      x: cornerSize / 2,
      y: boardSize - cornerSize - (leftIndex - 0.5) * edgeSpaceWidth,
      rotation: 90,
    };
  }

  // Top row (20-30)
  if (index <= 30) {
    if (index === 20) {
      // Free Parking (top-left corner)
      return { x: cornerSize / 2, y: cornerSize / 2, rotation: 0 };
    }
    if (index === 30) {
      // Go To Jail (top-right corner)
      return { x: boardSize - cornerSize / 2, y: cornerSize / 2, rotation: 0 };
    }
    // Top edge (left to right)
    const topIndex = index - 20;
    return {
      x: cornerSize + (topIndex - 0.5) * edgeSpaceWidth,
      y: cornerSize / 2,
      rotation: 180,
    };
  }

  // Right column (31-39)
  const rightIndex = index - 30;
  return {
    x: boardSize - cornerSize / 2,
    y: cornerSize + (rightIndex - 0.5) * edgeSpaceWidth,
    rotation: 270,
  };
}
