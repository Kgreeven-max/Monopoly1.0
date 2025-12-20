/**
 * Authentication routes
 */

import { Router, Request, Response } from 'express';
import bcrypt from 'bcryptjs';
import { prisma } from '../../db/client';
import { generateToken } from '../../services/AuthService';
import { createError } from '../middleware/errorHandler';
import { z } from 'zod';

export const authRouter = Router();

// Validation schemas
const registerSchema = z.object({
  username: z.string().min(3).max(50),
  email: z.string().email().optional(),
  password: z.string().min(6),
});

const loginSchema = z.object({
  username: z.string(),
  password: z.string(),
});

// Register new user
authRouter.post('/register', async (req: Request, res: Response, next) => {
  try {
    const data = registerSchema.parse(req.body);

    // Check if username exists
    const existing = await prisma.user.findUnique({
      where: { username: data.username },
    });

    if (existing) {
      throw createError('Username already taken', 400, 'USERNAME_EXISTS');
    }

    // Hash password
    const passwordHash = await bcrypt.hash(data.password, 10);

    // Create user
    const user = await prisma.user.create({
      data: {
        username: data.username,
        email: data.email,
        passwordHash,
      },
      select: {
        id: true,
        username: true,
        email: true,
        createdAt: true,
      },
    });

    // Generate token
    const token = generateToken({
      userId: user.id,
      username: user.username,
    });

    res.status(201).json({
      user,
      token,
    });
  } catch (error) {
    next(error);
  }
});

// Login
authRouter.post('/login', async (req: Request, res: Response, next) => {
  try {
    const data = loginSchema.parse(req.body);

    // Find user
    const user = await prisma.user.findUnique({
      where: { username: data.username },
    });

    if (!user) {
      throw createError('Invalid credentials', 401, 'INVALID_CREDENTIALS');
    }

    // Check password
    const valid = await bcrypt.compare(data.password, user.passwordHash);

    if (!valid) {
      throw createError('Invalid credentials', 401, 'INVALID_CREDENTIALS');
    }

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLogin: new Date() },
    });

    // Generate token
    const token = generateToken({
      userId: user.id,
      username: user.username,
    });

    res.json({
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        totalGamesPlayed: user.totalGamesPlayed,
        totalWins: user.totalWins,
      },
      token,
    });
  } catch (error) {
    next(error);
  }
});

// Guest login (for quick play)
authRouter.post('/guest', async (req: Request, res: Response, next) => {
  try {
    const { name } = req.body;

    if (!name || typeof name !== 'string' || name.length < 2) {
      throw createError('Name is required (min 2 characters)', 400, 'INVALID_NAME');
    }

    // Generate guest token
    const guestId = `guest_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const token = generateToken({
      guestId,
      guestName: name,
      isGuest: true,
    });

    res.json({
      guestId,
      name,
      token,
    });
  } catch (error) {
    next(error);
  }
});
