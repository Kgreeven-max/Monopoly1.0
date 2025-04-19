#!/usr/bin/env python3
"""
Pi-nopoly Configuration Export Tool

This script exports Pi-nopoly configuration to different formats for various deployment scenarios.

Usage:
    python export_config.py <format> [--config-dir PATH] [--env ENVIRONMENT] [--output FILE]

Arguments:
    format                  Export format: env, docker-env, json, yaml, or shell
    --config-dir PATH       Path to the configuration directory (default: ./config)
    --env ENVIRONMENT       Environment to export (default: production)
    --output FILE           Output file (default: stdout)
    --prefix PREFIX         Prefix for environment variables (default: PINOPOLY_)
    --exclude KEYS          Comma-separated list of keys to exclude from export
    --include-comments      Include comments in the output (when supported by format)

Examples:
    # Export as environment variables to .env file
    python export_config.py env --output .env

    # Export as Docker environment file
    python export_config.py docker-env --output docker.env

    # Export as JSON
    python export_config.py json --output config.json

    # Export as YAML
    python export_config.py yaml --output config.yaml

    # Export as shell script
    python export_config.py shell --output config.sh

    # Export development environment to stdout
    python export_config.py env --env development
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Set, Optional


# Try to import the configuration schema from the project
try:
    sys.path.append(str(Path(__file__).resolve().parent))
    from generate_config import CONFIG_SCHEMA
except ImportError:
    print("Error: Could not import CONFIG_SCHEMA from generate_config.py")
    print("Please make sure you have the latest version of the Pi-nopoly repository.")
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
        print(f"Error: Configuration file does not exist: {config_path}")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_path}: {e}")
        return None
    except Exception as e:
        print(f"Error: Could not read {config_path}: {e}")
        return None


def load_merged_config(config_dir: Path, environment: str) -> Optional[Dict[str, Any]]:
    """
    Load and merge base and environment-specific configuration.
    
    Args:
        config_dir: Path to the configuration directory.
        environment: Environment to load.
        
    Returns:
        The merged configuration, or None if the files do not exist or are invalid.
    """
    base_config_path = config_dir / "base.json"
    env_config_path = config_dir / f"{environment}.json"
    
    # Check if files exist
    if not base_config_path.exists():
        print(f"Error: Base configuration file does not exist: {base_config_path}")
        return None
    
    if not env_config_path.exists():
        print(f"Error: Environment configuration file does not exist: {env_config_path}")
        return None
    
    # Load and merge configurations
    base_config = load_config_file(base_config_path)
    env_config = load_config_file(env_config_path)
    
    if base_config is None or env_config is None:
        return None
    
    # Merge configurations (environment overrides base)
    return {**base_config, **env_config}


def get_env_var_name(key: str, prefix: str) -> str:
    """
    Convert a configuration key to an environment variable name.
    
    Args:
        key: Configuration key.
        prefix: Environment variable prefix.
        
    Returns:
        The environment variable name.
    """
    # Convert camelCase or snake_case to SCREAMING_SNAKE_CASE
    result = ""
    for char in key:
        if char.isupper() and result and result[-1] != '_':
            result += '_' + char
        else:
            result += char.upper()
    
    # Replace any remaining non-alphanumeric characters with underscores
    result = ''.join(c if c.isalnum() else '_' for c in result)
    
    # Add prefix
    return f"{prefix}{result}"


def format_value_for_env(value: Any) -> str:
    """
    Format a value for use in environment variables.
    
    Args:
        value: The value to format.
        
    Returns:
        The formatted value as a string.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict) or isinstance(value, list):
        return json.dumps(value, separators=(',', ':'))
    else:
        # Escape special characters
        value_str = str(value)
        # Escape quotes
        value_str = value_str.replace('"', '\\"')
        return f'"{value_str}"'


def export_as_env(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]], prefix: str, exclude_keys: Set[str], include_comments: bool) -> str:
    """
    Export configuration as environment variables.
    
    Args:
        config: The configuration to export.
        schema: The configuration schema.
        prefix: Environment variable prefix.
        exclude_keys: Keys to exclude from export.
        include_comments: Whether to include comments in the output.
        
    Returns:
        The environment variables as a string.
    """
    result = []
    
    # Add header
    result.append("# Pi-nopoly Environment Variables")
    result.append("# Generated by export_config.py")
    result.append("")
    
    # Sort keys to ensure consistent output
    sorted_keys = sorted(config.keys())
    
    for key in sorted_keys:
        if key in exclude_keys:
            continue
        
        env_var_name = get_env_var_name(key, prefix)
        value = format_value_for_env(config[key])
        
        # Add comment if requested and available
        if include_comments and key in schema and "description" in schema[key]:
            result.append(f"# {schema[key]['description']}")
            
            # Add type and default info if available
            type_info = schema[key].get("type", "")
            default_value = schema[key].get("default", "")
            
            if type_info or default_value:
                type_str = f"Type: {type_info}" if type_info else ""
                default_str = f"Default: {default_value}" if default_value != "" else ""
                separator = ", " if type_str and default_str else ""
                result.append(f"# {type_str}{separator}{default_str}")
        
        result.append(f"{env_var_name}={value}")
        
        # Add empty line for readability
        if include_comments:
            result.append("")
    
    return "\n".join(result)


def export_as_docker_env(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]], prefix: str, exclude_keys: Set[str], include_comments: bool) -> str:
    """
    Export configuration as Docker environment variables.
    
    Args:
        config: The configuration to export.
        schema: The configuration schema.
        prefix: Environment variable prefix.
        exclude_keys: Keys to exclude from export.
        include_comments: Whether to include comments in the output.
        
    Returns:
        The Docker environment variables as a string.
    """
    # Docker env format is the same as regular env format
    return export_as_env(config, schema, prefix, exclude_keys, include_comments)


