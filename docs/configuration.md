# Pi-nopoly Configuration System

This document describes the configuration system for Pi-nopoly, including how to configure the application for different environments, available configuration options, and tools for managing configuration.

## Configuration Overview

Pi-nopoly uses a flexible configuration system with support for:

- Default values defined in code
- JSON configuration files
- Environment-specific configuration
- Environment variable overrides
- Runtime configuration changes

Configuration is loaded in the following order, with later sources overriding earlier ones:

1. Default values from the configuration schema
2. Base configuration file (`config/base.json`)
3. Environment-specific configuration file (`config/development.json`, `config/production.json`, etc.)
4. Environment variables

## Configuration Files

Configuration files are stored in the `config` directory and are in JSON format. There are four main configuration files:

- `base.json` - Common settings for all environments
- `development.json` - Settings specific to the development environment
- `production.json` - Settings specific to the production environment
- `testing.json` - Settings specific to the testing environment

## Configuration Options

| Key | Type | Required | Default | Description | Environment Variable |
|-----|------|----------|---------|-------------|---------------------|
| SQLALCHEMY_DATABASE_URI | string | Yes | `sqlite:///pinopoly.sqlite` | Database connection string | DATABASE_URI |
| SQLALCHEMY_TRACK_MODIFICATIONS | boolean | No | `false` | Track modifications flag for SQLAlchemy | PINOPOLY_SQLALCHEMY_TRACK_MODIFICATIONS |
| SECRET_KEY | string | Yes | `pinopoly-development-key` | Flask secret key | PINOPOLY_SECRET_KEY |
| ADMIN_KEY | string | Yes | `pinopoly-admin` | Admin authentication key | PINOPOLY_ADMIN_KEY |
| DISPLAY_KEY | string | Yes | `pinopoly-display` | Display authentication key | PINOPOLY_DISPLAY_KEY |
| DEBUG | boolean | No | `false` | Debug mode flag | PINOPOLY_DEBUG |
| PORT | integer | No | `5000` | Server port | PINOPOLY_PORT |
| DATABASE_PATH | string | No | `pinopoly.db` | SQLite database file path | PINOPOLY_DATABASE_PATH |
| REMOTE_PLAY_ENABLED | boolean | No | `false` | Remote play flag | PINOPOLY_REMOTE_PLAY_ENABLED |
| REMOTE_PLAY_TIMEOUT | integer | No | `60` | Remote play timeout | PINOPOLY_REMOTE_PLAY_TIMEOUT |
| ADAPTIVE_DIFFICULTY_ENABLED | boolean | No | `true` | Adaptive difficulty flag | PINOPOLY_ADAPTIVE_DIFFICULTY_ENABLED |
| ADAPTIVE_DIFFICULTY_INTERVAL | integer | No | `15` | Adaptive difficulty interval | PINOPOLY_ADAPTIVE_DIFFICULTY_INTERVAL |
| POLICE_PATROL_ENABLED | boolean | No | `true` | Police patrol flag | PINOPOLY_POLICE_PATROL_ENABLED |
| POLICE_PATROL_INTERVAL | integer | No | `45` | Police patrol interval | PINOPOLY_POLICE_PATROL_INTERVAL |
| ECONOMIC_CYCLE_ENABLED | boolean | No | `true` | Enable/disable economic cycle updates | PINOPOLY_ECONOMIC_CYCLE_ENABLED |
| ECONOMIC_CYCLE_INTERVAL | integer | No | `5` | Minutes between economic updates | PINOPOLY_ECONOMIC_CYCLE_INTERVAL |
| PROPERTY_VALUES_FOLLOW_ECONOMY | boolean | No | `true` | Whether property values update with economy | PINOPOLY_PROPERTY_VALUES_FOLLOW_ECONOMY |
| FREE_PARKING_FUND | boolean | No | `true` | Free parking fund configuration | PINOPOLY_FREE_PARKING_FUND |

## Environment Variables

You can override any configuration option by setting an environment variable. Environment variables should be prefixed with `PINOPOLY_` followed by the configuration key. For example:

```bash
# Set debug mode
export PINOPOLY_DEBUG=true

# Set server port
export PINOPOLY_PORT=8080

# Set database URI
export DATABASE_URI=postgresql://user:password@localhost/pinopoly
```

Note that the `SQLALCHEMY_DATABASE_URI` option can be set with the `DATABASE_URI` environment variable (without the `PINOPOLY_` prefix) for backward compatibility.

## Setup Scripts

Pi-nopoly provides setup scripts to help you quickly set up the configuration system:

