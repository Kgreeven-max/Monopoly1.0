# Pi-nopoly Testing Guide

This document provides instructions for running tests and ensuring code quality in the Pi-nopoly project.

## Available Testing Tools

Pi-nopoly provides several testing utilities to help maintain code quality:

1. **Individual Test Files** - Specific controllers and components have dedicated test files
2. **run_tests.py** - General test runner for discovering and running tests
3. **run_coverage.py** - Test runner with coverage reporting
4. **make_scripts_executable.py** - Makes utility scripts executable on Unix/Linux

## How to Run Tests

### Running All Tests

To run all tests in the project:

```bash
# On Windows
python run_tests.py

# On Unix/Linux (after making scripts executable)
./run_tests.py
```

### Running a Specific Test File

To run a specific test file:

```bash
python run_tests.py -t test_game_controller.py
```

### Running Tests with Pattern Matching

To run tests matching a specific pattern:

```bash
python run_tests.py -p "test_*_controller.py"
```

### Additional Options

- `-v` or `--verbose` - Enable verbose output
- `-f` or `--failfast` - Stop on first test failure

## Running Tests with Coverage

To run tests with coverage reporting:

```bash
# Install coverage first
pip install coverage

# Run with coverage reporting
python run_coverage.py
```

### Coverage Options

- `--no-html` - Don't generate HTML report
- `--xml` - Generate XML report (useful for CI/CD systems)
- `--no-report` - Don't show coverage report in terminal
- `-v` or `--verbose` - Show verbose output
- `-p PATTERN` or `--pattern PATTERN` - Test file pattern to discover

## Individual Test Files

| Test File | Description | Controller Tested |
|-----------|-------------|-------------------|
| test_economic_cycle_controller.py | Tests for economic cycle functionality | EconomicCycleController |
| test_auction_controller.py | Tests for auction system | AuctionController |
| test_special_space_controller.py | Tests for special spaces on game board | SpecialSpaceController |
| test_game_controller.py | Tests for core game logic | GameController |

## Writing New Tests

When adding new functionality to Pi-nopoly, please follow these guidelines for writing tests:

1. **Create test files** - For new controllers or major components, create a matching test file using the naming convention `test_*.py`
2. **Use unittest** - Inherit from `unittest.TestCase` for test classes
3. **Write test methods** - Each test method should start with `test_` and test a specific aspect of functionality
4. **Use mocks** - Use `unittest.mock` to mock dependencies to isolate the component under test
5. **Organize tests** - Group related tests in the same test class
6. **Test edge cases** - Include tests for error conditions and edge cases

Example test method structure:

```python
def test_method_name(self):
    """Description of what this test verifies."""
    # Setup
    # ... setup code ...
    
    # Execute
    result = method_under_test()
    
    # Assert
    self.assertEqual(expected_value, result)
```

## Running Tests in CI/CD

For continuous integration, you can use the following commands:

```bash
# Run all tests and fail if any test fails
python run_tests.py

# Run with coverage and generate XML report
python run_coverage.py --xml
```

The XML coverage report will be saved to `.coverage_reports/coverage.xml`, which can be consumed by CI/CD systems like Jenkins, GitHub Actions, or GitLab CI.

## Troubleshooting

### Tests Not Discovered

If tests are not being discovered:

1. Ensure test files are named with the prefix `test_`
2. Ensure test classes inherit from `unittest.TestCase`
3. Ensure test methods start with `test_`

### Import Errors

If you encounter import errors:

1. Ensure your Python path includes the project root
2. Check that dependencies are installed
3. Verify module imports in test files are correct

### Coverage Not Working

If coverage reporting is not working:

1. Ensure the `coverage` package is installed (`pip install coverage`)
2. Check that source paths in `run_coverage.py` match your project structure 