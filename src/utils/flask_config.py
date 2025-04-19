"""
Flask configuration integration for Pi-nopoly.

This module provides utilities to integrate our configuration system with Flask applications.
It ensures that Flask applications are properly configured using our centralized configuration
management system, providing consistent configuration across different environments.
"""

from flask import Flask
from typing import Optional, Dict, Any
from pathlib import Path

from .config_manager import (
    init_config,
    get_config,
    get_all_config,
    get_flask_config
)


def configure_flask_app(app: Flask, 
                        environment: str = "development", 
                        config_dir: Optional[str] = None) -> Flask:
    """
    Configure a Flask application using our configuration system.
    
    This function initializes our configuration system and applies the configuration
    to the provided Flask application. It loads the base configuration, environment-specific
    configuration, and any environment variable overrides.
    
    Args:
        app: The Flask application to configure
        environment: The environment name (development, testing, production)
        config_dir: Optional path to the configuration directory
        
    Returns:
        The configured Flask application
    """
    # Initialize the configuration system
    if config_dir is None:
        # Use the default config directory
        project_root = Path(__file__).parent.parent.parent
        config_dir = str(project_root / "config")
    
    # Initialize the configuration for the specified environment
    init_config(config_dir, environment)
    
    # Get Flask-specific configuration
    flask_config = get_flask_config()
    
    # Apply configuration to Flask app
    app.config.update(flask_config)
    
    # Set environment-specific Flask options
    if environment == "development":
        app.debug = get_config("DEBUG", True)
    elif environment == "production":
        app.debug = False
    
    return app


def get_environment() -> str:
    """
    Determine the current environment based on environment variables.
    
    Returns:
        The current environment name (development, testing, production)
    """
    import os
    
    # Check environment variables in order of precedence
    env = os.environ.get("FLASK_ENV") or os.environ.get("PINOPOLY_ENV")
    
    # Default to development if not specified
    if env not in ["development", "testing", "production"]:
        env = "development"
        
    return env


def update_flask_config(app: Flask, config_updates: Dict[str, Any]) -> None:
    """
    Update the configuration of a Flask application.
    
    This function updates both our configuration system and the Flask application's
    configuration with the provided updates.
    
    Args:
        app: The Flask application to update
        config_updates: Dictionary of configuration keys and values to update
    """
    from .config_manager import update_config
    
    # Update our configuration system
    update_config(config_updates)
    
    # Update Flask app configuration
    app.config.update(config_updates)


def get_secret_key() -> str:
    """
    Get the secret key for Flask applications.
    
    Returns:
        The secret key from the configuration
    """
    return get_config("SECRET_KEY", "pinopoly-default-key-change-me")


def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled.
    
    Returns:
        True if debug mode is enabled, False otherwise
    """
    return get_config("DEBUG", False)


def get_port() -> int:
    """
    Get the server port.
    
    Returns:
        The server port from the configuration
    """
    return get_config("PORT", 5000)


def configure_flask_extensions(app: Flask) -> None:
    """
    Configure Flask extensions based on our configuration.
    
    This function configures Flask extensions such as SQLAlchemy, Flask-Login, etc.
    using our configuration system.
    
    Args:
        app: The Flask application to configure
    """
    # Example: Configure SQLAlchemy
    if "SQLALCHEMY_DATABASE_URI" in app.config:
        # SQLAlchemy will be configured with the URI from our config
        pass
    
    # Example: Configure other extensions as needed
    pass 