def export_as_json(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]], exclude_keys: Set[str], include_comments: bool) -> str:
    """
    Export configuration as JSON.
    
    Args:
        config: The configuration to export.
        schema: The configuration schema.
        exclude_keys: Keys to exclude from export.
        include_comments: Whether to include comments in the output.
        
    Returns:
        The JSON as a string.
    """
    # Filter excluded keys
    filtered_config = {k: v for k, v in config.items() if k not in exclude_keys}
    
    # Return formatted JSON
    return json.dumps(filtered_config, indent=2)


def export_as_yaml(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]], exclude_keys: Set[str], include_comments: bool) -> str:
    """
    Export configuration as YAML.
    
    Args:
        config: The configuration to export.
        schema: The configuration schema.
        exclude_keys: Keys to exclude from export.
        include_comments: Whether to include comments in the output.
        
    Returns:
        The YAML as a string.
    """
    try:
        import yaml
    except ImportError:
        print("Error: YAML export requires PyYAML. Please install it with 'pip install pyyaml'.")
        sys.exit(1)
    
    # Filter excluded keys
    filtered_config = {k: v for k, v in config.items() if k not in exclude_keys}
    
    result = []
    
    # Add header
    result.append("# Pi-nopoly Configuration")
    result.append("# Generated by export_config.py")
    result.append("")
    
    # Export as YAML
    yaml_str = yaml.dump(filtered_config, default_flow_style=False, sort_keys=True)
    
    # Add comments if requested
    if include_comments:
        lines = yaml_str.split("\n")
        yaml_with_comments = []
        
        for line in lines:
            if line.strip() and ":" in line:
                key = line.split(":", 1)[0].strip()
                if key in schema and "description" in schema[key]:
                    yaml_with_comments.append(f"# {schema[key]['description']}")
            yaml_with_comments.append(line)
        
        yaml_str = "\n".join(yaml_with_comments)
    
    result.append(yaml_str)
    
    return "\n".join(result)


def export_as_shell(config: Dict[str, Any], schema: Dict[str, Dict[str, Any]], prefix: str, exclude_keys: Set[str], include_comments: bool) -> str:
    """
    Export configuration as a shell script.
    
    Args:
        config: The configuration to export.
        schema: The configuration schema.
        prefix: Environment variable prefix.
        exclude_keys: Keys to exclude from export.
        include_comments: Whether to include comments in the output.
        
    Returns:
        The shell script as a string.
    """
    result = []
    
    # Add shebang and header
    result.append("#!/bin/sh")
    result.append("# Pi-nopoly Configuration Shell Script")
    result.append("# Generated by export_config.py")
    result.append("")
    
    # Sort keys to ensure consistent output
    sorted_keys = sorted(config.keys())
    
    for key in sorted_keys:
        if key in exclude_keys:
            continue
        
        env_var_name = get_env_var_name(key, prefix)
        value = format_value_for_env(config[key])
        
        # Add comment if requested and available
        if include_comments and key in schema and "description" in schema[key]:
            result.append(f"# {schema[key]['description']}")
        
        result.append(f"export {env_var_name}={value}")
        
        # Add empty line for readability
        if include_comments:
            result.append("")
    
    return "\n".join(result)


def main() -> None:
    """Main function."""
    # Define supported export formats
    export_formats = ["env", "docker-env", "json", "yaml", "shell"]
    
    parser = argparse.ArgumentParser(description="Pi-nopoly Configuration Export Tool")
    parser.add_argument(
        "format",
        choices=export_formats,
        help=f"Export format: {', '.join(export_formats)}"
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "config"),
        help="Path to the configuration directory"
    )
    parser.add_argument(
        "--env",
        type=str,
        default="production",
        help="Environment to export"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="PINOPOLY_",
        help="Prefix for environment variables"
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default="",
        help="Comma-separated list of keys to exclude from export"
    )
    parser.add_argument(
        "--include-comments",
        action="store_true",
        help="Include comments in the output"
    )
    args = parser.parse_args()
    
    # Convert to Path object
    config_dir = Path(args.config_dir)
    
    # Check if config directory exists
    if not config_dir.exists():
        print(f"Error: Configuration directory does not exist: {config_dir}")
        print("Please run setup_pinopoly_config.py to create the configuration files.")
        sys.exit(1)
    
    # Load configuration
    config = load_merged_config(config_dir, args.env)
    if config is None:
        sys.exit(1)
    
    # Convert exclude list to set
    exclude_keys = set(args.exclude.split(",")) if args.exclude else set()
    
    # Export configuration
    if args.format == "env":
        output = export_as_env(config, CONFIG_SCHEMA, args.prefix, exclude_keys, args.include_comments)
    elif args.format == "docker-env":
        output = export_as_docker_env(config, CONFIG_SCHEMA, args.prefix, exclude_keys, args.include_comments)
    elif args.format == "json":
        output = export_as_json(config, CONFIG_SCHEMA, exclude_keys, args.include_comments)
    elif args.format == "yaml":
        output = export_as_yaml(config, CONFIG_SCHEMA, exclude_keys, args.include_comments)
    elif args.format == "shell":
        output = export_as_shell(config, CONFIG_SCHEMA, args.prefix, exclude_keys, args.include_comments)
    
    # Write output
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Configuration exported to {args.output}")
        except Exception as e:
            print(f"Error: Could not write to {args.output}: {e}")
            sys.exit(1)
    else:
        print(output)


if __name__ == "__main__":
    main() 