# Pi-nopoly Configuration System

This directory contains the configuration files for Pi-nopoly. The configuration system is designed to be flexible and support different environments (development, testing, production).

## Configuration Files

The configuration files are stored in JSON format and organized as follows:

- `base.json`: Contains the base configuration settings shared across all environments
- `development.json`: Contains settings specific to the development environment
- `testing.json`: Contains settings specific to the testing environment
- `production.json`: Contains settings specific to the production environment

## Configuration Hierarchy

The configuration system works with the following hierarchy:

1. Base configuration (`base.json`)
2. Environment-specific configuration (`development.json`, `testing.json`, or `production.json`)
3. Environment variables (prefixed with `PINOPOLY_`)

Settings defined at a lower level override those defined at a higher level.

## Configuration Schema

The configuration schema defines the available configuration options, their types, default values, and whether they are required. You can see the schema in the `generate_config.py` file.

## Configuration Tools

The Pi-nopoly project includes several tools to help you manage your configuration:

### setup_pinopoly_config.py

This tool initializes the Pi-nopoly configuration directory with default configuration files.

```
python setup_pinopoly_config.py [options]
```

Options:
- `--config-dir PATH`: Path to the configuration directory (default: ./config)
- `--template-dir PATH`: Path to the template directory (default: ./config_templates)
- `--force`: Overwrite existing configuration files
- `--env ENVIRONMENT`: Only setup a specific environment (development, testing, production)
- `--secrets`: Prompt for sensitive values instead of using defaults
- `--interactive`: Interactive mode - prompt for all configuration values
- `--minimal`: Create minimal configuration files with required values only

Example:
```
python setup_pinopoly_config.py --secrets --config-dir ~/pinopoly/config
```

### generate_config.py

This tool helps you generate and manage your configuration files.

```
python generate_config.py [command] [options]
```

Commands:
- `generate`: Generate configuration files for one or all environments
- `check`: Check configuration files for errors
- `list`: List available configuration options

Options:
- `--config-dir PATH`: Path to the configuration directory
- `--env ENVIRONMENT`: The environment for which to generate configuration

Example:
```
python generate_config.py generate --env=production
```

### validate_config.py

This tool validates your configuration files against the schema and ensures consistency between environments.

```
python validate_config.py [options]
```

Options:
- `--config-dir PATH`: Path to the configuration directory (default: ./config)
- `--environments ENV1,ENV2,...`: Comma-separated list of environments to validate (default: all)
- `--strict`: Enable strict validation mode
- `--json`: Output results in JSON format

Example:
```
python validate_config.py --strict
```

## Environment Variables

You can override any configuration setting by setting an environment variable with the prefix `PINOPOLY_` followed by the configuration key in uppercase with dots replaced by underscores.

For example, to override the `debug` setting:

```bash
# For Unix-like systems
export PINOPOLY_DEBUG=false

# For Windows Command Prompt
set PINOPOLY_DEBUG=false

# For Windows PowerShell
$env:PINOPOLY_DEBUG = "false"
```

To override nested settings, use underscores to represent the nested structure:

```bash
# Override database.uri
export PINOPOLY_DATABASE_URI="sqlite:///custom_path.db"
```

## Configuration In Code

The Pi-nopoly application uses a specialized configuration loader to merge the base configuration, environment-specific configuration, and environment variables.

```python
from flask_config import load_config

# Load configuration for the current environment
config = load_config()

# Access configuration values
debug_mode = config.get("debug")
database_uri = config.get("database", {}).get("uri")
```

## Security Best Practices

1. **Never commit sensitive information** (like secret keys) to version control. Use environment variables or the `--secrets` option of the setup script to set these values.

2. **Use different secret keys** for each environment.

3. **Keep production configuration secure** and only accessible to authorized personnel.

4. **Validate configuration** before deploying to production using the validation tool.

## Adding New Configuration Options

If you need to add new configuration options, update the `CONFIG_SCHEMA` in `generate_config.py` to include the new options with their types, descriptions, and default values.

## Troubleshooting

If you encounter issues with your configuration:

1. Run the validation tool to check for errors:
   ```
   python validate_config.py --strict
   ```

2. Check that the configuration files are valid JSON.

3. Ensure that required configuration options are set.

4. Check for environment variables that might be overriding your configuration. 