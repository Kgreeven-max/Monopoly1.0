#!/usr/bin/env python3
"""
Pi-nopoly Server Startup Script

This script starts the Pi-nopoly server with proper configuration loading.
It loads the appropriate configuration based on the environment and
starts the Flask application with the configured settings.
"""

import os
import sys
import argparse
import subprocess
import logging

# Set up argument parser
parser = argparse.ArgumentParser(description='Start the Pi-nopoly server')
parser.add_argument(
    '--env', 
    choices=['development', 'testing', 'production'],
    default=None,
    help='Environment to run the server in (default: read from FLASK_ENV or PINOPOLY_ENV)'
)
parser.add_argument(
    '--port', 
    type=int, 
    default=None,
    help='Port to run the server on (default: from configuration)'
)
parser.add_argument(
    '--config-dir', 
    type=str, 
    default=None,
    help='Path to configuration directory (default: ./config)'
)
parser.add_argument(
    '--debug', 
    action='store_true',
    help='Run in debug mode (default: from configuration)'
)
parser.add_argument(
    '--generate-config',
    action='store_true',
    help='Generate configuration files before starting the server'
)

args = parser.parse_args()

# Set environment variables based on arguments
if args.env:
    os.environ['PINOPOLY_ENV'] = args.env
    
if args.port:
    os.environ['PINOPOLY_PORT'] = str(args.port)
    
if args.debug:
    os.environ['PINOPOLY_DEBUG'] = 'true'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pinopoly.log"),
        logging.StreamHandler()
    ]
)

# Generate configuration if requested
if args.generate_config:
    logging.info("Generating configuration files...")
    
    # Check if we have the correct environment
    if not args.env and not os.environ.get('PINOPOLY_ENV') and not os.environ.get('FLASK_ENV'):
        logging.warning("No environment specified. Using 'development' as default.")
        env = 'development'
    else:
        env = args.env or os.environ.get('PINOPOLY_ENV') or os.environ.get('FLASK_ENV') or 'development'
    
    # Run the configuration generator
    try:
        cmd = ["python", "generate_config.py", "generate", f"--env={env}"]
        if args.config_dir:
            cmd.extend(["--config-dir", args.config_dir])
            
        logging.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logging.info("Configuration generation complete.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Configuration generation failed: {e}")
        sys.exit(1)

# Run the application
try:
    logging.info("Starting Pi-nopoly server...")
    from app import app, socketio, setup_scheduled_tasks
    from src.utils.flask_config import get_port, is_debug_mode
    
    setup_scheduled_tasks()
    
    port = args.port or get_port()
    debug = args.debug or is_debug_mode()
    
    logging.info(f"Server running on port {port} with debug mode {'enabled' if debug else 'disabled'}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
    
except Exception as e:
    logging.error(f"Failed to start server: {e}", exc_info=True)
    sys.exit(1) 