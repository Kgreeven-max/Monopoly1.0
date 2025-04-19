#!/usr/bin/env python3
"""
Pi-nopoly Configuration Migration Tool

This script helps migrate configuration files when upgrading Pi-nopoly to a new version
that might have different configuration requirements.

Usage:
    python migrate_config.py [--config-dir PATH] [--backup] [--force]

Arguments:
    --config-dir PATH       Path to the configuration directory (default: ./config)
    --backup                Create backups of original configuration files before modifying
    --force                 Force migration even if not needed

The script will:
1. Backup existing configuration files if --backup is specified
2. Check existing configurations against the current schema
3. Add any missing configuration keys with default values
4. Remove deprecated configuration keys (with warning)
5. Update configuration value types if needed
"""

import os
import sys
import json
import shutil
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set


# ANSI color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @staticmethod
    def green(text):
        return f"{Colors.GREEN}{text}{Colors.RESET}"

    @staticmethod
    def yellow(text):
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

    @staticmethod
    def red(text):
        return f"{Colors.RED}{text}{Colors.RESET}"

    @staticmethod
    def blue(text):
        return f"{Colors.BLUE}{text}{Colors.RESET}"

    @staticmethod
    def bold(text):
        return f"{Colors.BOLD}{text}{Colors.RESET}"


# Try to import the configuration schema from the project
try:
    sys.path.append(str(Path(__file__).resolve().parent))
    from generate_config import CONFIG_SCHEMA
except ImportError:
    print(Colors.red("Error: Could not import CONFIG_SCHEMA from generate_config.py"))
    print(Colors.red("Please make sure you have the latest version of the Pi-nopoly repository."))
    sys.exit(1)


