# Pinopoly v2

A Jackbox-style Monopoly party game with phone controllers, TV display, and admin console.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TV DISPLAY                            │
│              (Main board view)                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   GAME SERVER                            │
│            (Node.js + Socket.IO)                         │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   PHONE     │      │   ADMIN     │      │   REDIS     │
│ CONTROLLER  │      │  CONSOLE    │      │  (Workers)  │
└─────────────┘      └─────────────┘      └─────────────┘
                                                  │
                                                  ▼
                                          ┌─────────────┐
                                          │ PostgreSQL  │
                                          │  (Master)   │
                                          └─────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm 8+
- Docker & Docker Compose

### Development

```bash
# Install dependencies
pnpm install

# Start development servers
pnpm dev

# Or use Docker
docker compose up --build
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| TV Display | http://localhost:3001 | Main board view |
| Phone Controller | http://localhost:3002 | Player controls |
| Admin Console | http://localhost:3003 | Game management |
| API | http://localhost:3000 | REST + WebSocket |

## Project Structure

```
pinopoly-v2/
├── apps/
│   ├── tv-display/          # React - TV/projector view
│   ├── controller/          # React - Phone controller
│   └── admin-console/       # React - Admin dashboard
├── services/
│   └── game-server/         # Node.js backend
├── packages/
│   ├── shared/              # Shared types & utilities
│   ├── game-engine/         # Pure game logic
│   └── ui-components/       # Shared React components
├── infra/
│   ├── docker/              # Dockerfiles
│   ├── nginx/               # Nginx configs
│   ├── postgres/            # DB init scripts
│   └── migrations/          # Prisma migrations
├── docs/                    # Documentation
└── tests/                   # Test suites
```

## Key Features

- **Jackbox-style gameplay**: Players use phones as controllers
- **Multiple concurrent games**: Room codes for game isolation
- **6 Bot personalities**: Conservative, Aggressive, Strategic, Opportunistic, Shark, Investor
- **Economic cycles**: Recession, Stable, Growth, Boom
- **Financial instruments**: Loans, CDs, HELOC
- **Admin console**: Full game control and debugging

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design
- [Archaeology](docs/ARCHAEOLOGY.md) - Original codebase analysis
- [API](docs/API.md) - Socket events & REST endpoints
- [Database](docs/DB_SCHEMA.md) - Schema design

## Commands

```bash
# Development
pnpm dev              # Start all dev servers
pnpm build            # Build all packages
pnpm test             # Run all tests
pnpm lint             # Lint all packages
pnpm typecheck        # Type check all packages

# Docker
pnpm docker:up        # Start Docker containers
pnpm docker:down      # Stop Docker containers
pnpm docker:build     # Rebuild Docker images
pnpm docker:logs      # View container logs

# Database
pnpm db:migrate       # Run Prisma migrations
pnpm db:generate      # Generate Prisma client
```

## Tech Stack

- **Runtime**: Node.js 20
- **Language**: TypeScript (strict)
- **Package Manager**: pnpm
- **Build System**: Turborepo
- **Backend**: Express + Socket.IO
- **Frontend**: React + Vite
- **Database**: PostgreSQL
- **Cache**: Redis
- **Validation**: Zod
- **Testing**: Vitest + Playwright

## License

Private - All rights reserved
