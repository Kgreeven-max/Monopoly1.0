#!/bin/bash

# ===============================================
# Pinopoly V2 - Development Environment Setup
# ===============================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "msys" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Main setup function
main() {
    log_info "🚀 Setting up Pinopoly V2 development environment..."
    
    # Check system requirements
    check_system_requirements
    
    # Create necessary directories
    create_directories
    
    # Setup environment files
    setup_environment_files
    
    # Setup backend
    setup_backend
    
    # Setup frontend
    setup_frontend
    
    # Setup pre-commit hooks
    setup_pre_commit_hooks
    
    # Setup Docker environment
    setup_docker_environment
    
    # Final verification
    verify_setup
    
    log_success "✅ Setup completed successfully!"
    log_info "🎯 Next steps:"
    echo "   1. Copy .env.example to .env and update values"
    echo "   2. Run 'docker-compose up -d' to start services"
    echo "   3. Visit http://localhost:3000 for the frontend"
    echo "   4. Visit http://localhost:8000/docs for API documentation"
}

# Check system requirements
check_system_requirements() {
    log_info "🔍 Checking system requirements..."
    
    local os=$(detect_os)
    log_info "Operating System: $os"
    
    # Check Python
    if command_exists python3; then
        local python_version=$(python3 --version | cut -d ' ' -f 2)
        log_success "Python: $python_version"
        
        # Check if Python version is >= 3.11
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            log_success "Python version is compatible (>= 3.11)"
        else
            log_error "Python 3.11+ is required. Please update Python."
            exit 1
        fi
    else
        log_error "Python 3 is not installed. Please install Python 3.11+."
        exit 1
    fi
    
    # Check Node.js
    if command_exists node; then
        local node_version=$(node --version)
        log_success "Node.js: $node_version"
        
        # Check if Node version is >= 18
        local node_major=$(node --version | cut -d 'v' -f 2 | cut -d '.' -f 1)
        if [ "$node_major" -ge 18 ]; then
            log_success "Node.js version is compatible (>= 18)"
        else
            log_error "Node.js 18+ is required. Please update Node.js."
            exit 1
        fi
    else
        log_error "Node.js is not installed. Please install Node.js 18+."
        exit 1
    fi
    
    # Check npm
    if command_exists npm; then
        local npm_version=$(npm --version)
        log_success "npm: $npm_version"
    else
        log_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    # Check Docker (optional but recommended)
    if command_exists docker; then
        local docker_version=$(docker --version | cut -d ' ' -f 3 | cut -d ',' -f 1)
        log_success "Docker: $docker_version"
    else
        log_warning "Docker is not installed. Install Docker for the best development experience."
    fi
    
    # Check Docker Compose (optional but recommended)
    if command_exists docker-compose || command_exists docker && docker compose version >/dev/null 2>&1; then
        if command_exists docker-compose; then
            local compose_version=$(docker-compose --version | cut -d ' ' -f 4 | cut -d ',' -f 1)
        else
            local compose_version=$(docker compose version --short)
        fi
        log_success "Docker Compose: $compose_version"
    else
        log_warning "Docker Compose is not installed. Install Docker Compose for the best development experience."
    fi
    
    # Check Git
    if command_exists git; then
        local git_version=$(git --version | cut -d ' ' -f 3)
        log_success "Git: $git_version"
    else
        log_error "Git is not installed. Please install Git."
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log_info "📁 Creating project directories..."
    
    # Backend directories
    mkdir -p backend/{src/{domain/{entities,repositories,services,events,exceptions},application/{use_cases,dto,interfaces,services},infrastructure/{database/{models,repositories},cache,websockets,events,external},presentation/{api/v1/{routers,schemas,dependencies},websockets/{namespaces,events},cli/{commands}}},tests/{unit/{domain,application,infrastructure},integration,e2e},migrations/versions,scripts}
    
    # Frontend directories  
    mkdir -p frontend/{src/{components/{ui,layout,common},pages,features/{game/{components,hooks,services,store,types},players/{components,hooks,services,store,types},properties/{components,hooks,services,store,types},finance/{components,hooks,services,store,types},admin/{components,hooks,services,store,types}},hooks,services/{api,websocket,storage},store/{slices,stores},types,utils,styles/{themes},assets/{images,icons,fonts,sounds}},tests/{setup,utils,unit/{components,hooks,services,utils},integration/{features,api},e2e/{specs,fixtures}},public/assets}
    
    # Documentation directories
    mkdir -p docs/{design,guides,examples/{use_cases,components,api_usage,deployment}}
    
    # Scripts directory
    mkdir -p scripts
    
    # Monitoring directories
    mkdir -p monitoring/{prometheus,grafana/{provisioning,dashboards},logs,alerts}
    
    # Deployment directories
    mkdir -p deployment/{docker,kubernetes/{namespace,backend,frontend,database,ingress},terraform/{modules},ci-cd/{.github/workflows,gitlab-ci,jenkins}}
    
    # Tools directories
    mkdir -p tools/{code-generators,database-tools,testing-tools,deployment-tools}
    
    # Config directory
    mkdir -p .config
    
    log_success "Directories created successfully"
}