def load_config_file(config_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a configuration file from the specified path.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        The configuration as a dictionary, or None if the file does not exist or is invalid.
    """
    if not config_path.exists():
        print(Colors.red(f"Error: Configuration file does not exist: {config_path}"))
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(Colors.red(f"Error: Invalid JSON in {config_path}: {e}"))
        return None
    except Exception as e:
        print(Colors.red(f"Error: Could not read {config_path}: {e}"))
        return None


def save_config_file(config: Dict[str, Any], config_path: Path) -> bool:
    """
    Save a configuration to a file.
    
    Args:
        config: The configuration to save.
        config_path: Path to save the configuration to.
        
    Returns:
        True if the file was saved successfully, False otherwise.
    """
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(Colors.red(f"Error: Could not write to {config_path}: {e}"))
        return False


def backup_config_files(config_dir: Path) -> bool:
    """
    Create backups of all configuration files in the specified directory.
    
    Args:
        config_dir: Path to the configuration directory.
        
    Returns:
        True if backups were created successfully, False otherwise.
    """
    # Create backup directory
    backup_dir = config_dir / f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        backup_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(Colors.red(f"Error: Could not create backup directory: {e}"))
        return False
    
    # Copy all JSON files to backup directory
    try:
        for config_file in config_dir.glob("*.json"):
            shutil.copy2(config_file, backup_dir / config_file.name)
        
        print(Colors.green(f"✓ Created backup of configuration files in {backup_dir}"))
        return True
    except Exception as e:
        print(Colors.red(f"Error: Could not backup configuration files: {e}"))
        return False


def convert_value_type(value: Any, expected_type: str) -> Any:
    """
    Convert a value to the expected type.
    
    Args:
        value: The value to convert.
        expected_type: The expected type.
        
    Returns:
        The converted value.
    """
    if expected_type == "string":
        return str(value)
    elif expected_type == "integer":
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if isinstance(value, float):
            return int(value)
        return value
    elif expected_type == "boolean":
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
        return value
    return value


def migrate_config_file(config_path: Path, schema: Dict[str, Dict[str, Any]]) -> Tuple[bool, int, int]:
    """
    Migrate a configuration file to match the current schema.
    
    Args:
        config_path: Path to the configuration file.
        schema: The schema to migrate to.
        
    Returns:
        A tuple containing success status, number of added keys, and number of removed keys.
    """
    # Load configuration
    config = load_config_file(config_path)
    if config is None:
        return False, 0, 0
    
    # Track changes
    added_keys = 0
    removed_keys = 0
    modified_keys = 0
    
    # Add missing keys with default values
    for key, value_schema in schema.items():
        if key not in config and "default" in value_schema:
            config[key] = value_schema["default"]
            added_keys += 1
            print(Colors.blue(f"+ Added missing key '{key}' with default value '{value_schema['default']}' to {config_path.name}"))
    
    # Remove deprecated keys
    current_keys = set(schema.keys())
    config_keys = set(config.keys())
    deprecated_keys = config_keys - current_keys
    
    for key in deprecated_keys:
        del config[key]
        removed_keys += 1
        print(Colors.yellow(f"- Removed deprecated key '{key}' from {config_path.name}"))
    
    # Update value types
    for key, value in list(config.items()):
        if key in schema:
            expected_type = schema[key].get("type")
            converted_value = convert_value_type(value, expected_type)
            
            # Check if conversion actually changed the value
            if converted_value != value:
                config[key] = converted_value
                modified_keys += 1
                print(Colors.blue(f"~ Modified value for '{key}' in {config_path.name}: {value} → {converted_value}"))
    
    # Save modified configuration
    if added_keys > 0 or removed_keys > 0 or modified_keys > 0:
        if save_config_file(config, config_path):
            print(Colors.green(f"✓ Updated {config_path.name} ({added_keys} keys added, {removed_keys} keys removed, {modified_keys} keys modified)"))
            return True, added_keys, removed_keys
        else:
            return False, 0, 0
    else:
        print(Colors.green(f"✓ No changes needed for {config_path.name}"))
        return True, 0, 0


def migrate_environments(config_dir: Path, force: bool = False) -> Tuple[bool, int, int]:
    """
    Migrate all environment configuration files.
    
    Args:
        config_dir: Path to the configuration directory.
        force: Whether to force migration even if not needed.
        
    Returns:
        A tuple containing success status, number of added keys, and number of removed keys.
    """
    environments = ["base", "development", "testing", "production"]
    total_success = True
    total_added = 0
    total_removed = 0
    
    for env in environments:
        config_path = config_dir / f"{env}.json"
        if config_path.exists():
            success, added, removed = migrate_config_file(config_path, CONFIG_SCHEMA)
            total_success = total_success and success
            total_added += added
            total_removed += removed
    
    return total_success, total_added, total_removed


def check_new_required_keys(config_dir: Path) -> None:
    """
    Check for any new required keys that might not have appropriate values.
    
    Args:
        config_dir: Path to the configuration directory.
    """
    environments = ["development", "testing", "production"]
    
    required_keys = [key for key, value in CONFIG_SCHEMA.items() if value.get("required", False)]
    default_required_keys = [key for key in required_keys if key in CONFIG_SCHEMA and "default" in CONFIG_SCHEMA[key]]
    
    # These are required keys that don't have defaults in the schema and might need attention
    critical_keys = [key for key in required_keys if key not in default_required_keys]
    
    if critical_keys:
        for env in environments:
            base_config_path = config_dir / "base.json"
            env_config_path = config_dir / f"{env}.json"
            
            if not base_config_path.exists() or not env_config_path.exists():
                continue
            
            # Load and merge configurations
            base_config = load_config_file(base_config_path)
            env_config = load_config_file(env_config_path)
            
            if base_config is None or env_config is None:
                continue
                
            merged_config = {**base_config, **env_config}
            
            # Check for missing required keys with no defaults
            missing_keys = [key for key in critical_keys if key not in merged_config]
            
            if missing_keys:
                print(Colors.yellow(f"\nWARNING: {env} environment is missing required keys with no default values:"))
                for key in missing_keys:
                    print(Colors.yellow(f"  - {key}"))
                print(Colors.yellow("You must set these values manually for the application to work correctly."))


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Pi-nopoly Configuration Migration Tool")
    parser.add_argument(
        "--config-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "config"),
        help="Path to the configuration directory"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backups of original configuration files before modifying"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if not needed"
    )
    args = parser.parse_args()
    
    # Convert to Path object
    config_dir = Path(args.config_dir)
    
    # Print welcome message
    print(Colors.bold("\nPi-nopoly Configuration Migration Tool"))
    print("=" * 80)
    print(f"Configuration directory: {config_dir}")
    print("=" * 80)
    
    # Check if config directory exists
    if not config_dir.exists():
        print(Colors.red(f"Error: Configuration directory does not exist: {config_dir}"))
        print(Colors.red("Please run setup_pinopoly_config.py to create the configuration files."))
        sys.exit(1)
    
    # Create backups if requested
    if args.backup:
        if not backup_config_files(config_dir):
            print(Colors.red("Error: Could not create backups. Aborting."))
            sys.exit(1)
    
    # Migrate configuration files
    success, added, removed = migrate_environments(config_dir, args.force)
    
    # Check for new required keys
    check_new_required_keys(config_dir)
    
    # Print summary
    print(Colors.bold("\nMigration Summary"))
    print("=" * 80)
    if success:
        if added > 0 or removed > 0:
            print(Colors.green(f"✓ Successfully migrated configuration files:"))
            print(Colors.green(f"  - {added} keys added"))
            print(Colors.green(f"  - {removed} keys removed"))
        else:
            print(Colors.green("✓ All configuration files are up to date."))
    else:
        print(Colors.red("✗ Failed to migrate some configuration files."))
        print(Colors.red("  Please check the error messages above."))
    
    # Set exit code based on success
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 