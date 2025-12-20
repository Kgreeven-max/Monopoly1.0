import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAdminStore } from '../store/adminStore';

export function LoginScreen() {
  const [adminKey, setAdminKey] = useState('');
  const { login, isLoading, error } = useAdminStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(adminKey);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎮 Pinopoly Admin
          </h1>
          <p className="text-slate-400">
            Enter your admin key to access the console
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card">
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Admin Key
            </label>
            <input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="Enter admin key..."
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg
                       text-white placeholder-slate-400
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm"
            >
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            disabled={isLoading || !adminKey}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600
                     text-white font-medium rounded-lg transition-colors"
          >
            {isLoading ? 'Authenticating...' : 'Login'}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-6">
          Contact your system administrator if you need access
        </p>
      </motion.div>
    </div>
  );
}