# Setup environment files
setup_environment_files() {
    log_info "🔧 Setting up environment files..."
    
    # Copy main environment file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Created .env from .env.example"
            log_warning "Please update .env with your local configuration"
        else
            log_warning ".env.example not found, skipping .env creation"
        fi
    else
        log_info ".env already exists, skipping"
    fi
    
    # Create backend environment file
    if [ ! -f backend/.env ]; then
        cat > backend/.env << EOF
# Backend Environment Variables
DATABASE_URL=postgresql://pinopoly_user:pinopoly_pass@localhost:5432/pinopoly_dev
REDIS_URL=redis://localhost:6379
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production
FLASK_ENV=development
FLASK_DEBUG=1
PYTHONPATH=/app/src
LOG_LEVEL=INFO
EOF
        log_success "Created backend/.env"
    else
        log_info "backend/.env already exists, skipping"
    fi
    
    # Create frontend environment file
    if [ ! -f frontend/.env ]; then
        cat > frontend/.env << EOF
# Frontend Environment Variables
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
VITE_APP_NAME=Pinopoly V2
VITE_ENABLE_DEV_TOOLS=true
EOF
        log_success "Created frontend/.env"
    else
        log_info "frontend/.env already exists, skipping"
    fi
}

# Setup backend
setup_backend() {
    log_info "🐍 Setting up Python backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Create requirements.txt if it doesn't exist
    if [ ! -f requirements.txt ]; then
        cat > requirements.txt << EOF
# Core Framework
Flask>=2.3,<3.0
Flask-SQLAlchemy>=3.0.0
Flask-Migrate>=4.0.0
Flask-CORS>=4.0.0

# Database
SQLAlchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0

# Real-time Communication
Flask-SocketIO>=5.3.0
python-socketio>=5.10.0
eventlet>=0.33.0

# Caching & Session Management
redis>=5.0.0
Flask-Session>=0.5.0

# Authentication & Security
PyJWT>=2.8.0
bcrypt>=4.0.0
cryptography>=41.0.0

# API Documentation
flask-restx>=1.2.0
flasgger>=0.9.7

# Data Validation
pydantic>=2.0.0
marshmallow>=3.20.0

# HTTP Requests
requests>=2.31.0
httpx>=0.25.0

# Configuration Management
python-decouple>=3.8.0
dynaconf>=3.2.0

# Utilities
python-dateutil>=2.8.0
pytz>=2023.3
click>=8.1.0

# Monitoring & Logging
prometheus-client>=0.17.0
structlog>=23.0.0

# Development Dependencies (move to requirements-dev.txt in production)
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
mypy>=1.5.0
flake8>=6.0.0
bandit>=1.7.0
pre-commit>=3.4.0
EOF
        log_success "Created requirements.txt"
    fi
    
    # Create development requirements
    if [ ! -f requirements-dev.txt ]; then
        cat > requirements-dev.txt << EOF
# Include production requirements
-r requirements.txt

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-asyncio>=0.21.0
pytest-xdist>=3.3.0
pytest-sugar>=0.9.7
pytest-clarity>=1.0.1
coverage>=7.3.0
factory-boy>=3.3.0
faker>=19.0.0

# Code Quality
black>=23.0.0
isort>=5.12.0
mypy>=1.5.0
flake8>=6.0.0
flake8-docstrings>=1.7.0
flake8-import-order>=0.18.0
bandit>=1.7.0
safety>=2.3.0

# Development Tools
pre-commit>=3.4.0
python-dotenv>=1.0.0
ipython>=8.15.0
ipdb>=0.13.0
watchdog>=3.0.0

# Documentation
sphinx>=7.2.0
sphinx-rtd-theme>=1.3.0
sphinx-autodoc-typehints>=1.24.0

# Profiling & Performance
py-spy>=0.3.0
memory-profiler>=0.61.0
line-profiler>=4.1.0
EOF
        log_success "Created requirements-dev.txt"
    fi
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements-dev.txt
    
    # Create basic Python package structure
    create_backend_package_structure
    
    cd ..
    log_success "Backend setup completed"
}

