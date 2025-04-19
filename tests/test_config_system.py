#!/usr/bin/env python3
"""
Configuration System Test Script for Pi-nopoly.

This script tests the Pi-nopoly configuration system by loading configuration
from different sources and printing the results.

Usage:
    python test_config_system.py [environment]

Arguments:
    environment: Optional environment name (development, testing, production)
                Default is development.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import configuration utilities
try:
    from src.utils.config_manager import (
        init_config, 
        get_config, 
        get_all_config, 
        CONFIG_SCHEMA
    )
except ImportError:
    print("Error: Could not import configuration utilities.")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_config_value(key: str, value: Any, source: str = None):
    """Print a configuration value with its key and optional source."""
    if source:
        print(f"{key}: {value} (from {source})")
    else:
        print(f"{key}: {value}")

def print_dict(data: Dict[str, Any], indent: int = 0):
    """Print a dictionary with indentation."""
    for key, value in sorted(data.items()):
        if isinstance(value, dict):
            print("  " * indent + f"{key}:")
            print_dict(value, indent + 1)
        else:
            print("  " * indent + f"{key}: {value}")

def main():
    """Main function."""
    # Get environment from command line argument
    environment = "development"
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    
    if environment not in ["development", "testing", "production"]:
        print(f"Error: Unknown environment '{environment}'.")
        print("Available environments: development, testing, production")
        sys.exit(1)
    
    print_section(f"PI-NOPOLY CONFIGURATION SYSTEM TEST ({environment.upper()})")
    
    # Initialize configuration
    print(f"Initializing configuration for {environment} environment...")
    init_config(base_path=str(project_root / "config"), environment=environment)
    
    # Print the schema
    print_section("CONFIGURATION SCHEMA")
    print(f"Total options: {len(CONFIG_SCHEMA)}")
    for key, schema in sorted(CONFIG_SCHEMA.items()):
        print(f"\n{key}:")
        print(f"  Type: {schema['type'].__name__}")
        print(f"  Required: {schema.get('required', False)}")
        if 'default' in schema:
            print(f"  Default: {schema['default']}")
        if 'env_var' in schema:
            print(f"  Environment Variable: {schema['env_var']}")
    
    # Print all configuration values
    print_section("ALL CONFIGURATION VALUES")
    config = get_all_config()
    print_dict(config)
    
    # Test getting specific values
    print_section("SPECIFIC CONFIGURATION VALUES")
    print_config_value("DEBUG", get_config("DEBUG"))
    print_config_value("SECRET_KEY", get_config("SECRET_KEY"))
    print_config_value("PORT", get_config("PORT"))
    print_config_value("SQLALCHEMY_DATABASE_URI", get_config("SQLALCHEMY_DATABASE_URI"))
    
    # Test environment variables
    print_section("ENVIRONMENT VARIABLE OVERRIDE TEST")
    test_key = "TEST_PORT"
    test_value = 8080
    
    # Save original value
    original_value = get_config("PORT")
    print(f"Original PORT value: {original_value}")
    
    # Set environment variable
    os.environ["PINOPOLY_PORT"] = str(test_value)
    
    # Reinitialize configuration
    init_config(base_path=str(project_root / "config"), environment=environment)
    
    # Check if override worked
    new_value = get_config("PORT")
    print(f"New PORT value after setting PINOPOLY_PORT={test_value}: {new_value}")
    
    # Clean up
    del os.environ["PINOPOLY_PORT"]
    
    print_section("TEST COMPLETE")
    print("The configuration system is working properly!")

if __name__ == "__main__":
    main() 