#!/usr/bin/env python3
"""
Configuration generator for Pi-nopoly.

This script generates configuration files for different environments based on the schema defined
in config_manager.py. It can be used to create base configuration files, environment-specific
configurations, and to validate existing configuration files.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to sys.path to import config_manager
sys.path.append(str(Path(__file__).parent.parent))
from utils.config_manager import CONFIG_SCHEMA, ConfigManager


def create_config_directory(config_dir: Path) -> None:
    """
    Create the configuration directory if it doesn't exist.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    if not config_dir.exists():
        print(f"Creating configuration directory: {config_dir}")
        config_dir.mkdir(parents=True)


def generate_base_config(config_dir: Path) -> None:
    """
    Generate a base configuration file with all available options and their default values.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    create_config_directory(config_dir)
    
    base_config = {}
    for key, schema in CONFIG_SCHEMA.items():
        if "default" in schema:
            base_config[key] = schema["default"]
    
    base_config_file = config_dir / "base.json"
    with open(base_config_file, 'w') as f:
        json.dump(base_config, f, indent=4)
    
    print(f"Generated base configuration file: {base_config_file}")


def generate_env_config(config_dir: Path, environment: str) -> None:
    """
    Generate an environment-specific configuration file.
    
    Args:
        config_dir: Path to the configuration directory.
        environment: Environment name (development, production, testing).
    """
    create_config_directory(config_dir)
    
    # Define environment-specific overrides
    env_configs = {
        "development": {
            "DEBUG": True,
            "SECRET_KEY": "dev-secret-key-change-me",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///pinopoly-dev.sqlite"
        },
        "testing": {
            "DEBUG": True,
            "SECRET_KEY": "test-secret-key-change-me",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///pinopoly-test.sqlite"
        },
        "production": {
            "DEBUG": False,
            "SECRET_KEY": "change-me-in-production",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///pinopoly-prod.sqlite",
            "PORT": 8080
        }
    }
    
    env_config = env_configs.get(environment, {})
    env_config_file = config_dir / f"{environment}.json"
    
    with open(env_config_file, 'w') as f:
        json.dump(env_config, f, indent=4)
    
    print(f"Generated {environment} configuration file: {env_config_file}")


def list_config_options() -> None:
    """List all available configuration options with their descriptions and default values."""
    print("Available configuration options:")
    print("-" * 80)
    print(f"{'Key':<30} {'Type':<10} {'Required':<10} {'Default':<20} {'Environment Variable':<25}")
    print("-" * 80)
    
    for key, schema in sorted(CONFIG_SCHEMA.items()):
        required = "Yes" if schema.get("required", False) else "No"
        default = str(schema.get("default", "None"))
        if len(default) > 20:
            default = default[:17] + "..."
        
        env_var = schema.get("env_var", f"PINOPOLY_{key}")
        
        print(f"{key:<30} {schema['type'].__name__:<10} {required:<10} {default:<20} {env_var:<25}")


def check_config_files(config_dir: Path) -> None:
    """
    Check if all necessary configuration files exist and validate their content.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    if not config_dir.exists():
        print(f"Configuration directory does not exist: {config_dir}")
        return
    
    base_config_file = config_dir / "base.json"
    if not base_config_file.exists():
        print(f"Base configuration file not found: {base_config_file}")
        return
    
    # Check environment-specific configuration files
    for env in ["development", "testing", "production"]:
        env_config_file = config_dir / f"{env}.json"
        if not env_config_file.exists():
            print(f"Warning: Environment configuration file not found: {env_config_file}")
    
    # Validate the configuration
    try:
        config_manager = ConfigManager(str(config_dir))
        for env in ["development", "testing", "production"]:
            print(f"Validating {env} configuration...")
            try:
                config_manager.load_config(env)
                print(f"✓ {env} configuration is valid")
            except ValueError as e:
                print(f"✗ {env} configuration is invalid: {e}")
    except Exception as e:
        print(f"Error validating configuration: {e}")


def main() -> None:
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Pi-nopoly Configuration Generator")
    parser.add_argument("--config-dir", type=str, default=str(Path(__file__).parent.parent.parent / "config"),
                        help="Path to the configuration directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Generate base configuration
    subparsers.add_parser("generate-base", help="Generate a base configuration file")
    
    # Generate environment-specific configuration
    env_parser = subparsers.add_parser("generate-env", help="Generate an environment-specific configuration file")
    env_parser.add_argument("environment", choices=["development", "testing", "production"],
                           help="Environment name")
    
    # Generate all configuration files
    subparsers.add_parser("generate-all", help="Generate all configuration files")
    
    # List available configuration options
    subparsers.add_parser("list", help="List all available configuration options")
    
    # Check configuration files
    subparsers.add_parser("check", help="Check if all necessary configuration files exist and validate their content")
    
    args = parser.parse_args()
    
    config_dir = Path(args.config_dir)
    
    if args.command == "generate-base":
        generate_base_config(config_dir)
    elif args.command == "generate-env":
        generate_env_config(config_dir, args.environment)
    elif args.command == "generate-all":
        generate_base_config(config_dir)
        for env in ["development", "testing", "production"]:
            generate_env_config(config_dir, env)
        print("Generated all configuration files")
    elif args.command == "list":
        list_config_options()
    elif args.command == "check":
        check_config_files(config_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 