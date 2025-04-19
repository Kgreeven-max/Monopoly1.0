#!/usr/bin/env python3
"""
Flask Application Configuration for Pi-nopoly.

This module provides utilities for configuring a Flask application with
the Pi-nopoly configuration system. It sets up the application with the
appropriate configuration values based on the environment and provides
utilities for accessing configuration values.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, current_app, request
from flask.cli import ScriptInfo

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration utilities
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.config_manager import (
        init_config, 
        get_config, 
        set_config, 
        update_config, 
        get_all_config, 
        get_flask_config
    )
    from src.utils.flask_config import (
        configure_flask_app,
        get_environment,
        update_flask_config,
        get_secret_key,
        is_debug_mode,
        get_port
    )
except ImportError as e:
    logger.error(f"Could not import configuration utilities: {e}")
    logger.error("Make sure the project is properly installed.")
    raise


def create_app(environment: Optional[str] = None, config_dir: Optional[str] = None) -> Flask:
    """
    Create and configure a Flask application instance.
    
    Args:
        environment: The environment to use (development, testing, production).
                    If None, it will be determined from environment variables.
        config_dir: Path to the configuration directory.
                   If None, it will use the default config directory.
                   
    Returns:
        A configured Flask application instance.
    """
    # Create Flask application
    app = Flask("pinopoly")
    
    # Determine the environment
    if environment is None:
        environment = get_environment()
    
    # Configure the application
    logger.info(f"Configuring application for {environment} environment...")
    configure_flask_app(app, environment, config_dir)
    
    # Set up error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        return {"error": "Internal server error"}, 500
    
    # Set up before request handler to log requests in debug mode
    @app.before_request
    def log_request():
        if app.debug:
            logger.debug(f"Request: {request.method} {request.path}")
    
    # Set up after request handler to log response in debug mode
    @app.after_request
    def log_response(response):
        if app.debug:
            logger.debug(f"Response: {response.status}")
        return response
    
    # Register health check endpoint
    @app.route('/api/health')
    def health_check():
        return {"status": "ok"}
    
    logger.info(f"Application configured for {environment} environment")
    return app


def configure_app_with_cli(info: ScriptInfo) -> Flask:
    """
    Configure the Flask application from the command line interface.
    
    This function is used as a factory for the Flask CLI. It creates and
    configures a Flask application instance based on the environment and
    configuration directory specified in the command line or environment
    variables.
    
    Args:
        info: The ScriptInfo instance from the Flask CLI.
        
    Returns:
        A configured Flask application instance.
    """
    # Get environment from environment variables
    environment = get_environment()
    
    # Create and configure the application
    app = create_app(environment)
    
    # Add the configuration to the ScriptInfo for use by other CLI commands
    info.data['config'] = app.config
    
    return app


def get_app_config() -> Dict[str, Any]:
    """
    Get the configuration of the current application.
    
    Returns:
        The configuration dictionary of the current application.
    """
    if current_app:
        return dict(current_app.config)
    else:
        return get_all_config()


def set_app_config(key: str, value: Any):
    """
    Set a configuration value in the current application.
    
    Args:
        key: The configuration key.
        value: The configuration value.
    """
    if current_app:
        current_app.config[key] = value
        set_config(key, value)
    else:
        set_config(key, value)


def update_app_config(config_dict: Dict[str, Any]):
    """
    Update multiple configuration values in the current application.
    
    Args:
        config_dict: Dictionary of configuration keys and values.
    """
    if current_app:
        current_app.config.update(config_dict)
        update_config(config_dict)
    else:
        update_config(config_dict)


# Flask application factory for use with the Flask CLI
app = create_app


if __name__ == "__main__":
    # This file is not meant to be run directly, but if it is, create and run the application
    from flask import request
    
    # Create and configure the application
    app = create_app()
    
    # Run the application
    port = get_port()
    debug = is_debug_mode()
    
    logger.info(f"Starting application on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug) 