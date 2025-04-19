#!/usr/bin/env python3
"""
Configuration manager for Pi-nopoly.

This module provides a centralized way to access configuration settings for the Pi-nopoly application.
It supports loading configuration from JSON files, environment variables, and provides methods to get, set,
and validate configuration values.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration schema with default values and type information
CONFIG_SCHEMA = {
    "SQLALCHEMY_DATABASE_URI": {
        "type": str,
        "required": True,
        "default": "sqlite:///pinopoly.sqlite",
        "env_var": "DATABASE_URI"  # Special case for compatibility
    },
    "SQLALCHEMY_TRACK_MODIFICATIONS": {
        "type": bool,
        "required": False,
        "default": False,
        "env_var": "PINOPOLY_SQLALCHEMY_TRACK_MODIFICATIONS"
    },
    "SECRET_KEY": {
        "type": str,
        "required": True,
        "default": "pinopoly-development-key",
        "env_var": "PINOPOLY_SECRET_KEY"
    },
    "ADMIN_KEY": {
        "type": str,
        "required": True,
        "default": "pinopoly-admin",
        "env_var": "PINOPOLY_ADMIN_KEY"
    },
    "DISPLAY_KEY": {
        "type": str,
        "required": True,
        "default": "pinopoly-display",
        "env_var": "PINOPOLY_DISPLAY_KEY"
    },
    "DEBUG": {
        "type": bool,
        "required": False,
        "default": False,
        "env_var": "PINOPOLY_DEBUG"
    },
    "PORT": {
        "type": int,
        "required": False,
        "default": 5000,
        "env_var": "PINOPOLY_PORT"
    },
    "DATABASE_PATH": {
        "type": str,
        "required": False,
        "default": "pinopoly.db",
        "env_var": "PINOPOLY_DATABASE_PATH"
    },
    "REMOTE_PLAY_ENABLED": {
        "type": bool,
        "required": False,
        "default": False,
        "env_var": "PINOPOLY_REMOTE_PLAY_ENABLED"
    },
    "REMOTE_PLAY_TIMEOUT": {
        "type": int,
        "required": False,
        "default": 60,
        "env_var": "PINOPOLY_REMOTE_PLAY_TIMEOUT"
    },
    "ADAPTIVE_DIFFICULTY_ENABLED": {
        "type": bool,
        "required": False,
        "default": True,
        "env_var": "PINOPOLY_ADAPTIVE_DIFFICULTY_ENABLED"
    },
    "ADAPTIVE_DIFFICULTY_INTERVAL": {
        "type": int,
        "required": False,
        "default": 15,
        "env_var": "PINOPOLY_ADAPTIVE_DIFFICULTY_INTERVAL"
    },
    "POLICE_PATROL_ENABLED": {
        "type": bool,
        "required": False,
        "default": True,
        "env_var": "PINOPOLY_POLICE_PATROL_ENABLED"
    },
    "POLICE_PATROL_INTERVAL": {
        "type": int,
        "required": False,
        "default": 45,
        "env_var": "PINOPOLY_POLICE_PATROL_INTERVAL"
    },
    "ECONOMIC_CYCLE_ENABLED": {
        "type": bool,
        "required": False,
        "default": True,
        "env_var": "PINOPOLY_ECONOMIC_CYCLE_ENABLED"
    },
    "ECONOMIC_CYCLE_INTERVAL": {
        "type": int,
        "required": False,
        "default": 5,
        "env_var": "PINOPOLY_ECONOMIC_CYCLE_INTERVAL"
    },
    "PROPERTY_VALUES_FOLLOW_ECONOMY": {
        "type": bool,
        "required": False,
        "default": True,
        "env_var": "PINOPOLY_PROPERTY_VALUES_FOLLOW_ECONOMY"
    },
    "FREE_PARKING_FUND": {
        "type": bool,
        "required": False,
        "default": True,
        "env_var": "PINOPOLY_FREE_PARKING_FUND"
    }
}


class ConfigManager:
    """
    Configuration manager for Pi-nopoly.
    
    This class provides methods to load, get, set, and validate configuration settings.
    It supports loading configuration from JSON files and environment variables.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            base_path: Base path for configuration files. If None, defaults to the 'config' 
                      directory in the project root.
        """
        # Determine the base path for configuration files
        if base_path is None:
            # Find the project root - assumes this file is in src/utils/
            project_root = Path(__file__).parent.parent.parent
            base_path = str(project_root / "config")
        
        self.base_path = base_path
        self.config: Dict[str, Any] = {}
        
        # Initialize with default values from schema
        self._load_defaults()
        
    def _load_defaults(self):
        """Load default values from the configuration schema."""
        for key, schema in CONFIG_SCHEMA.items():
            if "default" in schema:
                self.config[key] = schema["default"]
    
    def _parse_value(self, value: str, expected_type: type) -> Any:
        """
        Parse a string value to the expected type.
        
        Args:
            value: The string value to parse.
            expected_type: The expected type of the value.
            
        Returns:
            The parsed value.
            
        Raises:
            ValueError: If the value cannot be parsed to the expected type.
        """
        if expected_type == str:
            return value
        elif expected_type == bool:
            return value.lower() in ("true", "yes", "1", "t", "y")
        elif expected_type == int:
            return int(value)
        elif expected_type == float:
            return float(value)
        else:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Cannot parse value '{value}' to type {expected_type}") from e
    
    def _validate_config(self):
        """
        Validate the configuration against the schema.
        
        Raises:
            ValueError: If a required value is missing or has the wrong type.
        """
        for key, schema in CONFIG_SCHEMA.items():
            if schema.get("required", False) and key not in self.config:
                raise ValueError(f"Required configuration value '{key}' is missing")
            
            if key in self.config and self.config[key] is not None:
                expected_type = schema["type"]
                actual_value = self.config[key]
                
                # Check if the value has the correct type
                if expected_type == bool and isinstance(actual_value, int):
                    # Special case for bool (int is okay, we'll convert it)
                    self.config[key] = bool(actual_value)
                elif not isinstance(actual_value, expected_type):
                    # Try to convert
                    try:
                        if isinstance(actual_value, str):
                            self.config[key] = self._parse_value(actual_value, expected_type)
                        else:
                            raise ValueError(
                                f"Configuration value '{key}' has wrong type: "
                                f"expected {expected_type}, got {type(actual_value)}"
                            )
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Configuration value '{key}' has wrong type: "
                            f"expected {expected_type}, got {type(actual_value)}"
                        ) from e
    
    def load_config_file(self, file_path: str) -> bool:
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON file.
            
        Returns:
            True if the file was loaded successfully, False otherwise.
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(self.base_path) / path
            
        if not path.exists():
            logger.warning(f"Configuration file not found: {path}")
            return False
        
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
                
            # Update the configuration with values from the file
            for key, value in config_data.items():
                if key in CONFIG_SCHEMA:
                    self.config[key] = value
                else:
                    logger.warning(f"Unknown configuration key: {key}")
                    
            logger.info(f"Loaded configuration from {path}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading configuration from {path}: {e}")
            return False
    
    def load_environment_variables(self):
        """
        Load configuration from environment variables.
        
        Environment variables take precedence over configuration files.
        """
        for key, schema in CONFIG_SCHEMA.items():
            env_var = schema.get("env_var")
            if env_var and env_var in os.environ:
                raw_value = os.environ[env_var]
                expected_type = schema["type"]
                
                try:
                    self.config[key] = self._parse_value(raw_value, expected_type)
                    logger.debug(f"Loaded {key} from environment variable {env_var}")
                except ValueError as e:
                    logger.warning(f"Error parsing environment variable {env_var}: {e}")
    
    def load_config(self, environment: str = "development"):
        """
        Load configuration from files and environment variables.
        
        This method loads configuration in the following order:
        1. Default values from schema
        2. Base configuration file (base.json)
        3. Environment-specific configuration file (development.json, production.json, etc.)
        4. Environment variables
        
        Args:
            environment: Environment name (development, production, testing).
        """
        # Load base configuration
        self.load_config_file("base.json")
        
        # Load environment-specific configuration
        self.load_config_file(f"{environment}.json")
        
        # Load environment variables
        self.load_environment_variables()
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Configuration loaded for environment: {environment}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key.
            default: Default value to return if the key is not found.
            
        Returns:
            The configuration value, or the default value if the key is not found.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key.
            value: Configuration value.
            
        Raises:
            ValueError: If the key is not in the configuration schema or the value has the wrong type.
        """
        if key not in CONFIG_SCHEMA:
            logger.warning(f"Setting unknown configuration key: {key}")
        else:
            expected_type = CONFIG_SCHEMA[key]["type"]
            if not isinstance(value, expected_type):
                try:
                    if isinstance(value, str):
                        value = self._parse_value(value, expected_type)
                    else:
                        raise ValueError(
                            f"Configuration value '{key}' has wrong type: "
                            f"expected {expected_type}, got {type(value)}"
                        )
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Configuration value '{key}' has wrong type: "
                        f"expected {expected_type}, got {type(value)}"
                    ) from e
        
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update multiple configuration values.
        
        Args:
            config_dict: Dictionary of configuration keys and values.
        """
        for key, value in config_dict.items():
            self.set(key, value)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary of all configuration values.
        """
        return self.config.copy()
    
    def to_flask_config(self) -> Dict[str, Any]:
        """
        Get configuration values formatted for Flask.
        
        Returns:
            Dictionary of configuration values suitable for Flask app.config.
        """
        flask_config = {}
        for key, value in self.config.items():
            flask_config[key] = value
        return flask_config


