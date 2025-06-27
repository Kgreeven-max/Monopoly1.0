#!/bin/bash

# Docker Environment Validation Script for Pinopoly V2
# This script validates that Docker setup is correct and working

set -e

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

# Validate Docker installation
validate_docker_installation() {
    log_info "Validating Docker installation..."
    
    if ! command_exists docker; then
        log_error "Docker is not installed or not in PATH"
        log_info "Install Docker from: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    # Check Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        log_info "Start Docker Desktop or run: sudo systemctl start docker"
        return 1
    fi
    
    local docker_version=$(docker --version | cut -d ' ' -f 3 | cut -d ',' -f 1)
    log_success "Docker version: $docker_version"
    
    # Check Docker Compose
    if command_exists docker-compose; then
        local compose_version=$(docker-compose --version | cut -d ' ' -f 4 | cut -d ',' -f 1)
        log_success "Docker Compose version: $compose_version"
    elif docker compose version >/dev/null 2>&1; then
        local compose_version=$(docker compose version --short)
        log_success "Docker Compose (plugin) version: $compose_version"
    else
        log_error "Docker Compose is not available"
        return 1
    fi
    
    return 0
}

# Validate Dockerfile syntax
validate_dockerfiles() {
    log_info "Validating Dockerfile syntax..."
    
    local dockerfiles=("backend/Dockerfile" "frontend/Dockerfile")
    local all_valid=true
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [ -f "$dockerfile" ]; then
            # Check Dockerfile syntax using docker build --dry-run equivalent
            if docker build -f "$dockerfile" --no-cache --pull -t validate-syntax . >/dev/null 2>&1; then
                log_success "Dockerfile syntax valid: $dockerfile"
                # Clean up test image
                docker rmi validate-syntax >/dev/null 2>&1 || true
            else
                log_error "Dockerfile syntax error: $dockerfile"
                all_valid=false
            fi
        else
            log_warning "Dockerfile not found: $dockerfile"
            all_valid=false
        fi
    done
    
    return $all_valid
}

# Validate docker-compose.yml
validate_docker_compose() {
    log_info "Validating docker-compose.yml..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found"
        return 1
    fi
    
    # Validate syntax
    if docker-compose config >/dev/null 2>&1 || docker compose config >/dev/null 2>&1; then
        log_success "docker-compose.yml syntax is valid"
    else
        log_error "docker-compose.yml has syntax errors"
        return 1
    fi
    
    # Check required services
    local required_services=("backend" "frontend" "database" "redis")
    local compose_services
    
    if command_exists docker-compose; then
        compose_services=$(docker-compose config --services 2>/dev/null || echo "")
    else
        compose_services=$(docker compose config --services 2>/dev/null || echo "")
    fi
    
    for service in "${required_services[@]}"; do
        if echo "$compose_services" | grep -q "^$service$"; then
            log_success "Service defined: $service"
        else
            log_warning "Service not defined: $service"
        fi
    done
    
    return 0
}

# Test Docker build process
test_docker_build() {
    log_info "Testing Docker build process..."
    
    # Build backend
    if [ -f "backend/Dockerfile" ]; then
        log_info "Building backend image..."
        if docker build -t pinopoly-v2-backend-test backend/ >/dev/null 2>&1; then
            log_success "Backend image built successfully"
            # Clean up
            docker rmi pinopoly-v2-backend-test >/dev/null 2>&1 || true
        else
            log_error "Backend image build failed"
            return 1
        fi
    fi
    
    # Build frontend
    if [ -f "frontend/Dockerfile" ]; then
        log_info "Building frontend image..."
        if docker build -t pinopoly-v2-frontend-test frontend/ >/dev/null 2>&1; then
            log_success "Frontend image built successfully"
            # Clean up
            docker rmi pinopoly-v2-frontend-test >/dev/null 2>&1 || true
        else
            log_error "Frontend image build failed"
            return 1
        fi
    fi
    
    return 0
}

