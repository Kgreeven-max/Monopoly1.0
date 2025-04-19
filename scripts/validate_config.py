#!/usr/bin/env python3
"""
validate_config.py - Validates Pi-nopoly configuration files against schema

This script checks the configuration files for a Pi-nopoly installation,
validating them against the configuration schema and ensuring consistency
across environments.

Usage:
    python validate_config.py [options]

Options:
    --config-dir PATH       Path to configuration directory (default: ./config)
    --environments ENV1,... Comma-separated list of environments to validate (default: all)
    --strict                Enable strict validation mode
    --json                  Output results in JSON format
    --quiet                 Suppress all output except errors and final result
    --fix                   Attempt to fix minor issues automatically
    --backup                Create backups before fixing issues
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set
import jsonschema
import copy
import datetime

# Import the configuration schema
try:
    from generate_config import CONFIG_SCHEMA
except ImportError:
    print("Error: Could not import CONFIG_SCHEMA from generate_config.py")
    print("Make sure generate_config.py is in the same directory as this script")
    sys.exit(1)

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    CRITICAL = '\033[91m\033[1m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable color output"""
        Colors.HEADER = ''
        Colors.INFO = ''
        Colors.SUCCESS = ''
        Colors.WARNING = ''
        Colors.ERROR = ''
        Colors.CRITICAL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''

# Check if Windows terminal doesn't support ANSI colors
if sys.platform == "win32" and not os.environ.get("TERM"):
    Colors.disable()

class ValidationResult:
    """Class to store and report validation results"""
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.fixed = []
    
    def add_error(self, message: str, file: str = None, key: str = None):
        """Add an error message"""
        self.errors.append({"message": message, "file": file, "key": key})
    
    def add_warning(self, message: str, file: str = None, key: str = None):
        """Add a warning message"""
        self.warnings.append({"message": message, "file": file, "key": key})
    
    def add_info(self, message: str, file: str = None, key: str = None):
        """Add an informational message"""
        self.info.append({"message": message, "file": file, "key": key})
    
    def add_fixed(self, message: str, file: str = None, key: str = None):
        """Add a fixed issue message"""
        self.fixed.append({"message": message, "file": file, "key": key})
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def print_report(self, quiet: bool = False, json_output: bool = False):
        """Print the validation report"""
        if json_output:
            result = {
                "errors": self.errors,
                "warnings": self.warnings,
                "info": self.info,
                "fixed": self.fixed,
                "status": "failed" if self.has_errors() else "passed_with_warnings" if self.has_warnings() else "passed"
            }
            print(json.dumps(result, indent=2))
            return
        
        if not quiet:
            # Print information messages
            for item in self.info:
                print(f"{Colors.INFO}INFO:{Colors.ENDC} {item['message']}")
                if item['file']:
                    print(f"  File: {item['file']}")
                if item['key']:
                    print(f"  Key: {item['key']}")
            
            # Print fixed messages
            for item in self.fixed:
                print(f"{Colors.SUCCESS}FIXED:{Colors.ENDC} {item['message']}")
                if item['file']:
                    print(f"  File: {item['file']}")
                if item['key']:
                    print(f"  Key: {item['key']}")
        
        # Print warning messages
        if self.warnings:
            print(f"\n{Colors.WARNING}Warnings:{Colors.ENDC}")
            for item in self.warnings:
                print(f"{Colors.WARNING}WARNING:{Colors.ENDC} {item['message']}")
                if item['file']:
                    print(f"  File: {item['file']}")
                if item['key']:
                    print(f"  Key: {item['key']}")
        
        # Print error messages
        if self.errors:
            print(f"\n{Colors.ERROR}Errors:{Colors.ENDC}")
            for item in self.errors:
                print(f"{Colors.ERROR}ERROR:{Colors.ENDC} {item['message']}")
                if item['file']:
                    print(f"  File: {item['file']}")
                if item['key']:
                    print(f"  Key: {item['key']}")
        
        # Print summary
        if not quiet:
            print("\n" + "=" * 50)
            if not self.has_errors() and not self.has_warnings():
                print(f"{Colors.SUCCESS}Validation Passed! All configurations are valid.{Colors.ENDC}")
            elif not self.has_errors():
                print(f"{Colors.WARNING}Validation Passed with Warnings!{Colors.ENDC}")
                print(f"  {len(self.warnings)} warnings found that should be addressed.")
            else:
                print(f"{Colors.ERROR}Validation Failed!{Colors.ENDC}")
                print(f"  {len(self.errors)} errors found that must be fixed.")
                if self.warnings:
                    print(f"  {len(self.warnings)} warnings found that should be addressed.")
            
            if self.fixed:
                print(f"\n{Colors.SUCCESS}{len(self.fixed)} issues were automatically fixed.{Colors.ENDC}")

