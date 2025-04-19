import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from generate_config import (
    create_config_directory,
    generate_base_config,
    generate_env_config,
    validate_config_file,
    ENV_CONFIGS,
    CONFIG_SCHEMA
)

class TestGenerateConfig(unittest.TestCase):
    """Test the configuration generator."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def test_create_config_directory(self):
        """Test creating the configuration directory."""
        # Create a nested directory path
        nested_dir = self.config_dir / "nested" / "config"
        
        # Run the function
        create_config_directory(nested_dir)
        
        # Check that the directory was created
        self.assertTrue(nested_dir.exists())
        self.assertTrue(nested_dir.is_dir())
        
        # Run the function again to test the case where the directory already exists
        create_config_directory(nested_dir)
        self.assertTrue(nested_dir.exists())

    def test_generate_base_config(self):
        """Test generating the base configuration file."""
        # Run the function
        generate_base_config(self.config_dir)
        
        # Check that the file was created
        base_config_path = self.config_dir / "base.json"
        self.assertTrue(base_config_path.exists())
        
        # Check that the content is valid JSON
        with open(base_config_path, 'r') as f:
            config = json.load(f)
        
        # Check that all default values from schema are present
        for key, schema in CONFIG_SCHEMA.items():
            if "default" in schema:
                self.assertIn(key, config)
                self.assertEqual(config[key], schema["default"])

    def test_generate_env_config(self):
        """Test generating environment-specific configuration files."""
        # Test each environment
        for env in ENV_CONFIGS.keys():
            # Run the function
            generate_env_config(self.config_dir, env)
            
            # Check that the file was created
            env_config_path = self.config_dir / f"{env}.json"
            self.assertTrue(env_config_path.exists())
            
            # Check that the content is valid JSON
            with open(env_config_path, 'r') as f:
                config = json.load(f)
            
            # Check that all values for this environment are present
            for key, value in ENV_CONFIGS[env].items():
                self.assertIn(key, config)
                self.assertEqual(config[key], value)

    def test_validate_config_file(self):
        """Test validating configuration files."""
        # Create a valid configuration file
        valid_config = {
            "DEBUG": True,
            "PORT": 8080,
            "SECRET_KEY": "test-key"
        }
        valid_path = self.config_dir / "valid.json"
        with open(valid_path, 'w') as f:
            json.dump(valid_config, f)
        
        # Create an invalid configuration file (type error)
        invalid_config = {
            "DEBUG": "not-a-bool",
            "PORT": "not-an-int"
        }
        invalid_path = self.config_dir / "invalid.json"
        with open(invalid_path, 'w') as f:
            json.dump(invalid_config, f)
        
        # Create a configuration file with unknown keys
        unknown_config = {
            "DEBUG": True,
            "UNKNOWN_KEY": "value"
        }
        unknown_path = self.config_dir / "unknown.json"
        with open(unknown_path, 'w') as f:
            json.dump(unknown_config, f)
        
        # Test validating the files (should not raise exceptions)
        validate_config_file(valid_path)
        validate_config_file(invalid_path)
        validate_config_file(unknown_path)

    def test_generate_invalid_env_config(self):
        """Test generating configuration for an invalid environment."""
        # This should not create a file, but should also not crash
        generate_env_config(self.config_dir, "invalid-env")
        
        # Check that no file was created
        invalid_path = self.config_dir / "invalid-env.json"
        self.assertFalse(invalid_path.exists())


if __name__ == "__main__":
    unittest.main() 