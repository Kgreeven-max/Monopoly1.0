#!/usr/bin/env python3
"""
Configuration Generator for Pi-nopoly.

This script provides a command-line interface for creating and managing
configuration files for the Pi-nopoly application. It supports generating
default configuration files for different environments, validating
existing configurations, and listing available configuration options.

Usage:
    python generate_config.py [command] [options]

Commands:
    generate    Generate configuration files
    list        List available configuration options
    check       Check existing configuration files
    help        Show this help message

Examples:
    python generate_config.py generate                  # Generate base + all env configs
    python generate_config.py generate --env=production # Generate only production config
    python generate_config.py list                      # List all configuration options
    python generate_config.py check                     # Check configuration files
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import the configuration schema from the config_manager module
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from src.utils.config_manager import CONFIG_SCHEMA
except ImportError:
    print("Error: Could not import CONFIG_SCHEMA from config_manager.")
    print("Make sure this script is run from the project root directory.")
    sys.exit(1)

# Default configuration directory
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent / "config"

# Environment-specific configurations
ENV_CONFIGS = {
    "development": {
        "DEBUG": True,
        "SECRET_KEY": "pinopoly-development-only-key",
        "REMOTE_PLAY_ENABLED": True,
        "REMOTE_PLAY_TIMEOUT": 120,
        "ECONOMIC_CYCLE_INTERVAL": 2
    },
    "testing": {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "DEBUG": False,
        "SECRET_KEY": "pinopoly-testing-key",
        "ADMIN_KEY": "admin-test",
        "DISPLAY_KEY": "display-test",
        "REMOTE_PLAY_ENABLED": False,
        "ECONOMIC_CYCLE_ENABLED": False,
        "ADAPTIVE_DIFFICULTY_ENABLED": False,
        "POLICE_PATROL_ENABLED": False
    },
    "production": {
        "DEBUG": False,
        "SECRET_KEY": "CHANGE_ME_IN_PRODUCTION",
        "ADMIN_KEY": "CHANGE_ME_IN_PRODUCTION",
        "DISPLAY_KEY": "CHANGE_ME_IN_PRODUCTION",
        "ECONOMIC_CYCLE_INTERVAL": 10,
        "REMOTE_PLAY_ENABLED": True,
        "REMOTE_PLAY_TIMEOUT": 300
    }
}


def create_config_directory(config_dir: Path) -> None:
    """
    Create the configuration directory if it doesn't exist.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    if not config_dir.exists():
        print(f"Creating configuration directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Configuration directory already exists: {config_dir}")


def generate_base_config(config_dir: Path) -> None:
    """
    Generate the base configuration file with default values.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    base_config_path = config_dir / "base.json"
    
    # Check if the file already exists
    if base_config_path.exists():
        print(f"Base configuration file already exists: {base_config_path}")
        overwrite = input("Do you want to overwrite it? (y/n) ").lower().strip()
        if overwrite != 'y':
            print("Skipping base configuration file.")
            return
    
    # Generate base configuration with default values from schema
    base_config = {}
    for key, schema in CONFIG_SCHEMA.items():
        if "default" in schema:
            base_config[key] = schema["default"]
    
    # Write the configuration file
    with open(base_config_path, 'w') as f:
        json.dump(base_config, f, indent=4, sort_keys=True)
    
    print(f"Generated base configuration file: {base_config_path}")


def generate_env_config(config_dir: Path, environment: str) -> None:
    """
    Generate an environment-specific configuration file.
    
    Args:
        config_dir: Path to the configuration directory.
        environment: Environment name (development, testing, production).
    """
    if environment not in ENV_CONFIGS:
        print(f"Error: Unknown environment '{environment}'.")
        print(f"Available environments: {', '.join(ENV_CONFIGS.keys())}")
        return
    
    env_config_path = config_dir / f"{environment}.json"
    
    # Check if the file already exists
    if env_config_path.exists():
        print(f"{environment.capitalize()} configuration file already exists: {env_config_path}")
        overwrite = input("Do you want to overwrite it? (y/n) ").lower().strip()
        if overwrite != 'y':
            print(f"Skipping {environment} configuration file.")
            return
    
    # Get environment-specific configuration
    env_config = ENV_CONFIGS[environment]
    
    # Write the configuration file
    with open(env_config_path, 'w') as f:
        json.dump(env_config, f, indent=4, sort_keys=True)
    
    print(f"Generated {environment} configuration file: {env_config_path}")


def list_config_options() -> None:
    """List all available configuration options with their details."""
    print("Available configuration options:")
    print("-" * 80)
    
    # Disable the global config manager initialization to avoid log messages
    # This is a workaround to prevent the config manager from logging during our script
    import src.utils.config_manager
    original_init = src.utils.config_manager.init_config
    src.utils.config_manager.init_config = lambda *args, **kwargs: None
    
    # Get the maximum key length for padding
    max_key_length = max(len(key) for key in CONFIG_SCHEMA.keys())
    
    # Print the configuration options
    for key, schema in sorted(CONFIG_SCHEMA.items()):
        required = "Required" if schema.get("required", False) else "Optional"
        type_name = schema.get("type", Any).__name__
        default = schema.get("default", "None")
        env_var = schema.get("env_var", "")
        
        # Print the key with padding
        print(f"{key.ljust(max_key_length)} | {type_name.ljust(8)} | {required.ljust(8)} | {str(default).ljust(20)} | ENV: {env_var}")
    
    print("-" * 80)
    print("Note: You can override any of these values using environment variables.")
    
    # Restore the original init function
    src.utils.config_manager.init_config = original_init


def check_config_files(config_dir: Path) -> None:
    """
    Check if configuration files exist and validate their content.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    print(f"Checking configuration files in {config_dir}")
    print("-" * 80)
    
    # Check if the configuration directory exists
    if not config_dir.exists():
        print(f"Error: Configuration directory does not exist: {config_dir}")
        return
    
    # Check for base configuration file
    base_config_path = config_dir / "base.json"
    if not base_config_path.exists():
        print(f"Warning: Base configuration file not found: {base_config_path}")
    else:
        print(f"Base configuration file found: {base_config_path}")
        validate_config_file(base_config_path)
    
    # Check for environment-specific configuration files
    for env in ENV_CONFIGS.keys():
        env_config_path = config_dir / f"{env}.json"
        if not env_config_path.exists():
            print(f"Warning: {env.capitalize()} configuration file not found: {env_config_path}")
        else:
            print(f"{env.capitalize()} configuration file found: {env_config_path}")
            validate_config_file(env_config_path)
            
    print("-" * 80)