# Global instance of the configuration manager
_config_manager = None


def init_config(base_path: Optional[str] = None, environment: str = "development"):
    """
    Initialize the global configuration manager.
    
    Args:
        base_path: Base path for configuration files.
        environment: Environment name (development, production, testing).
    """
    global _config_manager
    _config_manager = ConfigManager(base_path)
    _config_manager.load_config(environment)


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value from the global configuration manager.
    
    Args:
        key: Configuration key.
        default: Default value to return if the key is not found.
        
    Returns:
        The configuration value, or the default value if the key is not found.
    """
    global _config_manager
    if _config_manager is None:
        init_config()
    return _config_manager.get(key, default)


def set_config(key: str, value: Any):
    """
    Set a configuration value in the global configuration manager.
    
    Args:
        key: Configuration key.
        value: Configuration value.
    """
    global _config_manager
    if _config_manager is None:
        init_config()
    _config_manager.set(key, value)


def update_config(config_dict: Dict[str, Any]):
    """
    Update multiple configuration values in the global configuration manager.
    
    Args:
        config_dict: Dictionary of configuration keys and values.
    """
    global _config_manager
    if _config_manager is None:
        init_config()
    _config_manager.update(config_dict)


def get_all_config() -> Dict[str, Any]:
    """
    Get all configuration values from the global configuration manager.
    
    Returns:
        Dictionary of all configuration values.
    """
    global _config_manager
    if _config_manager is None:
        init_config()
    return _config_manager.get_all()


def get_flask_config() -> Dict[str, Any]:
    """
    Get configuration values formatted for Flask from the global configuration manager.
    
    Returns:
        Dictionary of configuration values suitable for Flask app.config.
    """
    global _config_manager
    if _config_manager is None:
        init_config()
    return _config_manager.to_flask_config()


# Initialize the global configuration manager
if __name__ != "__main__":
    init_config() 