def generate_json_schema() -> Dict[str, Any]:
    """Generate a JSON schema from the CONFIG_SCHEMA"""
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Process each configuration option
    for key, config in CONFIG_SCHEMA.items():
        # Map Python types to JSON schema types
        if config["type"] == str:
            prop_type = "string"
        elif config["type"] == int:
            prop_type = "integer"
        elif config["type"] == float:
            prop_type = "number"
        elif config["type"] == bool:
            prop_type = "boolean"
        elif config["type"] == list:
            prop_type = "array"
        elif config["type"] == dict:
            prop_type = "object"
        else:
            # Default to string for unknown types
            prop_type = "string"
        
        # Create property definition
        schema["properties"][key] = {"type": prop_type}
        
        # Add description if available
        if "description" in config:
            schema["properties"][key]["description"] = config["description"]
        
        # Add enum if available
        if "enum" in config:
            schema["properties"][key]["enum"] = config["enum"]
        
        # Add required property
        if config.get("required", False):
            schema["required"].append(key)
    
    return schema

def load_config_file(file_path: Path) -> Tuple[Optional[Dict[str, Any]], ValidationResult]:
    """Load and parse a configuration file"""
    result = ValidationResult()
    
    if not file_path.exists():
        result.add_error(f"Configuration file not found: {file_path}", str(file_path))
        return None, result
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
            result.add_info(f"Successfully loaded configuration file: {file_path}", str(file_path))
            return config, result
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON in configuration file: {e}", str(file_path))
        return None, result

def validate_config_against_schema(config: Dict[str, Any], schema: Dict[str, Any], 
                                   file_path: str) -> ValidationResult:
    """Validate a configuration against the JSON schema"""
    result = ValidationResult()
    
    try:
        jsonschema.validate(instance=config, schema=schema)
        result.add_info(f"Configuration validates against schema", file_path)
    except jsonschema.exceptions.ValidationError as e:
        # Get the path to the error
        path = '.'.join(str(p) for p in e.path) if e.path else 'root'
        result.add_error(f"Schema validation error: {e.message} at '{path}'", file_path, path)
    
    return result

def check_for_unknown_keys(config: Dict[str, Any], file_path: str, 
                          fix: bool = False) -> Tuple[Dict[str, Any], ValidationResult]:
    """Check for unknown keys not defined in the schema"""
    result = ValidationResult()
    config_copy = copy.deepcopy(config)
    
    # Get all valid keys from the schema
    valid_keys = set(CONFIG_SCHEMA.keys())
    config_keys = set(config.keys())
    
    # Find unknown keys
    unknown_keys = config_keys - valid_keys
    
    if unknown_keys:
        # Report unknown keys
        for key in unknown_keys:
            if fix:
                del config_copy[key]
                result.add_fixed(f"Removed unknown key: {key}", file_path, key)
            else:
                result.add_warning(f"Unknown configuration key: {key}", file_path, key)
    
    return config_copy, result

def validate_environment_config(base_config: Dict[str, Any], env_config: Dict[str, Any], 
                               env_name: str, strict: bool = False) -> ValidationResult:
    """Validate environment-specific configuration against base configuration"""
    result = ValidationResult()
    
    # In strict mode, check that all required keys are present in the environment config
    if strict:
        for key, config in CONFIG_SCHEMA.items():
            if config.get("required", False) and key not in env_config:
                result.add_warning(
                    f"Required key '{key}' missing in {env_name} environment",
                    f"{env_name}.json", key
                )
    
    # Check for environment variables that might override required settings
    for key, config in CONFIG_SCHEMA.items():
        if config.get("required", False):
            env_var = f"PINOPOLY_{key.upper()}"
            if env_var in os.environ:
                result.add_info(
                    f"Environment variable {env_var} will override configuration",
                    f"{env_name}.json", key
                )
    
    # Check that production environment doesn't have development or testing values
    if env_name == "production":
        for key, value in env_config.items():
            # Check for development placeholders or testing values
            if isinstance(value, str) and ("development" in value.lower() or 
                                           "test" in value.lower() or 
                                           "placeholder" in value.lower()):
                result.add_warning(
                    f"Production environment contains possible development/test value: {key}={value}",
                    "production.json", key
                )
    
    return result

