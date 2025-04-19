#!/usr/bin/env python3
"""
flask_config.py - Flask configuration manager for Pi-nopoly

This module provides a configuration manager for Flask applications that
integrates with Pi-nopoly's configuration system. It loads configuration
from the Pi-nopoly configuration files and environment variables,
and provides them in a format that Flask can use.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flask_config')

class PinopolyFlaskConfig:
    """
    Flask configuration manager for Pi-nopoly applications.
    
    This class loads configuration from Pi-nopoly's configuration files
    and environment variables, and provides them in a format that Flask
    can use.
    """
    
    def __init__(
        self,
        app_env: Optional[str] = None,
        config_dir: Optional[Path] = None,
        flask_env_prefix: str = 'FLASK_',
        pinopoly_env_prefix: str = 'PINOPOLY_'
    ):
        """
        Initialize the configuration manager.
        
        Args:
            app_env: The application environment (development, testing, production).
                     If None, will be determined from FLASK_ENV or default to 'development'.
            config_dir: The directory containing the configuration files.
                       If None, will use './config' relative to current directory.
            flask_env_prefix: The prefix for Flask environment variables.
            pinopoly_env_prefix: The prefix for Pi-nopoly environment variables.
        """
        # Set default config directory if not provided
        if config_dir is None:
            config_dir = Path('./config')
        
        self.config_dir = config_dir
        self.flask_env_prefix = flask_env_prefix
        self.pinopoly_env_prefix = pinopoly_env_prefix
        
        # Determine environment
        if app_env is None:
            app_env = os.environ.get('FLASK_ENV', 'development')
        
        self.app_env = app_env
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from files and environment variables.
        
        Returns:
            Dict[str, Any]: The loaded configuration.
        """
        config = {}
        
        # Check if config directory exists
        if not self.config_dir.exists():
            logger.warning(f"Configuration directory not found: {self.config_dir}")
            return config
        
        # Load base configuration
        base_config_path = self.config_dir / 'base.json'
        if base_config_path.exists():
            try:
                with open(base_config_path, 'r') as f:
                    base_config = json.load(f)
                    config.update(base_config)
                    logger.info(f"Loaded base configuration from {base_config_path}")
            except (json.JSONDecodeError, PermissionError, IOError) as e:
                logger.error(f"Failed to load base configuration: {e}")
        else:
            logger.warning(f"Base configuration file not found: {base_config_path}")
        
        # Load environment-specific configuration
        env_config_path = self.config_dir / f"{self.app_env}.json"
        if env_config_path.exists():
            try:
                with open(env_config_path, 'r') as f:
                    env_config = json.load(f)
                    config.update(env_config)
                    logger.info(f"Loaded {self.app_env} configuration from {env_config_path}")
            except (json.JSONDecodeError, PermissionError, IOError) as e:
                logger.error(f"Failed to load {self.app_env} configuration: {e}")
        else:
            logger.warning(f"Environment configuration file not found: {env_config_path}")
        
        # Load environment variables
        self._load_env_vars(config)
        
        return config
    
    def _load_env_vars(self, config: Dict[str, Any]) -> None:
        """
        Load configuration from environment variables.
        
        Environment variables with the prefix PINOPOLY_ will override
        configuration values. For example, PINOPOLY_DATABASE_URL will
        override the database_url configuration value.
        
        Args:
            config: The configuration dictionary to update.
        """
        for key, value in os.environ.items():
            # Check for Pi-nopoly environment variables
            if key.startswith(self.pinopoly_env_prefix):
                config_key = key[len(self.pinopoly_env_prefix):].lower()
                
                # Convert value to appropriate type if possible
                converted_value = self._convert_value(value)
                
                # Update configuration
                config[config_key] = converted_value
                logger.info(f"Overriding {config_key} from environment variable {key}")
    
    def _convert_value(self, value: str) -> Any:
        """
        Convert a string value to an appropriate type.
        
        Args:
            value: The string value to convert.
        
        Returns:
            The converted value.
        """
        # Try to convert to boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        
        # Try to convert to integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try to convert to JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        # Return as string
        return value
    
    def get_flask_config(self) -> Dict[str, Any]:
        """
        Get the configuration in a format that Flask can use.
        
        Returns:
            Dict[str, Any]: The Flask configuration.
        """
        flask_config = {}
        
        # Add all configuration values, converting keys to uppercase
        # as expected by Flask
        for key, value in self.config.items():
            flask_key = key.upper()
            flask_config[flask_key] = value
        
        # Add environment-specific Flask settings
        if self.app_env == 'development':
            flask_config.setdefault('DEBUG', True)
            flask_config.setdefault('TESTING', False)
        elif self.app_env == 'testing':
            flask_config.setdefault('DEBUG', False)
            flask_config.setdefault('TESTING', True)
        elif self.app_env == 'production':
            flask_config.setdefault('DEBUG', False)
            flask_config.setdefault('TESTING', False)
        
        # Check for important security settings in production
        if self.app_env == 'production':
            if not flask_config.get('SECRET_KEY') or flask_config.get('SECRET_KEY') == 'changeme':
                logger.warning("SECRET_KEY is not set or has default value in production!")
            
            if flask_config.get('DEBUG', False):
                logger.warning("DEBUG is enabled in production!")
        
        return flask_config
    
    def configure_flask_app(self, app) -> None:
        """
        Configure a Flask application with the loaded configuration.
        
        Args:
            app: The Flask application to configure.
        """
        flask_config = self.get_flask_config()
        
        # Update app configuration
        app.config.update(flask_config)
        
        # Set environment
        if not app.config.get('ENV'):
            app.config['ENV'] = self.app_env
        
        logger.info(f"Configured Flask application for {self.app_env} environment")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key.
            default: The default value to return if the key is not found.
        
        Returns:
            The configuration value, or default if not found.
        """
        return self.config.get(key, default)
    
    def get_database_uri(self) -> str:
        """
        Get the database URI for SQLAlchemy.
        
        This is a convenience method that builds a SQLAlchemy connection
        string from the database configuration.
        
        Returns:
            str: The database URI.
        """
        # Get database configuration
        db_type = self.get_value('database_type', 'sqlite')
        db_host = self.get_value('database_host', 'localhost')
        db_port = self.get_value('database_port', 5432)
        db_name = self.get_value('database_name', 'pinopoly')
        db_user = self.get_value('database_user', '')
        db_password = self.get_value('database_password', '')
        
        # Build connection string based on database type
        if db_type == 'sqlite':
            # For SQLite, the database name is the path to the database file
            return f"sqlite:///{db_name}"
        elif db_type == 'postgresql':
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        elif db_type == 'mysql':
            return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            logger.warning(f"Unknown database type: {db_type}")
            return f"{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Example usage
if __name__ == "__main__":
    # Simple CLI to print configuration
    import argparse
    
    parser = argparse.ArgumentParser(description="Flask configuration manager for Pi-nopoly")
    parser.add_argument("--env", type=str, default=None,
                        help="Application environment (development, testing, production)")
    parser.add_argument("--config-dir", type=str, default="./config",
                        help="Path to configuration directory")
    parser.add_argument("--show-flask", action="store_true",
                        help="Show Flask-specific configuration")
    
    args = parser.parse_args()
    
    config_manager = PinopolyFlaskConfig(
        app_env=args.env,
        config_dir=Path(args.config_dir)
    )
    
    if args.show_flask:
        flask_config = config_manager.get_flask_config()
        print(json.dumps(flask_config, indent=2))
    else:
        print(json.dumps(config_manager.config, indent=2))

# Create a default config instance
_default_config = PinopolyFlaskConfig()

# Export functions that wrap the default config instance
def configure_flask_app(app, environment=None):
    """Configure a Flask application with the loaded configuration."""
    # If environment is provided, create a new config instance with that environment
    if environment and environment != _default_config.app_env:
        config = PinopolyFlaskConfig(app_env=environment)
        return config.configure_flask_app(app)
    return _default_config.configure_flask_app(app)

def get_environment():
    """Get the current environment (development, testing, production)."""
    return _default_config.app_env

def get_secret_key():
    """Get the secret key for the Flask application."""
    return _default_config.get_value('secret_key', 'default-secret-key')

def is_debug_mode():
    """Check if debug mode is enabled."""
    return _default_config.get_value('debug', False)

def get_port():
    """Get the port to run the Flask application on."""
    return _default_config.get_value('port', 5000) 