# Test docker-compose functionality
test_docker_compose() {
    log_info "Testing docker-compose functionality..."
    
    # Check if services are already running
    local running_services
    if command_exists docker-compose; then
        running_services=$(docker-compose ps --services --filter status=running 2>/dev/null || echo "")
    else
        running_services=$(docker compose ps --services --filter status=running 2>/dev/null || echo "")
    fi
    
    if [ -n "$running_services" ]; then
        log_warning "Some services are already running:"
        echo "$running_services"
        log_info "Stopping services for clean test..."
        
        if command_exists docker-compose; then
            docker-compose down >/dev/null 2>&1 || true
        else
            docker compose down >/dev/null 2>&1 || true
        fi
    fi
    
    # Test docker-compose up in detached mode
    log_info "Starting services with docker-compose..."
    
    if command_exists docker-compose; then
        docker-compose up -d >/dev/null 2>&1
        sleep 10  # Wait for services to start
        
        # Check service status
        local healthy_services=$(docker-compose ps --services --filter status=running 2>/dev/null || echo "")
        if [ -n "$healthy_services" ]; then
            log_success "Services started successfully:"
            echo "$healthy_services"
        else
            log_error "No services are running"
            docker-compose logs
            return 1
        fi
        
        # Clean up
        log_info "Cleaning up test environment..."
        docker-compose down >/dev/null 2>&1
    else
        docker compose up -d >/dev/null 2>&1
        sleep 10  # Wait for services to start
        
        # Check service status
        local healthy_services=$(docker compose ps --services --filter status=running 2>/dev/null || echo "")
        if [ -n "$healthy_services" ]; then
            log_success "Services started successfully:"
            echo "$healthy_services"
        else
            log_error "No services are running"
            docker compose logs
            return 1
        fi
        
        # Clean up
        log_info "Cleaning up test environment..."
        docker compose down >/dev/null 2>&1
    fi
    
    return 0
}

# Check networking configuration
validate_networking() {
    log_info "Validating Docker networking..."
    
    # Check if custom networks are defined
    local networks
    if command_exists docker-compose; then
        networks=$(docker-compose config | grep -A 10 "networks:" | grep -v "networks:" | grep ":" | cut -d ':' -f 1 | xargs 2>/dev/null || echo "")
    else
        networks=$(docker compose config | grep -A 10 "networks:" | grep -v "networks:" | grep ":" | cut -d ':' -f 1 | xargs 2>/dev/null || echo "")
    fi
    
    if [ -n "$networks" ]; then
        log_success "Custom networks defined: $networks"
    else
        log_info "Using default Docker network"
    fi
    
    return 0
}

# Check volume configuration
validate_volumes() {
    log_info "Validating Docker volumes..."
    
    # Check if volumes are defined
    local volumes
    if command_exists docker-compose; then
        volumes=$(docker-compose config | grep -A 10 "volumes:" | grep -v "volumes:" | grep ":" | cut -d ':' -f 1 | xargs 2>/dev/null || echo "")
    else
        volumes=$(docker compose config | grep -A 10 "volumes:" | grep -v "volumes:" | grep ":" | cut -d ':' -f 1 | xargs 2>/dev/null || echo "")
    fi
    
    if [ -n "$volumes" ]; then
        log_success "Named volumes defined: $volumes"
    else
        log_info "No named volumes defined"
    fi
    
    # Check for bind mounts in development
    local bind_mounts
    if command_exists docker-compose; then
        bind_mounts=$(docker-compose config | grep -E "^\s+- \./" | wc -l)
    else
        bind_mounts=$(docker compose config | grep -E "^\s+- \./" | wc -l)
    fi
    
    if [ "$bind_mounts" -gt 0 ]; then
        log_success "Bind mounts configured for development"
    else
        log_warning "No bind mounts found - code changes may not be reflected"
    fi
    
    return 0
}

# Main validation function
main() {
    log_info "🐳 Starting Docker environment validation..."
    echo
    
    local all_passed=true
    
    # Run all validations
    if ! validate_docker_installation; then
        all_passed=false
    fi
    echo
    
    if ! validate_dockerfiles; then
        all_passed=false
    fi
    echo
    
    if ! validate_docker_compose; then
        all_passed=false
    fi
    echo
    
    if ! validate_networking; then
        all_passed=false
    fi
    echo
    
    if ! validate_volumes; then
        all_passed=false
    fi
    echo
    
    if ! test_docker_build; then
        all_passed=false
    fi
    echo
    
    if ! test_docker_compose; then
        all_passed=false
    fi
    echo
    
    # Print summary
    echo "=" * 50
    echo "DOCKER VALIDATION SUMMARY"
    echo "=" * 50
    
    if $all_passed; then
        log_success "All Docker validations passed! ✨"
        log_info "Your Docker environment is ready for development."
        echo
        log_info "Next steps:"
        log_info "1. Run: docker-compose up -d"
        log_info "2. Check services: docker-compose ps"
        log_info "3. View logs: docker-compose logs -f"
        log_info "4. Stop services: docker-compose down"
    else
        log_error "Some Docker validations failed"
        log_info "Please fix the issues above before proceeding."
    fi
    
    return $all_passed
}

# Check if script is run from project root
if [ ! -f "docker-compose.yml" ] && [ ! -f "ACTUAL_IMPLEMENTATION_PLAN.md" ]; then
    log_error "Please run this script from the project root directory"
    log_info "The script should find docker-compose.yml in the current directory"
    exit 1
fi

# Run main function
if main; then
    exit 0
else
    exit 1
fi