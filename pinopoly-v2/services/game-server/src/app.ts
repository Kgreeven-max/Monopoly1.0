/**
 * Express application setup
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { config } from './config';
import { errorHandler } from './api/middleware/errorHandler';
import { authRouter } from './api/routes/auth';
import { gamesRouter } from './api/routes/games';
import { playersRouter } from './api/routes/players';
import { adminRouter } from './api/routes/admin';
import { healthRouter } from './api/routes/health';

export const app = express();

// =============================================================================
// MIDDLEWARE
// =============================================================================

// Security headers
app.use(helmet({
  contentSecurityPolicy: false, // Disable for Socket.IO compatibility
}));

// CORS
app.use(cors({
  origin: config.cors.origins,
  credentials: true,
}));

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
if (config.nodeEnv !== 'test') {
  app.use(morgan(config.nodeEnv === 'development' ? 'dev' : 'combined'));
}

// =============================================================================
// ROUTES
// =============================================================================

// Health check (no /api prefix)
app.use('/health', healthRouter);

// API routes
app.use('/api/auth', authRouter);
app.use('/api/games', gamesRouter);
app.use('/api/players', playersRouter);
app.use('/api/admin', adminRouter);

// API info
app.get('/api', (_req, res) => {
  res.json({
    name: 'Pinopoly Game Server',
    version: '2.0.0',
    endpoints: {
      health: '/health',
      auth: '/api/auth',
      games: '/api/games',
      players: '/api/players',
      admin: '/api/admin',
    },
  });
});

// 404 handler
app.use((_req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: 'The requested resource does not exist',
  });
});

// Error handler
app.use(errorHandler);