def check_consistency_across_environments(envs_configs: Dict[str, Dict[str, Any]]) -> ValidationResult:
    """Check for consistency issues across different environments"""
    result = ValidationResult()
    
    # Check for keys that appear in one environment but not others
    all_keys = set()
    for env, config in envs_configs.items():
        all_keys.update(config.keys())
    
    # For each unique key found
    for key in all_keys:
        envs_with_key = [env for env, config in envs_configs.items() if key in config]
        envs_without_key = [env for env, config in envs_configs.items() if key not in config]
        
        # If the key is required by schema, it should be in all configs
        if CONFIG_SCHEMA.get(key, {}).get("required", False) and envs_without_key:
            for env in envs_without_key:
                result.add_warning(
                    f"Required key '{key}' is missing in {env} environment",
                    f"{env}.json", key
                )
        
        # If the key is in some configs but not all, and it's not a deliberate override, flag it
        elif envs_with_key and envs_without_key and key in CONFIG_SCHEMA:
            # This is just a warning as it might be intentional
            for env in envs_without_key:
                result.add_info(
                    f"Key '{key}' exists in {', '.join(envs_with_key)} but not in {env}",
                    f"{env}.json", key
                )
    
    # Check for security keys in production
    if "production" in envs_configs:
        prod_config = envs_configs["production"]
        for key in ["secret_key", "api_key", "password", "token"]:
            for config_key in prod_config:
                if key in config_key.lower():
                    value = prod_config[config_key]
                    # Check if the value looks like a placeholder or default
                    if isinstance(value, str) and (
                        value.lower() in ["changeme", "change_me", "default", "placeholder", "example"] or
                        "change" in value.lower() or "replace" in value.lower()
                    ):
                        result.add_error(
                            f"Production environment contains placeholder for sensitive key: {config_key}={value}",
                            "production.json", config_key
                        )
    
    return result

def fix_issues(config_dir: Path, validation_results: Dict[str, ValidationResult], 
               make_backup: bool = True) -> ValidationResult:
    """Attempt to fix issues in configuration files"""
    result = ValidationResult()
    
    # Process each environment
    for env, val_result in validation_results.items():
        if not val_result.has_errors() and not val_result.has_warnings():
            continue
        
        # Load the configuration file
        file_path = config_dir / f"{env}.json"
        if not file_path.exists():
            continue
        
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Create backup if requested
            if make_backup:
                backup_path = config_dir / f"{env}.json.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                with open(backup_path, 'w') as f:
                    json.dump(config, f, indent=2)
                result.add_info(f"Created backup: {backup_path}", str(file_path))
            
            modified = False
            
            # Fix 1: Add missing required keys with default values
            for key, schema_config in CONFIG_SCHEMA.items():
                if schema_config.get("required", False) and key not in config:
                    if "default" in schema_config:
                        config[key] = schema_config["default"]
                        result.add_fixed(f"Added missing required key '{key}' with default value", str(file_path), key)
                        modified = True
            
            # Fix 2: Remove unknown keys
            valid_keys = set(CONFIG_SCHEMA.keys())
            config_keys = set(config.keys())
            unknown_keys = config_keys - valid_keys
            
            for key in unknown_keys:
                del config[key]
                result.add_fixed(f"Removed unknown key: {key}", str(file_path), key)
                modified = True
            
            # Write back the modified configuration if changes were made
            if modified:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                result.add_info(f"Updated configuration file: {file_path}", str(file_path))
            
        except (json.JSONDecodeError, PermissionError, IOError) as e:
            result.add_error(f"Failed to fix issues in {file_path}: {e}", str(file_path))
    
    return result

