import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSocket } from '../hooks/useSocket';
import { usePlayerStore } from '../store/playerStore';
import { TokenPicker } from '../components/TokenPicker';

const TOKENS = [
  { id: 'car', name: 'Car', emoji: '🚗', color: '#e74c3c' },
  { id: 'dog', name: 'Dog', emoji: '🐕', color: '#3498db' },
  { id: 'hat', name: 'Top Hat', emoji: '🎩', color: '#2ecc71' },
  { id: 'ship', name: 'Ship', emoji: '🚢', color: '#9b59b6' },
  { id: 'boot', name: 'Boot', emoji: '👢', color: '#f39c12' },
  { id: 'thimble', name: 'Thimble', emoji: '🧵', color: '#1abc9c' },
  { id: 'iron', name: 'Iron', emoji: '🔧', color: '#e91e63' },
  { id: 'wheelbarrow', name: 'Wheelbarrow', emoji: '🛒', color: '#00bcd4' },
];

export function JoinScreen() {
  const { playerName: savedName, token: savedToken } = usePlayerStore();
  const { joinGame } = useSocket();

  const [step, setStep] = useState<'code' | 'name' | 'token'>('code');
  const [roomCode, setRoomCode] = useState('');
  const [playerName, setPlayerName] = useState(savedName || '');
  const [selectedToken, setSelectedToken] = useState(savedToken || 'car');
  const [error, setError] = useState('');

  // Check URL for room code
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('room');
    if (code) {
      setRoomCode(code.toUpperCase());
      setStep('name');
    }
  }, []);

  const handleCodeSubmit = () => {
    if (roomCode.length !== 6) {
      setError('Room code must be 6 characters');
      return;
    }
    setError('');
    setStep('name');
  };

  const handleNameSubmit = () => {
    if (playerName.trim().length < 2) {
      setError('Name must be at least 2 characters');
      return;
    }
    setError('');
    setStep('token');
  };

  const handleJoin = () => {
    joinGame(roomCode, playerName.trim(), selectedToken);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-5xl font-display font-bold text-white mb-2">
          PINOPOLY
        </h1>
        <p className="text-gray-400">Join the game!</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-sm"
      >
        {/* Step 1: Room Code */}
        {step === 'code' && (
          <div className="bg-white/10 backdrop-blur rounded-2xl p-6">
            <h2 className="text-xl font-bold text-white mb-4 text-center">
              Enter Room Code
            </h2>

            <input
              type="text"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              placeholder="ABCDEF"
              maxLength={6}
              autoFocus
              className="w-full px-4 py-4 text-3xl text-center font-mono tracking-[0.5em]
                       bg-white/20 border border-white/30 rounded-xl text-white
                       placeholder-white/30 focus:outline-none focus:border-white/60"
            />

            {error && (
              <p className="text-red-400 text-center mt-3">{error}</p>
            )}

            <button
              onClick={handleCodeSubmit}
              disabled={roomCode.length !== 6}
              className="btn-action btn-primary mt-6 disabled:btn-disabled"
            >
              Continue
            </button>
          </div>
        )}

        {/* Step 2: Player Name */}
        {step === 'name' && (
          <div className="bg-white/10 backdrop-blur rounded-2xl p-6">
            <button
              onClick={() => setStep('code')}
              className="text-white/50 mb-4 flex items-center gap-2"
            >
              ← Back
            </button>

            <h2 className="text-xl font-bold text-white mb-4 text-center">
              What's Your Name?
            </h2>

            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="Enter your name"
              maxLength={20}
              autoFocus
              className="w-full px-4 py-4 text-xl text-center
                       bg-white/20 border border-white/30 rounded-xl text-white
                       placeholder-white/30 focus:outline-none focus:border-white/60"
            />

            {error && (
              <p className="text-red-400 text-center mt-3">{error}</p>
            )}

            <button
              onClick={handleNameSubmit}
              disabled={playerName.trim().length < 2}
              className="btn-action btn-primary mt-6 disabled:btn-disabled"
            >
              Continue
            </button>
          </div>
        )}

        {/* Step 3: Token Selection */}
        {step === 'token' && (
          <div className="bg-white/10 backdrop-blur rounded-2xl p-6">
            <button
              onClick={() => setStep('name')}
              className="text-white/50 mb-4 flex items-center gap-2"
            >
              ← Back
            </button>

            <h2 className="text-xl font-bold text-white mb-4 text-center">
              Choose Your Token
            </h2>

            <TokenPicker
              tokens={TOKENS}
              selected={selectedToken}
              onSelect={setSelectedToken}
            />

            <button
              onClick={handleJoin}
              className="btn-action btn-primary mt-6"
            >
              Join Game
            </button>

            <p className="text-center text-white/50 text-sm mt-4">
              Room: <span className="font-mono font-bold">{roomCode}</span>
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
