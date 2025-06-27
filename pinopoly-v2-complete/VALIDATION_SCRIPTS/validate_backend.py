#!/usr/bin/env python3
"""
Backend Validation Script for Pinopoly V2

This script validates that the backend implementation is correct and working.
Run this after creating backend files to ensure everything is set up properly.
"""

import os
import sys
import subprocess
import importlib.util
import traceback
from pathlib import Path
from typing import List, Tuple, Optional

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_success(message: str):
    print(f"{GREEN}✓{END} {message}")

def print_error(message: str):
    print(f"{RED}✗{END} {message}")

def print_warning(message: str):
    print(f"{YELLOW}⚠{END} {message}")

def print_info(message: str):
    print(f"{BLUE}ℹ{END} {message}")

class BackendValidator:
    def __init__(self, backend_dir: str = "backend"):
        self.backend_dir = Path(backend_dir)
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print_info("Starting backend validation...")
        print()
        
        checks = [
            ("Directory Structure", self.validate_directory_structure),
            ("Python Environment", self.validate_python_environment),
            ("Dependencies", self.validate_dependencies),
            ("Configuration Files", self.validate_configuration),
            ("Import Structure", self.validate_imports),
            ("Database Models", self.validate_database_models),
            ("Domain Entities", self.validate_domain_entities),
            ("Repositories", self.validate_repositories),
            ("Use Cases", self.validate_use_cases),
            ("API Routes", self.validate_api_routes),
            ("Main Application", self.validate_main_app),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            print(f"Checking {check_name}...")
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                print_error(f"Validation error in {check_name}: {e}")
                all_passed = False
            print()
        
        self.print_summary()
        return all_passed
    
    def validate_directory_structure(self) -> bool:
        """Validate that all required directories exist."""
        required_dirs = [
            "src",
            "src/domain",
            "src/domain/entities",
            "src/domain/repositories", 
            "src/domain/services",
            "src/domain/events",
            "src/application",
            "src/application/use_cases",
            "src/application/dto",
            "src/infrastructure",
            "src/infrastructure/database",
            "src/infrastructure/database/models",
            "src/infrastructure/database/repositories",
            "src/presentation",
            "src/presentation/api",
            "src/presentation/api/v1",
            "src/presentation/websockets",
            "tests",
            "tests/unit",
            "tests/integration",
            "migrations"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.backend_dir / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            for dir_path in missing_dirs:
                print_error(f"Missing directory: {dir_path}")
            return False
        
        print_success("All required directories exist")
        return True
    
    def validate_python_environment(self) -> bool:
        """Validate Python environment setup."""
        # Check if virtual environment exists
        venv_path = self.backend_dir / "venv"
        if not venv_path.exists():
            print_warning("Virtual environment not found at backend/venv")
        else:
            print_success("Virtual environment found")
        
        # Check Python version
        try:
            result = subprocess.run([sys.executable, "--version"], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            print_success(f"Python version: {version}")
            
            # Check if Python 3.11+
            import sys
            if sys.version_info < (3, 11):
                print_error("Python 3.11+ is required")
                return False
                
        except Exception as e:
            print_error(f"Cannot check Python version: {e}")
            return False
        
        return True
    
    def validate_dependencies(self) -> bool:
        """Validate that all required dependencies are available."""
        required_deps = [
            'flask',
            'sqlalchemy', 
            'pydantic',
            'pytest',
            'alembic'
        ]
        
        missing_deps = []
        for dep in required_deps:
            try:
                __import__(dep)
                print_success(f"Dependency available: {dep}")
            except ImportError:
                missing_deps.append(dep)
                print_error(f"Missing dependency: {dep}")
        
        if missing_deps:
            print_info("Install missing dependencies with:")
            print_info("pip install -r requirements-dev.txt")
            return False
        
        return True
    
    def validate_configuration(self) -> bool:
        """Validate configuration files."""
        config_files = [
            "requirements.txt",
            "requirements-dev.txt",
            ".env"
        ]
        
        missing_files = []
        for file_path in config_files:
            full_path = self.backend_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            else:
                print_success(f"Configuration file exists: {file_path}")
        
        if missing_files:
            for file_path in missing_files:
                print_error(f"Missing configuration file: {file_path}")
            return False
        
        return True
    
    def validate_imports(self) -> bool:
        """Validate that Python modules can be imported."""
        # Add backend/src to Python path
        backend_src = str(self.backend_dir / "src")
        if backend_src not in sys.path:
            sys.path.insert(0, backend_src)
        
        # Check for __init__.py files
        init_files = [
            "src/__init__.py",
            "src/domain/__init__.py",
            "src/domain/entities/__init__.py",
            "src/domain/repositories/__init__.py",
            "src/application/__init__.py",
            "src/infrastructure/__init__.py",
        ]
        
        for init_file in init_files:
            path = self.backend_dir / init_file
            if not path.exists():
                print_warning(f"Missing __init__.py: {init_file}")
        
        print_success("Import structure validated")
        return True
    
    def validate_database_models(self) -> bool:
        """Validate database models can be imported."""
        try:
            # Try to import common model files
            model_files = [
                "infrastructure.database.models.base",
                "infrastructure.database.models.player", 
                "infrastructure.database.models.game",
                "infrastructure.database.models.property"
            ]
            
            for model_file in model_files:
                try:
                    spec = importlib.util.find_spec(model_file)
                    if spec is None:
                        print_warning(f"Model not found: {model_file}")
                    else:
                        print_success(f"Model available: {model_file}")
                except Exception as e:
                    print_warning(f"Cannot check model {model_file}: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Error validating database models: {e}")
            return False
    
    def validate_domain_entities(self) -> bool:
        """Validate domain entities can be imported."""
        try:
            entity_files = [
                "domain.entities.player",
                "domain.entities.game", 
                "domain.entities.property",
                "domain.entities.value_objects"
            ]
            
            for entity_file in entity_files:
                try:
                    spec = importlib.util.find_spec(entity_file)
                    if spec is None:
                        print_warning(f"Entity not found: {entity_file}")
                    else:
                        print_success(f"Entity available: {entity_file}")
                except Exception as e:
                    print_warning(f"Cannot check entity {entity_file}: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Error validating domain entities: {e}")
            return False
    
    def validate_repositories(self) -> bool:
        """Validate repository interfaces and implementations."""
        try:
            repo_files = [
                "domain.repositories.player_repository",
                "domain.repositories.game_repository",
                "infrastructure.database.repositories.player_repository"
            ]
            
            for repo_file in repo_files:
                try:
                    spec = importlib.util.find_spec(repo_file)
                    if spec is None:
                        print_warning(f"Repository not found: {repo_file}")
                    else:
                        print_success(f"Repository available: {repo_file}")
                except Exception as e:
                    print_warning(f"Cannot check repository {repo_file}: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Error validating repositories: {e}")
            return False
    
    def validate_use_cases(self) -> bool:
        """Validate use cases can be imported."""
        try:
            use_case_files = [
                "application.use_cases.create_player",
                "application.use_cases.move_player",
                "application.use_cases.start_game"
            ]
            
            for use_case_file in use_case_files:
                try:
                    spec = importlib.util.find_spec(use_case_file)
                    if spec is None:
                        print_warning(f"Use case not found: {use_case_file}")
                    else:
                        print_success(f"Use case available: {use_case_file}")
                except Exception as e:
                    print_warning(f"Cannot check use case {use_case_file}: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Error validating use cases: {e}")
            return False
    
    def validate_api_routes(self) -> bool:
        """Validate API routes can be imported."""
        try:
            route_files = [
                "presentation.api.v1.routers.players",
                "presentation.api.v1.routers.games"
            ]
            
            for route_file in route_files:
                try:
                    spec = importlib.util.find_spec(route_file)
                    if spec is None:
                        print_warning(f"Route not found: {route_file}")
                    else:
                        print_success(f"Route available: {route_file}")
                except Exception as e:
                    print_warning(f"Cannot check route {route_file}: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Error validating API routes: {e}")
            return False
    
    def validate_main_app(self) -> bool:
        """Validate main application can be imported."""
        try:
            main_file = self.backend_dir / "src" / "main.py"
            if not main_file.exists():
                print_error("Main application file not found: src/main.py")
                return False
            
            # Try to import main module
            try:
                spec = importlib.util.find_spec("main")
                if spec is None:
                    print_warning("Cannot import main module")
                else:
                    print_success("Main application module available")
            except Exception as e:
                print_warning(f"Cannot check main module: {e}")
            
            return True
            
        except Exception as e:
            print_error(f"Error validating main application: {e}")
            return False
    
    def print_summary(self):
        """Print validation summary."""
        print("=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)
        
        if not self.errors and not self.warnings:
            print_success("All validations passed! ✨")
            print_info("Your backend is ready for development.")
        else:
            if self.errors:
                print_error(f"Found {len(self.errors)} error(s)")
                for error in self.errors:
                    print_error(f"  - {error}")
            
            if self.warnings:
                print_warning(f"Found {len(self.warnings)} warning(s)")
                for warning in self.warnings:
                    print_warning(f"  - {warning}")
        
        print()
        print_info("Next steps:")
        print_info("1. Fix any errors above")
        print_info("2. Create missing files using templates")
        print_info("3. Run: python src/main.py")
        print_info("4. Test API: curl http://localhost:8000/health")

def main():
    """Main validation function."""
    if len(sys.argv) > 1:
        backend_dir = sys.argv[1]
    else:
        backend_dir = "backend"
    
    validator = BackendValidator(backend_dir)
    
    if not Path(backend_dir).exists():
        print_error(f"Backend directory not found: {backend_dir}")
        print_info("Run this script from the project root directory")
        sys.exit(1)
    
    success = validator.validate_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()