# Create backend package structure
create_backend_package_structure() {
    log_info "Creating backend package structure..."
    
    # Create __init__.py files
    find src -type d -exec touch {}/__init__.py \;
    
    # Create main application entry point
    if [ ! -f src/main.py ]; then
        cat > src/main.py << EOF
"""
Pinopoly V2 - Main Application Entry Point
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from config.settings import get_settings
from infrastructure.database.session import init_db
from presentation.api.v1.routers import init_routes
from presentation.websockets.events import init_websocket_events


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    settings = get_settings()
    app.config.update(settings.dict())
    
    # Initialize extensions
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize database
    init_db(app)
    
    # Initialize routes
    init_routes(app)
    
    # Initialize WebSocket events
    init_websocket_events(socketio)
    
    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(
        app,
        host="0.0.0.0",
        port=8000,
        debug=True
    )
EOF
        log_success "Created src/main.py"
    fi
    
    # Create basic configuration
    if [ ! -f src/config/settings.py ]; then
        cat > src/config/settings.py << EOF
"""
Application configuration settings.
"""

import os
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Pinopoly V2"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://pinopoly_user:pinopoly_pass@localhost:5432/pinopoly_dev"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_secret: str = "dev-jwt-secret-change-in-production"
    
    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
EOF
        log_success "Created configuration files"
    fi
}

# Setup frontend
setup_frontend() {
    log_info "⚛️ Setting up React frontend..."
    
    cd frontend
    
    # Create package.json if it doesn't exist
    if [ ! -f package.json ]; then
        cat > package.json << EOF
{
  "name": "pinopoly-v2-frontend",
  "version": "2.0.0",
  "type": "module",
  "description": "Pinopoly V2 React TypeScript Frontend",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "type-check": "tsc --noEmit",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css,md}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx,json,css,md}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.16.0",
    "socket.io-client": "^4.7.0",
    "zustand": "^4.4.0",
    "framer-motion": "^10.16.0",
    "tailwindcss": "^3.3.0",
    "@headlessui/react": "^1.7.0",
    "@heroicons/react": "^2.0.0",
    "clsx": "^2.0.0",
    "date-fns": "^2.30.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "typescript": "^5.0.0",
    "vite": "^4.4.0",
    "vitest": "^0.34.0",
    "@vitest/coverage-v8": "^0.34.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.0.0",
    "jsdom": "^22.1.0",
    "prettier": "^3.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@playwright/test": "^1.37.0"
  }
}
EOF
        log_success "Created package.json"
    fi
    
    # Install dependencies
    log_info "Installing Node.js dependencies..."
    npm install
    
    # Create basic TypeScript configuration
    if [ ! -f tsconfig.json ]; then
        cat > tsconfig.json << EOF
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    
    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    
    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    
    /* Path mapping */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/pages/*": ["./src/pages/*"],
      "@/features/*": ["./src/features/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/services/*": ["./src/services/*"],
      "@/store/*": ["./src/store/*"],
      "@/types/*": ["./src/types/*"],
      "@/utils/*": ["./src/utils/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
        log_success "Created TypeScript configuration"
    fi
    
    # Create Vite configuration
    if [ ! -f vite.config.ts ]; then
        cat > vite.config.ts << EOF
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
EOF
        log_success "Created Vite configuration"
    fi
    
    cd ..
    log_success "Frontend setup completed"
}

# Setup pre-commit hooks
setup_pre_commit_hooks() {
    log_info "🪝 Setting up pre-commit hooks..."
    
    if [ ! -f .pre-commit-config.yaml ]; then
        cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: check-toml
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        files: ^backend/
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        files: ^backend/
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        files: ^backend/
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.47.0
    hooks:
      - id: eslint
        files: ^frontend/.*\.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@8.47.0
          - '@typescript-eslint/parser@6.0.0'
          - '@typescript-eslint/eslint-plugin@6.0.0'

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: ^frontend/.*\.(js|jsx|ts|tsx|json|css|md)$
EOF
        log_success "Created pre-commit configuration"
    fi
    
    # Install pre-commit if not in CI
    if [ -z "$CI" ] && command_exists pre-commit; then
        log_info "Installing pre-commit hooks..."
        pre-commit install
        log_success "Pre-commit hooks installed"
    else
        log_warning "Pre-commit not available or in CI environment, skipping hook installation"
    fi
}

# Setup Docker environment
setup_docker_environment() {
    log_info "🐳 Setting up Docker environment..."
    
    # Create backend Dockerfile
    if [ ! -f backend/Dockerfile ]; then
        cat > backend/Dockerfile << EOF
# Multi-stage Dockerfile for Python Flask backend

# Development stage
FROM python:3.11-slim as development

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv venv
ENV PATH="/app/venv/bin:\$PATH"

# Copy requirements and install dependencies
COPY requirements-dev.txt .
RUN pip install --upgrade pip && \\
    pip install -r requirements-dev.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "src/main.py"]

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create virtual environment
RUN python -m venv venv
ENV PATH="/app/venv/bin:\$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \\
    pip install -r requirements.txt

# Copy source code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "src.main:app"]
EOF
        log_success "Created backend/Dockerfile"
    fi
    
    # Create frontend Dockerfile
    if [ ! -f frontend/Dockerfile ]; then
        cat > frontend/Dockerfile << EOF
# Multi-stage Dockerfile for React frontend

# Development stage
FROM node:18-alpine as development

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Development command
CMD ["npm", "run", "dev"]

# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine as production

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=build /app/dist /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF
        log_success "Created frontend/Dockerfile"
    fi
    
    # Create nginx configuration for frontend
    if [ ! -f frontend/nginx.conf ]; then
        cat > frontend/nginx.conf << EOF
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Handle client-side routing
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API proxy (optional, for production without separate API domain)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate no-transform;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
}
EOF
        log_success "Created nginx configuration"
    fi
}

# Verify setup
verify_setup() {
    log_info "🔍 Verifying setup..."
    
    local errors=0
    
    # Check backend setup
    if [ -d "backend/venv" ] && [ -f "backend/requirements-dev.txt" ]; then
        log_success "Backend environment configured"
    else
        log_error "Backend environment not properly configured"
        errors=$((errors + 1))
    fi
    
    # Check frontend setup
    if [ -f "frontend/package.json" ] && [ -d "frontend/node_modules" ]; then
        log_success "Frontend environment configured"
    else
        log_error "Frontend environment not properly configured"
        errors=$((errors + 1))
    fi
    
    # Check Docker files
    if [ -f "docker-compose.yml" ] && [ -f "backend/Dockerfile" ] && [ -f "frontend/Dockerfile" ]; then
        log_success "Docker configuration present"
    else
        log_error "Docker configuration incomplete"
        errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "All verifications passed"
    else
        log_error "$errors verification(s) failed"
        exit 1
    fi
}

# Run main function
main "$@"