def validate_config_file(config_path: Path) -> None:
    """
    Validate a configuration file against the schema.
    
    Args:
        config_path: Path to the configuration file.
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for unknown keys
        unknown_keys = [key for key in config.keys() if key not in CONFIG_SCHEMA]
        if unknown_keys:
            print(f"  Warning: Unknown configuration keys: {', '.join(unknown_keys)}")
        
        # Check for required keys in base.json
        if config_path.name == "base.json":
            required_keys = [key for key, schema in CONFIG_SCHEMA.items() if schema.get("required", False)]
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                print(f"  Error: Missing required configuration keys: {', '.join(missing_keys)}")
        
        # Track type errors for reporting
        type_errors = []
        
        # Check for type mismatches
        for key, value in config.items():
            if key in CONFIG_SCHEMA:
                expected_type = CONFIG_SCHEMA[key]["type"]
                if not isinstance(value, expected_type) and value is not None:
                    # Special case for bool and int
                    if expected_type == bool and isinstance(value, int):
                        continue
                    
                    type_errors.append(f"{key}: expected {expected_type.__name__}, got {type(value).__name__}")
        
        if type_errors:
            print(f"  Warning: Type mismatches found:")
            for error in type_errors:
                print(f"    - {error}")
        
        print("  Validation complete.")
    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON in configuration file: {e}")
        print(f"  File: {config_path}")
    except IOError as e:
        print(f"  Error: Could not read configuration file: {e}")
        print(f"  File: {config_path}")
    except Exception as e:
        print(f"  Unexpected error during validation: {str(e)}")
        print(f"  File: {config_path}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Configuration Generator for Pi-nopoly")
    
    # Command argument
    parser.add_argument(
        "command",
        choices=["generate", "list", "check", "help"],
        help="Command to execute"
    )
    
    # Configuration directory option
    parser.add_argument(
        "--config-dir",
        "-c",
        type=str,
        default=str(DEFAULT_CONFIG_DIR),
        help=f"Configuration directory (default: {DEFAULT_CONFIG_DIR})"
    )
    
    # Environment option for generate command
    parser.add_argument(
        "--env",
        "-e",
        type=str,
        choices=list(ENV_CONFIGS.keys()) + ["all", "base"],
        default="all",
        help="Environment for which to generate configuration (default: all)"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_args()
    
    # Get the configuration directory
    config_dir = Path(args.config_dir)
    
    # Execute the command
    if args.command == "generate":
        create_config_directory(config_dir)
        
        if args.env == "all":
            # Generate base and all environment configurations
            generate_base_config(config_dir)
            for env in ENV_CONFIGS.keys():
                generate_env_config(config_dir, env)
        elif args.env == "base":
            # Generate only base configuration
            generate_base_config(config_dir)
        else:
            # Generate only the specified environment configuration
            generate_env_config(config_dir, args.env)
    
    elif args.command == "list":
        list_config_options()
    
    elif args.command == "check":
        check_config_files(config_dir)
    
    elif args.command == "help":
        print(__doc__)


if __name__ == "__main__":
    main() 