### Unix/Linux/macOS

On Unix-like systems, you can use the `setup_config.sh` script:

```bash
# Make the script executable
chmod +x setup_config.sh

# Run the script
./setup_config.sh
```

### Windows

On Windows, you can use the `setup_config.ps1` PowerShell script:

```powershell
# Run the script (you may need to adjust PowerShell execution policy)
.\setup_config.ps1
```

Both scripts will:
1. Create the configuration directory if it doesn't exist
2. Generate the base configuration file
3. Ask which environment-specific configurations to generate
4. Check the generated configurations
5. List available configuration options

## Running the Application

Pi-nopoly provides a convenient startup script called `run_pinopoly.py` that uses the configuration system:

```bash
# Run with default settings
python run_pinopoly.py

# Run in a specific environment
python run_pinopoly.py --env=production

# Run on a specific port
python run_pinopoly.py --port=8080

# Run in debug mode
python run_pinopoly.py --debug

# Generate configuration files before starting
python run_pinopoly.py --generate-config

# Specify a custom configuration directory
python run_pinopoly.py --config-dir=/path/to/config
```

## Configuration Tools

Pi-nopoly provides several tools to help manage configuration:

### Generate Configuration Files

You can generate or update configuration files using the `generate_config.py` script:

```bash
# Generate all configuration files
python generate_config.py generate

# Generate only the base configuration
python generate_config.py generate --env=base

# Generate only the development configuration
python generate_config.py generate --env=development

# Generate only the production configuration
python generate_config.py generate --env=production

# Generate only the testing configuration
python generate_config.py generate --env=testing
```

### List Configuration Options

You can list all available configuration options:

```bash
python generate_config.py list
```

### Check Configuration Files

You can check existing configuration files for validity:

```bash
python generate_config.py check
```

## Using the Configuration System in Code

### Accessing Configuration

You can access configuration values in code using the configuration manager:

```python
from src.utils.config_manager import get_config

# Get a configuration value
debug_mode = get_config("DEBUG", False)

# Get a required configuration value
database_uri = get_config("SQLALCHEMY_DATABASE_URI")
```

### Setting Configuration

You can set configuration values at runtime:

```python
from src.utils.config_manager import set_config

# Set a configuration value
set_config("DEBUG", True)
```

### Updating Multiple Configuration Values

You can update multiple configuration values at once:

```python
from src.utils.config_manager import update_config

# Update multiple configuration values
update_config({
    "DEBUG": True,
    "PORT": 8080
})
```

### Getting All Configuration Values

You can get all configuration values as a dictionary:

```python
from src.utils.config_manager import get_all_config

# Get all configuration values
config = get_all_config()
```

## Integration with Flask

Pi-nopoly provides utilities to integrate the configuration system with Flask:

```python
from flask import Flask
from src.utils.flask_config import configure_flask_app, get_environment

# Create a Flask application
app = Flask(__name__)

# Configure the application with settings from the configuration manager
environment = get_environment()
configure_flask_app(app, environment)
```

You can also use the convenience functions to access common configuration values:

```python
from src.utils.flask_config import get_port, is_debug_mode, get_secret_key

# Get the server port
port = get_port()

# Check if debug mode is enabled
debug = is_debug_mode()

# Get the secret key
secret_key = get_secret_key()
```

You can update the Flask application configuration at runtime:

```python
from src.utils.flask_config import update_flask_config

# Update the application configuration
update_flask_config(app, {
    "DEBUG": True,
    "PORT": 8080
})
```

## Best Practices

### Sensitive Information

Do not store sensitive information (like passwords or API keys) in configuration files that are committed to version control. Instead, use environment variables or a separate configuration file that is not committed to version control.

For production environments, always change the default values for sensitive configuration options such as:
- `SECRET_KEY`
- `ADMIN_KEY`
- `DISPLAY_KEY`

The production configuration file includes placeholders like `CHANGE_ME_IN_PRODUCTION` to remind you to set these values.

### Environment-Specific Configuration

Use environment-specific configuration files for settings that differ between environments. For example, use `development.json` for development settings and `production.json` for production settings.

### Configuration Validation

Always validate configuration values at startup to ensure that all required values are set and have the correct type. The configuration manager does this automatically, but you can also check configuration files manually using the `generate_config.py check` command.

### Testing

When writing tests that depend on configuration values, use the testing environment by setting:

```python
os.environ['PINOPOLY_ENV'] = 'testing'
```

This will ensure that your tests use the testing-specific configuration values, which are often different from development or production values (e.g., using an in-memory database). 