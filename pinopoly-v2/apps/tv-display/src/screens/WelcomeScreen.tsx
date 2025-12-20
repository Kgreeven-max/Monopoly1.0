import { useState } from 'react';
import { useSocket } from '../hooks/useSocket';
import { motion } from 'framer-motion';

export function WelcomeScreen() {
  const [roomCode, setRoomCode] = useState('');
  const [error, setError] = useState('');
  const { connect } = useSocket();

  const handleJoin = () => {
    const code = roomCode.trim().toUpperCase();
    if (code.length !== 4) {
      setError('Room code must be 4 characters');
      return;
    }
    setError('');
    connect(code);
  };

  const handleCreateGame = async () => {
    try {
      const response = await fetch('/api/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hostName: 'TV Display' }),
      });

      if (!response.ok) {
        throw new Error('Failed to create game');
      }

      const data = await response.json();
      connect(data.roomCode);
    } catch (err) {
      setError('Failed to create game. Please try again.');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen p-8">
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <h1 className="text-8xl font-display font-bold text-white mb-4">
          PINOPOLY
        </h1>
        <p className="text-2xl text-gray-400">
          The Ultimate Party Monopoly Experience
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md"
      >
        <h2 className="text-2xl font-display text-white mb-6 text-center">
          Join a Game
        </h2>

        <div className="mb-6">
          <input
            type="text"
            value={roomCode}
            onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
            placeholder="Enter Room Code"
            maxLength={4}
            className="w-full px-6 py-4 text-3xl text-center font-mono tracking-widest
                     bg-white/20 border border-white/30 rounded-xl text-white
                     placeholder-white/50 focus:outline-none focus:border-white/60"
          />
        </div>

        {error && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-red-400 text-center mb-4"
          >
            {error}
          </motion.p>
        )}

        <button
          onClick={handleJoin}
          disabled={roomCode.length !== 4}
          className="w-full py-4 bg-green-500 hover:bg-green-600 disabled:bg-gray-600
                   text-white text-xl font-bold rounded-xl transition-colors mb-4"
        >
          Join Game
        </button>

        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 h-px bg-white/20" />
          <span className="text-white/50">or</span>
          <div className="flex-1 h-px bg-white/20" />
        </div>

        <button
          onClick={handleCreateGame}
          className="w-full py-4 bg-blue-500 hover:bg-blue-600
                   text-white text-xl font-bold rounded-xl transition-colors"
        >
          Create New Game
        </button>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mt-12 text-center text-gray-500"
      >
        <p className="mb-2">Players join using their phones at:</p>
        <p className="text-2xl text-white font-mono">
          {window.location.hostname}/play
        </p>
      </motion.div>
    </div>
  );
}
