# 🎲 Pinopoly V2 - Modern Monopoly Game

A completely rebuilt, modern implementation of the classic Monopoly board game using Clean Architecture, Domain-Driven Design, and cutting-edge web technologies.

## 🌟 Features

### 🎮 Core Game Mechanics
- **Classic Monopoly Rules**: Buy, sell, develop properties, collect rent
- **Real-time Multiplayer**: Up to 8 players with live WebSocket communication
- **AI Bot Players**: 6 different bot personalities with adaptive difficulty
- **Advanced Financial System**: Loans, CDs, HELOCs, bankruptcy protection
- **Economic Cycles**: Dynamic market conditions affecting property values
- **Auction System**: Property auctions with real-time bidding
- **Crime & Justice**: Crime system with police patrols and consequences

### 🏗️ Technical Highlights
- **Clean Architecture**: Proper separation of concerns
- **Domain-Driven Design**: Business logic at the core
- **Type Safety**: Full TypeScript frontend, Python type hints
- **Real-time Updates**: Socket.IO for instant game state synchronization
- **Responsive Design**: Mobile-first, works on all devices
- **Performance Optimized**: Lazy loading, code splitting, caching
- **Comprehensive Testing**: Unit, integration, and E2E tests
- **DevOps Ready**: Docker, CI/CD, monitoring, logging

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **PostgreSQL** (or use Docker)
- **Redis** (or use Docker)

### Development Setup

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd pinopoly-v2
chmod +x scripts/*.sh
./scripts/setup.sh
```

2. **Start the development environment:**
```bash
docker-compose up -d
```

3. **Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:3000/admin

### Manual Setup (without Docker)

1. **Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head
python scripts/seed_database.py
python src/main.py
```

2. **Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────┐
│              Presentation Layer              │
│         (API, WebSockets, React UI)         │
├─────────────────────────────────────────────┤
│             Infrastructure Layer            │
│      (Database, Cache, External APIs)      │
├─────────────────────────────────────────────┤
│             Application Layer               │
│           (Use Cases, DTOs)                │
├─────────────────────────────────────────────┤
│              Domain Layer                   │
│     (Entities, Services, Business Rules)   │
└─────────────────────────────────────────────┘
```

### Technology Stack

#### Backend
- **Framework**: Flask 2.3+ with Clean Architecture
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Real-time**: Socket.IO with Redis adapter
- **Cache**: Redis for sessions and game state
- **Validation**: Pydantic for data validation
- **Testing**: pytest with 90%+ coverage
- **Code Quality**: Black, isort, mypy, flake8

#### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development
- **State Management**: Zustand for global state
- **Styling**: Tailwind CSS with CSS modules
- **Animations**: Framer Motion for smooth transitions
- **Testing**: Vitest + Testing Library + Playwright
- **Code Quality**: ESLint, Prettier, TypeScript strict mode

#### DevOps
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: Alembic
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured logging with correlation IDs

## 📁 Project Structure

```
pinopoly-v2/
├── backend/                    # Python Flask Clean Architecture
│   ├── src/
│   │   ├── domain/            # Business entities and rules
│   │   ├── application/       # Use cases and DTOs
│   │   ├── infrastructure/    # Database, cache, external services
│   │   └── presentation/      # API endpoints and WebSocket handlers
│   ├── tests/                 # Comprehensive test suite
│   └── migrations/            # Database migrations
├── frontend/                  # React TypeScript SPA
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── features/          # Feature-based modules
│   │   ├── pages/             # Route-based pages
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API and WebSocket services
│   │   └── store/             # State management
│   └── tests/                 # Frontend tests
├── docs/                      # Comprehensive documentation
├── scripts/                   # Development and deployment scripts
└── deployment/                # Docker, Kubernetes, CI/CD configs
```

## 🎯 Game Features

### 🎲 Core Gameplay
- **Turn-based Movement**: Roll dice, move around the board
- **Property Management**: Buy, develop, mortgage properties
- **Rent Collection**: Automatic rent calculation and collection
- **Special Spaces**: Chance, Community Chest, Tax, Jail
- **Bankruptcy Protection**: Advanced financial management
- **Trading System**: Player-to-player property and money trades

### 🤖 AI Bot System
- **Conservative Bot**: Safe investments, high cash reserves
- **Aggressive Bot**: High-risk, rapid expansion strategy
- **Strategic Bot**: Focuses on monopolies and strategic development
- **Opportunistic Bot**: Market timing and quick profits
- **Shark Bot**: Aggressive trading and property acquisition
- **Investor Bot**: Long-term investment strategy

### 💰 Financial System
- **Banking**: Loans with variable interest rates
- **Investments**: Certificates of Deposit (CDs) with maturation
- **Credit System**: HELOC (Home Equity Line of Credit)
- **Market Dynamics**: Economic cycles affecting all transactions
- **Bankruptcy**: Comprehensive debt restructuring system

### 📊 Admin Features
- **Game Management**: Start, pause, end games
- **Player Administration**: Add/remove players, manage bots
- **Economic Controls**: Trigger market events, adjust cycles
- **Property Management**: Modify property values and rules
- **Analytics Dashboard**: Game statistics and player metrics

## 🧪 Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest                          # All tests
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests
pytest --cov=src tests/         # With coverage

# Frontend tests
cd frontend
npm test                        # Unit tests
npm run test:e2e               # End-to-end tests
npm run test:coverage          # With coverage

# All tests
./scripts/test.sh              # Run everything
```

### Test Strategy
- **Unit Tests**: Domain entities, services, components
- **Integration Tests**: API endpoints, database operations
- **E2E Tests**: Complete user workflows
- **Performance Tests**: Load testing for multiplayer scenarios
- **Security Tests**: Authentication, authorization, input validation

## 🚀 Deployment

### Development
```bash
docker-compose up -d           # Start all services
```

### Production
```bash
./scripts/build.sh             # Build all components
./scripts/deploy.sh production # Deploy to production
```

### Environment Variables

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/pinopoly
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
```

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and patterns
- **[API Reference](docs/API_REFERENCE.md)**: Complete API documentation
- **[Development Guide](docs/DEVELOPMENT.md)**: Setup and workflow
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production deployment
- **[Testing Guide](docs/TESTING.md)**: Testing strategies and tools
- **[Game Mechanics](docs/design/GAME_MECHANICS.md)**: Rules and gameplay

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow the coding standards** (see CLAUDE.md)
4. **Write tests** for new functionality
5. **Commit changes**: `git commit -m 'feat: add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Monopoly** by Hasbro for inspiration
- **Clean Architecture** by Robert C. Martin
- **Domain-Driven Design** by Eric Evans
- **React Community** for excellent tools and patterns
- **Python Community** for robust backend technologies

## 📞 Support

- **Documentation**: Check the [docs](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/username/pinopoly-v2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/pinopoly-v2/discussions)
- **Email**: support@pinopoly.com

---

**Built with ❤️ using modern web technologies and best practices.**