def validate_configs(config_dir: Path, environments: List[str], 
                    strict: bool = False, fix: bool = False,
                    backup: bool = True) -> ValidationResult:
    """Validate all configuration files"""
    # Initialize results
    final_result = ValidationResult()
    per_env_results = {}
    
    # Generate JSON schema from CONFIG_SCHEMA
    json_schema = generate_json_schema()
    
    # Validate base configuration first
    base_file = config_dir / "base.json"
    base_config, base_result = load_config_file(base_file)
    final_result.errors.extend(base_result.errors)
    final_result.warnings.extend(base_result.warnings)
    final_result.info.extend(base_result.info)
    
    if base_config is not None:
        # Validate against schema
        schema_result = validate_config_against_schema(base_config, json_schema, str(base_file))
        final_result.errors.extend(schema_result.errors)
        final_result.warnings.extend(schema_result.warnings)
        final_result.info.extend(schema_result.info)
        
        # Check for unknown keys
        cleaned_base_config, unknown_keys_result = check_for_unknown_keys(
            base_config, str(base_file), fix
        )
        final_result.warnings.extend(unknown_keys_result.warnings)
        final_result.fixed.extend(unknown_keys_result.fixed)
        
        # Store cleaned config for environment validation
        base_config = cleaned_base_config if fix else base_config
    else:
        # Cannot continue without base configuration
        final_result.add_error("Cannot validate environment configurations without a valid base configuration")
        return final_result
    
    # Check if we should test all environments
    if not environments:
        environments = ["development", "testing", "production"]
    
    # Keep track of all environment configs for cross-environment checks
    env_configs = {"base": base_config}
    
    # Validate each environment
    for env in environments:
        env_file = config_dir / f"{env}.json"
        env_config, env_result = load_config_file(env_file)
        per_env_results[env] = env_result
        
        final_result.errors.extend(env_result.errors)
        final_result.warnings.extend(env_result.warnings)
        final_result.info.extend(env_result.info)
        
        if env_config is not None:
            # Validate against schema
            schema_result = validate_config_against_schema(env_config, json_schema, str(env_file))
            final_result.errors.extend(schema_result.errors)
            final_result.warnings.extend(schema_result.warnings)
            final_result.info.extend(schema_result.info)
            
            # Check for unknown keys
            cleaned_env_config, unknown_keys_result = check_for_unknown_keys(
                env_config, str(env_file), fix
            )
            final_result.warnings.extend(unknown_keys_result.warnings)
            final_result.fixed.extend(unknown_keys_result.fixed)
            
            # Validate environment-specific configuration
            env_val_result = validate_environment_config(base_config, 
                                                       cleaned_env_config if fix else env_config,
                                                       env, strict)
            final_result.errors.extend(env_val_result.errors)
            final_result.warnings.extend(env_val_result.warnings)
            final_result.info.extend(env_val_result.info)
            
            # Store environment config for cross-environment checks
            env_configs[env] = cleaned_env_config if fix else env_config
    
    # Check for consistency across environments
    consistency_result = check_consistency_across_environments(env_configs)
    final_result.errors.extend(consistency_result.errors)
    final_result.warnings.extend(consistency_result.warnings)
    final_result.info.extend(consistency_result.info)
    
    # Fix issues if requested
    if fix:
        fix_result = fix_issues(config_dir, per_env_results, backup)
        final_result.errors.extend(fix_result.errors)
        final_result.fixed.extend(fix_result.fixed)
        final_result.info.extend(fix_result.info)
    
    return final_result

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Validate Pi-nopoly configuration files")
    parser.add_argument("--config-dir", type=str, default="./config",
                        help="Path to configuration directory (default: ./config)")
    parser.add_argument("--environments", type=str, default="",
                        help="Comma-separated list of environments to validate (default: all)")
    parser.add_argument("--strict", action="store_true",
                        help="Enable strict validation mode")
    parser.add_argument("--json", action="store_true",
                        help="Output results in JSON format")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress all output except errors and final result")
    parser.add_argument("--fix", action="store_true",
                        help="Attempt to fix minor issues automatically")
    parser.add_argument("--backup", action="store_true",
                        help="Create backups before fixing issues")
    
    args = parser.parse_args()
    
    # Normalize the config directory path
    config_dir = Path(args.config_dir)
    
    # Check if config directory exists
    if not config_dir.exists():
        print(f"{Colors.ERROR}Error: Configuration directory does not exist: {config_dir}{Colors.ENDC}")
        return 1
    
    # Parse environments
    environments = [env.strip() for env in args.environments.split(",") if env.strip()] if args.environments else []
    
    # Validate configurations
    result = validate_configs(
        config_dir, environments, args.strict, args.fix, args.backup
    )
    
    # Print the report
    result.print_report(args.quiet, args.json)
    
    # Return exit code
    return 1 if result.has_errors() else 0

if __name__ == "__main__":
    sys.exit(main()) 