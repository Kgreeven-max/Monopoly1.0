/**
 * Server configuration
 */

export const config = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3000', 10),

  database: {
    url: process.env.DATABASE_URL || 'postgresql://pinopoly:pinopoly_dev@localhost:5432/pinopoly_master',
  },

  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379',
    host: new URL(process.env.REDIS_URL || 'redis://localhost:6379').hostname,
    port: parseInt(new URL(process.env.REDIS_URL || 'redis://localhost:6379').port || '6379', 10),
  },

  jwt: {
    secret: process.env.JWT_SECRET || 'dev-jwt-secret-change-in-production',
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  },

  admin: {
    token: process.env.ADMIN_TOKEN || 'admin-dev-token',
  },

  game: {
    maxConcurrentGames: parseInt(process.env.MAX_CONCURRENT_GAMES || '10', 10),
    maxPlayersPerGame: parseInt(process.env.MAX_PLAYERS_PER_GAME || '8', 10),
    botThinkDelayMs: parseInt(process.env.BOT_THINK_DELAY_MS || '1500', 10),
  },

  cors: {
    origins: (process.env.CORS_ORIGINS || 'http://localhost:3001,http://localhost:3002,http://localhost:3003').split(','),
  },

  features: {
    economicCycles: process.env.ENABLE_ECONOMIC_CYCLES !== 'false',
    financialInstruments: process.env.ENABLE_FINANCIAL_INSTRUMENTS !== 'false',
    crimeSystem: process.env.ENABLE_CRIME_SYSTEM === 'true',
  },

  logging: {
    level: process.env.LOG_LEVEL || 'debug',
  },
} as const;

export type Config = typeof config;
