# Pinopoly

A modernized Monopoly-like game implemented in Python with Flask and a client web interface.

## Project Structure

This project follows a structured organization:

- `config/` - Configuration files for different environments
- `deployment/` - Files for deploying and running the application
- `docs/` - Documentation files
- `scripts/` - Utility scripts for setup, configuration, and testing
- `src/` - Source code
  - `controllers/` - Controller logic
  - `models/` - Data models
  - `routes/` - API routes
  - `game_logic/` - Core game logic
  - `utils/` - Utility functions
  - `views/` - View templates
- `static/` - Static files (CSS, JavaScript)
- `templates/` - HTML templates
- `client/` - Frontend application
- `tests/` - Test files
- `tickets/` - Work tickets and task tracking
- `reference/` - Reference materials and original code

## Getting Started

1. Setup the backend:
   ```
   python scripts/setup_python_backend.py
   ```

2. Setup the frontend:
   ```
   python scripts/setup_frontend.py
   ```

3. Initialize the database:
   ```
   python deployment/init_db.py
   ```

4. Run the application:
   ```
   python deployment/run_pinopoly.py
   ```

For more detailed setup instructions, see `SETUP_README.md`.

## Documentation

See the `docs/` directory for detailed documentation about different aspects of the project.

## Testing

Run the tests using the provided script:
```
python scripts/run_tests.py
```

For test coverage, use:
```
python scripts/run_coverage.py
```

## License

See the LICENSE file for details. 