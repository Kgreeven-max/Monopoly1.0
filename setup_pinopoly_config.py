#!/usr/bin/env python3
"""
Pi-nopoly Configuration Setup Tool

This script initializes the Pi-nopoly configuration directory with the default configuration files.
It can set up configurations for different environments (development, testing, production)
and apply environment-specific overrides.

Usage:
    python setup_pinopoly_config.py [options]

Options:
    --config-dir PATH       Path to the configuration directory (default: ./config)
    --template-dir PATH     Path to the template directory (default: ./config_templates)
    --force                 Overwrite existing configuration files
    --env ENVIRONMENT       Only setup a specific environment (development, testing, production)
    --secrets               Prompt for sensitive values instead of using defaults
    --interactive           Interactive mode - prompt for all configuration values
    --minimal               Create minimal configuration files with required values only

Example:
    python setup_pinopoly_config.py --secrets --config-dir ~/pinopoly/config
"""

import os
import sys
import json
import getpass
import secrets
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class Colors:
    """Terminal colors for output formatting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Try to import the configuration schema from the project
try:
    sys.path.append(str(Path(__file__).resolve().parent))
    from generate_config import CONFIG_SCHEMA
except ImportError:
    print(f"{Colors.ERROR}Error: Could not import CONFIG_SCHEMA from generate_config.py{Colors.ENDC}")
    print("Please make sure you have the latest version of the Pi-nopoly repository.")
    sys.exit(1)


# Environment-specific overrides
ENV_OVERRIDES = {
    "development": {
        "debug": True,
        "logLevel": "DEBUG",
        "database": {
            "uri": "sqlite:///instance/pinopoly_dev.db",
            "poolSize": 5
        },
        "secretKey": "dev_secret_key_for_development_only",
        "sessionCookie": {
            "secure": False
        }
    },
    "testing": {
        "debug": True,
        "logLevel": "DEBUG",
        "database": {
            "uri": "sqlite:///instance/pinopoly_test.db",
            "poolSize": 5
        },
        "secretKey": "test_secret_key_for_testing_only",
        "testMode": True,
        "sessionCookie": {
            "secure": False
        }
    },
    "production": {
        "debug": False,
        "logLevel": "WARNING",
        "database": {
            "uri": "sqlite:///instance/pinopoly_prod.db",
            "poolSize": 10
        },
        "secretKey": "",  # Will be generated if --secrets is used
        "sessionCookie": {
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax"
        }
    }
}


def create_directory(directory: Path) -> None:
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory: The directory to create.
    """
    if not directory.exists():
        try:
            directory.mkdir(parents=True)
            print(f"Created directory: {directory}")
        except Exception as e:
            print(f"{Colors.ERROR}Error creating directory {directory}: {e}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"Directory already exists: {directory}")


def generate_secret_key(length: int = 32) -> str:
    """
    Generate a random secret key.
    
    Args:
        length: The length of the secret key.
        
    Returns:
        A random secret key.
    """
    return secrets.token_hex(length)


def prompt_for_value(key: str, schema_entry: Dict[str, Any], default_value: Any) -> Any:
    """
    Prompt the user for a configuration value.
    
    Args:
        key: The configuration key.
        schema_entry: The schema entry for the key.
        default_value: The default value for the key.
        
    Returns:
        The user-provided value or the default value.
    """
    value_type = schema_entry.get("type", "string")
    description = schema_entry.get("description", key)
    
    # Format the prompt
    if schema_entry.get("sensitive", False):
        prompt = f"{description} [{key}] (hidden, press Enter for default): "
    else:
        prompt = f"{description} [{key}] (default: {default_value}): "
    
    if schema_entry.get("sensitive", False):
        # Use getpass for sensitive values
        user_input = getpass.getpass(prompt)
    else:
        user_input = input(prompt)
    
    # Return default if user didn't enter anything
    if not user_input:
        return default_value
    
    # Convert value to the appropriate type
    try:
        if value_type == "boolean":
            return user_input.lower() in ["true", "yes", "y", "1"]
        elif value_type == "integer":
            return int(user_input)
        elif value_type == "number":
            return float(user_input)
        elif value_type == "array":
            # Parse as JSON array
            return json.loads(user_input)
        elif value_type == "object":
            # Parse as JSON object
            return json.loads(user_input)
        else:
            # String or any other type
            return user_input
    except (ValueError, json.JSONDecodeError):
        print(f"{Colors.WARNING}Invalid input for {key}, using default value.{Colors.ENDC}")
        return default_value


def prompt_for_secrets(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prompt the user for sensitive configuration values.
    
    Args:
        config: The configuration to update.
        schema: The configuration schema.
        
    Returns:
        The updated configuration.
    """
    updated_config = config.copy()
    
    for key, value in config.items():
        if key in schema and schema[key].get("sensitive", False):
            if isinstance(value, dict):
                # Recursive call for nested objects
                updated_config[key] = prompt_for_secrets(value, schema.get(key, {}).get("properties", {}))
            else:
                # Generate a default for secret keys
                if key == "secretKey" and not value:
                    default = generate_secret_key()
                else:
                    default = value
                
                updated_config[key] = prompt_for_value(key, schema[key], default)
    
    return updated_config


def prompt_for_all_values(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prompt the user for all configuration values.
    
    Args:
        config: The configuration to update.
        schema: The configuration schema.
        
    Returns:
        The updated configuration.
    """
    updated_config = config.copy()
    
    for key, value in config.items():
        if key in schema:
            if isinstance(value, dict) and "properties" in schema.get(key, {}):
                # Recursive call for nested objects
                updated_config[key] = prompt_for_all_values(value, schema[key].get("properties", {}))
            else:
                updated_config[key] = prompt_for_value(key, schema[key], value)
    
    return updated_config


def create_minimal_config(schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a minimal configuration with only required values.
    
    Args:
        schema: The configuration schema.
        
    Returns:
        A minimal configuration.
    """
    config = {}
    
    for key, value_schema in schema.items():
        if value_schema.get("required", False):
            if value_schema.get("type") == "object" and "properties" in value_schema:
                # Recursive call for nested objects
                config[key] = create_minimal_config(value_schema["properties"])
            else:
                # Use default value or a placeholder
                if "default" in value_schema:
                    config[key] = value_schema["default"]
                elif value_schema.get("type") == "string":
                    config[key] = ""
                elif value_schema.get("type") == "number" or value_schema.get("type") == "integer":
                    config[key] = 0
                elif value_schema.get("type") == "boolean":
                    config[key] = False
                elif value_schema.get("type") == "array":
                    config[key] = []
                elif value_schema.get("type") == "object":
                    config[key] = {}
    
    return config


def create_base_config() -> Dict[str, Any]:
    """
    Create a base configuration from the schema.
    
    Returns:
        A base configuration with default values.
    """
    config = {}
    
    for key, value_schema in CONFIG_SCHEMA.items():
        if "default" in value_schema:
            config[key] = value_schema["default"]
    
    return config


def deep_merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two configurations.
    
    Args:
        base: The base configuration.
        override: The override configuration.
        
    Returns:
        The merged configuration.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def write_config_file(config: Dict[str, Any], filename: Path, force: bool = False) -> None:
    """
    Write a configuration to a file.
    
    Args:
        config: The configuration to write.
        filename: The filename to write to.
        force: Whether to overwrite an existing file.
    """
    if filename.exists() and not force:
        print(f"{Colors.WARNING}File already exists: {filename}. Use --force to overwrite.{Colors.ENDC}")
        return
    
    try:
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"{Colors.GREEN}Created configuration file: {filename}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.ERROR}Error writing to {filename}: {e}{Colors.ENDC}")


def setup_environment_config(
    config_dir: Path,
    environment: str,
    base_config: Dict[str, Any],
    force: bool = False,
    secrets: bool = False,
    interactive: bool = False,
    minimal: bool = False
) -> None:
    """
    Set up configuration for a specific environment.
    
    Args:
        config_dir: The configuration directory.
        environment: The environment to set up.
        base_config: The base configuration.
        force: Whether to overwrite existing files.
        secrets: Whether to prompt for sensitive values.
        interactive: Whether to prompt for all values.
        minimal: Whether to create minimal configuration files.
    """
    print(f"{Colors.BOLD}Setting up {environment} environment configuration...{Colors.ENDC}")
    
    # Create environment-specific configuration
    if minimal:
        # Start with only required values for this environment
        env_config = {}
        for key, value in ENV_OVERRIDES[environment].items():
            if key in CONFIG_SCHEMA and CONFIG_SCHEMA[key].get("required", False):
                env_config[key] = value
    else:
        # Use all environment overrides
        env_config = ENV_OVERRIDES[environment].copy()
    
    # Generate a unique secret key for production if needed
    if environment == "production" and "secretKey" in env_config and not env_config["secretKey"]:
        env_config["secretKey"] = generate_secret_key()
    
    # Prompt for sensitive values if requested
    if secrets:
        env_config = prompt_for_secrets(env_config, CONFIG_SCHEMA)
    
    # Prompt for all values if in interactive mode
    if interactive:
        env_config = prompt_for_all_values(env_config, CONFIG_SCHEMA)
    
    # Write the environment-specific configuration
    env_file = config_dir / f"{environment}.json"
    write_config_file(env_config, env_file, force)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Pi-nopoly Configuration Setup Tool")
    parser.add_argument(
        "--config-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "config"),
        help="Path to the configuration directory"
    )
    parser.add_argument(
        "--template-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "config_templates"),
        help="Path to the template directory"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration files"
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=["development", "testing", "production"],
        help="Only setup a specific environment"
    )
    parser.add_argument(
        "--secrets",
        action="store_true",
        help="Prompt for sensitive values instead of using defaults"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode - prompt for all configuration values"
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Create minimal configuration files with required values only"
    )
    args = parser.parse_args()
    
    # Convert to Path objects
    config_dir = Path(args.config_dir)
    template_dir = Path(args.template_dir)
    
    # Create the configuration directory
    create_directory(config_dir)
    
    # Check for templates
    use_templates = template_dir.exists() and not args.minimal
    
    # Create or copy base configuration
    if use_templates and (template_dir / "base.json").exists():
        # Copy from template
        base_config_file = template_dir / "base.json"
        target_file = config_dir / "base.json"
        
        if target_file.exists() and not args.force:
            print(f"{Colors.WARNING}File already exists: {target_file}. Use --force to overwrite.{Colors.ENDC}")
        else:
            try:
                shutil.copy(base_config_file, target_file)
                print(f"{Colors.GREEN}Copied template to: {target_file}{Colors.ENDC}")
                
                # Read the base configuration
                with open(target_file, 'r') as f:
                    base_config = json.load(f)
            except Exception as e:
                print(f"{Colors.ERROR}Error copying template: {e}{Colors.ENDC}")
                sys.exit(1)
    else:
        # Create base configuration from schema
        if args.minimal:
            base_config = create_minimal_config(CONFIG_SCHEMA)
        else:
            base_config = create_base_config()
        
        # Prompt for all values if in interactive mode
        if args.interactive:
            base_config = prompt_for_all_values(base_config, CONFIG_SCHEMA)
        
        # Write the base configuration
        base_file = config_dir / "base.json"
        write_config_file(base_config, base_file, args.force)
    
    # Set up environment-specific configurations
    environments = ["development", "testing", "production"] if args.env is None else [args.env]
    
    for env in environments:
        if use_templates and (template_dir / f"{env}.json").exists():
            # Copy from template
            env_template_file = template_dir / f"{env}.json"
            target_file = config_dir / f"{env}.json"
            
            if target_file.exists() and not args.force:
                print(f"{Colors.WARNING}File already exists: {target_file}. Use --force to overwrite.{Colors.ENDC}")
            else:
                try:
                    shutil.copy(env_template_file, target_file)
                    print(f"{Colors.GREEN}Copied template to: {target_file}{Colors.ENDC}")
                    
                    # Read the environment configuration for potential updates
                    with open(target_file, 'r') as f:
                        env_config = json.load(f)
                    
                    # Update the configuration if needed
                    updated = False
                    
                    # Generate a unique secret key for production if needed
                    if env == "production" and "secretKey" in env_config and not env_config["secretKey"]:
                        env_config["secretKey"] = generate_secret_key()
                        updated = True
                    
                    # Prompt for sensitive values if requested
                    if args.secrets:
                        env_config = prompt_for_secrets(env_config, CONFIG_SCHEMA)
                        updated = True
                    
                    # Prompt for all values if in interactive mode
                    if args.interactive:
                        env_config = prompt_for_all_values(env_config, CONFIG_SCHEMA)
                        updated = True
                    
                    # Write the updated configuration if changed
                    if updated:
                        write_config_file(env_config, target_file, True)
                    
                except Exception as e:
                    print(f"{Colors.ERROR}Error copying template: {e}{Colors.ENDC}")
        else:
            # Create environment-specific configuration
            setup_environment_config(
                config_dir,
                env,
                base_config,
                force=args.force,
                secrets=args.secrets,
                interactive=args.interactive,
                minimal=args.minimal
            )
    
    print(f"{Colors.GREEN}{Colors.BOLD}Configuration setup complete!{Colors.ENDC}")
    print(f"Configuration directory: {config_dir}")
    
    # Print validation command
    print("\nTo validate your configuration, run:")
    print(f"python validate_config.py --config-dir {config_dir}")


if __name__ == "__main__":
    main() 