# CLAUDE.md - Pinopoly V2 Development Rules

## Project Overview
Pinopoly V2 is a modern, scalable Monopoly-like game built with Clean Architecture, Domain-Driven Design, and modern web technologies.

## Architecture Principles
- **Clean Architecture**: Strict separation of concerns with Domain, Application, Infrastructure, and Presentation layers
- **Domain-Driven Design**: Business logic centralized in domain entities and services
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Event-Driven Architecture**: Loose coupling through domain events
- **API-First Design**: REST APIs with OpenAPI documentation

## Development Commands

### Backend (Python/Flask)
```bash
# Setup backend environment
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt

# Database operations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m ""   # Create migration
python scripts/seed_database.py         # Seed with test data

# Testing
pytest                                  # Run all tests
pytest tests/unit/                      # Run unit tests
pytest tests/integration/              # Run integration tests
pytest --cov=src tests/                # Run with coverage

# Code quality
black src/ tests/                       # Format code
isort src/ tests/                       # Sort imports
mypy src/                              # Type checking
flake8 src/ tests/                     # Linting

# Development server
python src/main.py                     # Start development server
```

### Frontend (React/TypeScript)
```bash
# Setup frontend
cd frontend && npm install

# Development
npm run dev                            # Start development server
npm run build                          # Build for production
npm run preview                        # Preview production build

# Testing
npm test                              # Run unit tests
npm run test:watch                    # Run tests in watch mode
npm run test:coverage                 # Run with coverage
npm run test:e2e                     # Run end-to-end tests

# Code quality
npm run lint                          # ESLint
npm run lint:fix                      # Fix linting issues
npm run type-check                    # TypeScript checking
npm run format                        # Prettier formatting
```

### Full Stack Operations
```bash
# Start entire development environment
docker-compose up -d                  # Start all services
./scripts/start-dev.sh                # Alternative startup script

# Testing
./scripts/test.sh                     # Run all tests (backend + frontend)

# Deployment
./scripts/build.sh                    # Build all components
./scripts/deploy.sh                   # Deploy to staging/production
```

## Code Style & Standards

### Backend (Python)
- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- **mypy** for type checking (strict mode)
- **flake8** for linting
- **pytest** for testing with 90%+ coverage
- **Pydantic** for data validation
- **SQLAlchemy 2.0** with async support

### Frontend (TypeScript)
- **TypeScript strict mode** enabled
- **ESLint** with React hooks rules
- **Prettier** for formatting
- **Vitest** for unit testing
- **Testing Library** for component testing
- **Playwright** for E2E testing

### Git Workflow
- **Feature branches**: `feature/JIRA-123-add-property-management`
- **Conventional commits**: `feat(player): add player movement animation`
- **Pull request reviews** required
- **Pre-commit hooks** for code quality
- **Semantic versioning**

## Architecture Layers

### Domain Layer (Core Business Logic)
- **Entities**: Core business objects (Player, Property, Game)
- **Value Objects**: Immutable objects (Money, Position, GameState)
- **Domain Services**: Complex business logic that doesn't belong to entities
- **Repository Interfaces**: Abstract data access contracts
- **Domain Events**: Business event notifications

### Application Layer (Use Cases)
- **Use Cases**: Application-specific business rules
- **DTOs**: Data transfer objects for API communication
- **Application Services**: Orchestration of domain services
- **Command/Query Handlers**: CQRS pattern implementation

### Infrastructure Layer (External Concerns)
- **Database**: SQLAlchemy models and repository implementations
- **WebSockets**: Socket.IO real-time communication
- **Cache**: Redis for session and game state caching
- **External APIs**: Third-party service integrations

### Presentation Layer (User Interface)
- **REST API**: Flask/FastAPI endpoints with OpenAPI docs
- **WebSocket API**: Real-time event handling
- **Web UI**: React TypeScript SPA

## Key Design Patterns

### Backend Patterns
- **Repository Pattern**: Data access abstraction
- **Unit of Work**: Transaction management
- **Command Pattern**: User action handling
- **Observer Pattern**: Event-driven communication
- **Factory Pattern**: Object creation
- **Strategy Pattern**: Algorithm variations (bot AI)

### Frontend Patterns
- **Container/Presenter**: Logic separation
- **Custom Hooks**: Reusable state logic
- **Compound Components**: Flexible component APIs
- **Provider Pattern**: Context-based state sharing
- **Higher-Order Components**: Cross-cutting concerns

## Security Guidelines
- **Input Validation**: All user inputs validated with Pydantic/Zod
- **SQL Injection Prevention**: Use ORM query builders
- **XSS Prevention**: Sanitize all user-generated content
- **CSRF Protection**: CSRF tokens for state-changing operations
- **Authentication**: JWT tokens with proper expiration
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: API endpoint protection
- **HTTPS Only**: All communication encrypted

## Performance Guidelines
- **Database**: Use connection pooling, query optimization, proper indexing
- **Caching**: Redis for frequently accessed data
- **Frontend**: Code splitting, lazy loading, image optimization
- **WebSockets**: Connection pooling, event batching
- **Monitoring**: Application performance monitoring (APM)

## Testing Strategy
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows
- **Performance Tests**: Load testing with realistic scenarios
- **Security Tests**: Penetration testing and vulnerability scanning

## Deployment & DevOps
- **Containerization**: Docker for all services
- **Orchestration**: Kubernetes for production
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Infrastructure as Code**: Terraform for cloud resources
- **Monitoring**: Prometheus + Grafana for observability
- **Logging**: Centralized logging with ELK stack

## Development Workflow
1. **Create feature branch** from main
2. **Implement feature** following TDD
3. **Write tests** with good coverage
4. **Update documentation** as needed
5. **Run quality checks** (lint, type-check, test)
6. **Create pull request** with detailed description
7. **Code review** by team members
8. **Merge after approval** and CI passes

## Error Handling
- **Domain Exceptions**: Business rule violations
- **Application Exceptions**: Use case failures
- **Infrastructure Exceptions**: External service failures
- **Presentation Exceptions**: API/UI error responses
- **Centralized Logging**: All errors logged with context
- **User-Friendly Messages**: Clear error messages for users

## Monitoring & Observability
- **Application Metrics**: Response times, error rates, throughput
- **Business Metrics**: Game completion rates, user engagement
- **Infrastructure Metrics**: CPU, memory, disk, network usage
- **Log Aggregation**: Centralized logging for debugging
- **Alerting**: Real-time alerts for critical issues
- **Distributed Tracing**: Request tracing across services

## Common Commands Quick Reference
```bash
# Start development environment
docker-compose up -d

# Run backend tests
cd backend && pytest

# Run frontend tests  
cd frontend && npm test

# Format all code
./scripts/format.sh

# Run all quality checks
./scripts/lint.sh

# Deploy to staging
./scripts/deploy.sh staging

# Generate API documentation
cd backend && python scripts/generate_api_docs.py

# Database migration
cd backend && alembic upgrade head
```

## Important Notes
- **Always run tests** before committing
- **Update documentation** when changing APIs
- **Follow semantic versioning** for releases
- **Use feature flags** for experimental features
- **Monitor performance** after deployments
- **Keep dependencies updated** regularly
- **Security first** - validate all inputs
- **Mobile responsive** design required