import React, { useEffect, useRef } from 'react';
import { useGame } from '../../contexts/GameContext';
import PropertySpace from './PropertySpace';
import SpecialSpace from './SpecialSpace';
import PlayerToken from './PlayerToken';
import './GameBoard.css';

const BOARD_SPACES = 40;
const SPACES_PER_SIDE = 10;

export default function GameBoard() {
  const { state } = useGame();
  const boardRef = useRef(null);

  // Calculate positions for each space on the board
  const calculateSpacePositions = () => {
    const positions = [];
    const board = boardRef.current;
    if (!board) return positions;

    const boardSize = board.offsetWidth;
    const spaceSize = boardSize / SPACES_PER_SIDE;

    for (let i = 0; i < BOARD_SPACES; i++) {
      let x, y;
      const side = Math.floor(i / SPACES_PER_SIDE);
      const offset = i % SPACES_PER_SIDE;

      switch (side) {
        case 0: // Bottom row
          x = boardSize - (offset + 1) * spaceSize;
          y = boardSize - spaceSize;
          break;
        case 1: // Left column
          x = 0;
          y = boardSize - (offset + 1) * spaceSize;
          break;
        case 2: // Top row
          x = offset * spaceSize;
          y = 0;
          break;
        case 3: // Right column
          x = boardSize - spaceSize;
          y = offset * spaceSize;
          break;
        default:
          x = 0;
          y = 0;
      }

      positions.push({ x, y });
    }

    return positions;
  };

  // Render board spaces
  const renderSpaces = () => {
    const positions = calculateSpacePositions();
    return state.properties.map((property, index) => (
      property.type === 'property' ? (
        <PropertySpace
          key={property.id}
          property={property}
          position={positions[index]}
        />
      ) : (
        <SpecialSpace
          key={property.id}
          space={property}
          position={positions[index]}
        />
      )
    ));
  };

  // Render player tokens
  const renderPlayers = () => {
    const positions = calculateSpacePositions();
    return state.players.map((player) => (
      <PlayerToken
        key={player.id}
        player={player}
        position={positions[player.position]}
      />
    ));
  };

  return (
    <div className="game-board-container">
      <div className="game-board" ref={boardRef}>
        {/* Center area with logo or game info */}
        <div className="board-center">
          <h2>Pi-nopoly</h2>
          <div className="game-info">
            <p>Mode: {state.gameMode}</p>
            <p>Turn: {state.turn}</p>
            <p>Community Fund: ${state.communityFund}</p>
          </div>
        </div>

        {/* Board spaces */}
        <div className="board-spaces">
          {renderSpaces()}
        </div>

        {/* Player tokens */}
        <div className="player-tokens">
          {renderPlayers()}
        </div>
      </div>
    </div>
  );
} 