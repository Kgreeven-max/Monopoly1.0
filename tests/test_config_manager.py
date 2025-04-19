import unittest
import os
import tempfile
import json
import shutil
from pathlib import Path
from src.utils.config_manager import ConfigManager, CONFIG_SCHEMA

class TestConfigManager(unittest.TestCase):
    """Test the configuration manager."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir)
        
        # Save original environment variables
        self.original_env = os.environ.copy()
        
        # Create test config files
        self.create_test_config_files()

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def create_test_config_files(self):
        """Create test configuration files."""
        # Base config
        base_config = {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db",
            "SECRET_KEY": "test-base-key",
            "ADMIN_KEY": "admin-base",
            "PORT": 5555
        }
        with open(self.config_path / "base.json", "w") as f:
            json.dump(base_config, f)
        
        # Development config
        dev_config = {
            "DEBUG": True,
            "SECRET_KEY": "test-dev-key"
        }
        with open(self.config_path / "development.json", "w") as f:
            json.dump(dev_config, f)
        
        # Production config
        prod_config = {
            "DEBUG": False,
            "SECRET_KEY": "test-prod-key"
        }
        with open(self.config_path / "production.json", "w") as f:
            json.dump(prod_config, f)

    def test_init_defaults(self):
        """Test initialization with default values."""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Check that defaults were loaded
        for key, schema in CONFIG_SCHEMA.items():
            if "default" in schema:
                self.assertIn(key, config_manager.config)
                self.assertEqual(config_manager.config[key], schema["default"])

    def test_load_from_base_file(self):
        """Test loading configuration from base file."""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Load config from file
        base_config = config_manager._load_from_file("base.json")
        
        # Check that values were loaded correctly
        self.assertEqual(base_config["SQLALCHEMY_DATABASE_URI"], "sqlite:///test.db")
        self.assertEqual(base_config["SECRET_KEY"], "test-base-key")
        self.assertEqual(base_config["ADMIN_KEY"], "admin-base")
        self.assertEqual(base_config["PORT"], 5555)

    def test_load_from_env_file(self):
        """Test loading configuration from environment-specific file."""
        # Set environment to development
        os.environ["FLASK_ENV"] = "development"
        
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Load config from file
        env_config = config_manager._load_from_file("development.json")
        
        # Check that values were loaded correctly
        self.assertEqual(env_config["DEBUG"], True)
        self.assertEqual(env_config["SECRET_KEY"], "test-dev-key")

    def test_load_from_env_variables(self):
        """Test loading configuration from environment variables."""
        # Set environment variables
        os.environ["PINOPOLY_DEBUG"] = "true"
        os.environ["PINOPOLY_PORT"] = "8888"
        os.environ["DATABASE_URI"] = "sqlite:///env.db"  # Uses env_var mapping
        
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Load config from environment
        env_config = config_manager._load_from_env()
        
        # Check that values were loaded correctly
        self.assertEqual(env_config["DEBUG"], True)
        self.assertEqual(env_config["PORT"], 8888)
        self.assertEqual(env_config["SQLALCHEMY_DATABASE_URI"], "sqlite:///env.db")

    def test_load_config(self):
        """Test loading configuration from all sources."""
        # Set environment
        os.environ["FLASK_ENV"] = "development"
        os.environ["PINOPOLY_PORT"] = "9999"
        
        config_manager = ConfigManager(config_path=self.config_path)
        config_manager.load_config()
        
        # Check values from different sources
        # From base.json
        self.assertEqual(config_manager.get("SQLALCHEMY_DATABASE_URI"), "sqlite:///test.db")
        self.assertEqual(config_manager.get("ADMIN_KEY"), "admin-base")
        
        # From development.json (overrides base.json)
        self.assertEqual(config_manager.get("SECRET_KEY"), "test-dev-key")
        self.assertEqual(config_manager.get("DEBUG"), True)
        
        # From environment variables (overrides files)
        self.assertEqual(config_manager.get("PORT"), 9999)

    def test_set_config(self):
        """Test setting configuration values."""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Set a value
        config_manager.set("DEBUG", True)
        
        # Check that the value was set
        self.assertEqual(config_manager.get("DEBUG"), True)
        
        # Test setting an invalid value
        with self.assertRaises(ValueError):
            config_manager.set("PORT", "not-an-int")

    def test_update_config(self):
        """Test updating multiple configuration values."""
        config_manager = ConfigManager(config_path=self.config_path)
        
        # Update values
        config_manager.update({
            "DEBUG": True,
            "PORT": 7777,
            "SECRET_KEY": "updated-key"
        })
        
        # Check that values were updated
        self.assertEqual(config_manager.get("DEBUG"), True)
        self.assertEqual(config_manager.get("PORT"), 7777)
        self.assertEqual(config_manager.get("SECRET_KEY"), "updated-key")
        
        # Test updating with invalid values
        with self.assertRaises(ValueError):
            config_manager.update({
                "PORT": "not-an-int",
                "DEBUG": True
            })
        
        # Check that no values were updated due to validation error
        self.assertEqual(config_manager.get("PORT"), 7777)
        self.assertEqual(config_manager.get("DEBUG"), True)

    def test_environment_specific_config(self):
        """Test loading different configurations for different environments."""
        # Test development environment
        os.environ["FLASK_ENV"] = "development"
        dev_config = ConfigManager(config_path=self.config_path)
        dev_config.load_config()
        self.assertEqual(dev_config.get("SECRET_KEY"), "test-dev-key")
        self.assertTrue(dev_config.get("DEBUG"))
        
        # Test production environment
        os.environ["FLASK_ENV"] = "production"
        prod_config = ConfigManager(config_path=self.config_path)
        prod_config.load_config()
        self.assertEqual(prod_config.get("SECRET_KEY"), "test-prod-key")
        self.assertFalse(prod_config.get("DEBUG"))

    def test_create_app_config(self):
        """Test creating a Flask app configuration."""
        config_manager = ConfigManager(config_path=self.config_path)
        config_manager.load_config()
        
        # Create app config
        app_config = config_manager.create_app_config()
        
        # Check that app config contains all configuration values
        self.assertEqual(app_config, config_manager.config)

if __name__ == "__main__":
    unittest.main() 