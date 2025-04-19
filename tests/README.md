# Testing Structure

This document outlines the correct structure for tests in the project to prevent duplication and confusion.

## Test Organization

Tests should be organized according to the following structure:

- `tests/` - Base directory for all tests
  - `api/` - Tests for API endpoints
    - `admin_api/` - Admin API endpoint tests
    - `player_api/` - Player API endpoint tests
    - `game_api/` - Game-related API endpoint tests
  - `models/` - Tests for database models
  - `controllers/` - Tests for controller logic
  - `game_logic/` - Tests for game logic
  - `unit/` - Unit tests for utility functions and helpers

## Duplicate Tests

The following test files are duplicated and should be consolidated:

1. ✅ Admin Dashboard Tests:
   - Primary: `tests/api/admin_api/test_admin_dashboard.py`
   - Duplicate (deprecated): `tests/admin/test_admin_dashboard.py`
   - Duplicate (deprecated): `tests/test_admin_endpoints.py`

2. ✅ Auction Admin Routes:
   - Primary: `tests/routes/admin/test_auction_admin_routes.py`
   - Duplicate (deprecated): `tests/test_auction_admin_routes.py`

## Authentication in Tests

All tests for authenticated endpoints should:

1. Include the appropriate authentication headers
2. Use the fixtures defined in `tests/conftest.py` for authentication
3. Not rely on monkeypatching authentication decorators unless absolutely necessary

## Guidelines for Writing Tests

1. Use descriptive test names that indicate what is being tested
2. Include assertions that clearly verify the expected behavior
3. Mock external dependencies where appropriate
4. Clean up after tests to leave the database in a clean state
5. Use fixtures to set up common test data
6. Add new tests to the appropriate directory based on the structure above

# Monopoly Tests

This directory contains tests for the Monopoly application to ensure components function correctly.

## Test Organization

- `test_system_health.py`: Core system health checks to ensure all major components are working
- `test_admin_endpoints.py`: Tests for admin API endpoints and interfaces
- `test_auction_admin_routes.py`: Tests for auction admin routes
- `test_auction_controller.py`: Tests for the auction controller
- `routes/`: Tests for specific route modules

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_system_health.py
```

To run a specific test:

```bash
pytest tests/test_system_health.py::TestSystemHealth::test_database_migrations
```

## Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=src
```

To generate an HTML coverage report:

```bash
pytest --cov=src --cov-report=html
```

## Using the System Health Test

The system health test is designed to be run whenever changes are made to the codebase to ensure everything is still working correctly. It tests:

1. Database schema and migrations
2. API endpoints
3. Socket connections
4. Admin interface components

You should run this test:
- After making any database schema changes
- After modifying core API endpoints
- After updating socket communications
- After changing admin interfaces
- Before deploying new versions

## Adding New Tests

When adding new features or fixing bugs, add corresponding tests to ensure functionality works as expected. Follow these guidelines:

1. Create test classes that focus on specific components
2. Use fixtures to set up test environments
3. Mock external dependencies when appropriate
4. Test both success and error paths

## Admin Endpoint Tests

The admin endpoint tests are particularly important for keeping the admin interface working. They will automatically detect missing or broken endpoints and suggest implementations to fix them.

If you see warning messages when running these tests, follow the suggestions to add or fix the endpoints that are not working. 