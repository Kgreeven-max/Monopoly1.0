"""
Flask integration utilities for configuration management.

This module provides utilities to integrate the configuration manager with Flask.
"""

from typing import Dict, Any
from flask import Flask
from . import config_manager


def configure_app(app: Flask, config_path: str = None) -> Flask:
    """
    Configure a Flask application with settings from the configuration manager.
    
    Args:
        app (Flask): The Flask application to configure
        config_path (str, optional): Path to configuration files
        
    Returns:
        Flask: The configured Flask application
    """
    # Initialize the configuration manager with the specified path
    if config_path:
        config_manager.config_manager = config_manager.ConfigManager(config_path=config_path)
    
    # Load configuration
    config_manager.load_config()
    
    # Configure Flask app
    app.config.update(config_manager.get_all_config())
    
    return app


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value.
    
    Args:
        key (str): The configuration key
        default (Any, optional): Default value if the key doesn't exist
        
    Returns:
        Any: The configuration value or the default value
    """
    return config_manager.get_config(key, default)


def set_config_value(key: str, value: Any) -> None:
    """
    Set a configuration value.
    
    Args:
        key (str): The configuration key
        value (Any): The configuration value
    """
    config_manager.set_config(key, value)


def update_app_config(app: Flask, config_dict: Dict[str, Any]) -> None:
    """
    Update the application configuration.
    
    Args:
        app (Flask): The Flask application
        config_dict (Dict[str, Any]): Dictionary of configuration keys and values
    """
    # Update the configuration manager
    config_manager.update_config(config_dict)
    
    # Update the Flask app configuration
    app.config.update(config_dict) 