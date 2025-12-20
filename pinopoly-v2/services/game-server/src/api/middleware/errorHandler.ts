/**
 * Error handling middleware
 */

import { Request, Response, NextFunction } from 'express';
import { config } from '../../config';

export interface AppError extends Error {
  statusCode?: number;
  code?: string;
}

export function errorHandler(
  err: AppError,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';
  const code = err.code || 'INTERNAL_ERROR';

  // Log error
  console.error(`[${code}] ${message}`, config.nodeEnv === 'development' ? err.stack : '');

  res.status(statusCode).json({
    error: {
      code,
      message,
      ...(config.nodeEnv === 'development' && { stack: err.stack }),
    },
  });
}

export function createError(message: string, statusCode: number, code?: string): AppError {
  const error = new Error(message) as AppError;
  error.statusCode = statusCode;
  error.code = code;
  return error;
}
