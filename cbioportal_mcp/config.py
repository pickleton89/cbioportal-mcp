#!/usr/bin/env python3
"""
Configuration management for cBioPortal MCP Server.
Supports YAML configuration files, environment variables, and CLI overrides.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from .utils.logging import get_logger

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when there's an error in configuration."""
    pass


class Configuration:
    """
    Configuration management class for cBioPortal MCP Server.
    
    Supports multiple configuration sources with priority order:
    1. CLI arguments (highest priority)
    2. Environment variables
    3. Configuration file
    4. Default values (lowest priority)
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "server": {
            "base_url": "https://www.cbioportal.org/api",
            "client_timeout": 480.0,
            "transport": "stdio",
            "port": 8000,  # For future WebSocket support
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None,  # If None, log to console only
        },
        "api": {
            "rate_limit": {
                "enabled": False,
                "requests_per_second": 10,
            },
            "retry": {
                "enabled": True,
                "max_attempts": 3,
                "backoff_factor": 1.0,
            },
            "cache": {
                "enabled": False,
                "ttl_seconds": 300,
            },
        },
    }
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        "CBIOPORTAL_BASE_URL": "server.base_url",
        "CBIOPORTAL_CLIENT_TIMEOUT": "server.client_timeout",
        "CBIOPORTAL_TRANSPORT": "server.transport",
        "CBIOPORTAL_PORT": "server.port",
        "CBIOPORTAL_LOG_LEVEL": "logging.level",
        "CBIOPORTAL_LOG_FILE": "logging.file",
        "CBIOPORTAL_RATE_LIMIT_ENABLED": "api.rate_limit.enabled",
        "CBIOPORTAL_RATE_LIMIT_RPS": "api.rate_limit.requests_per_second",
        "CBIOPORTAL_RETRY_ENABLED": "api.retry.enabled",
        "CBIOPORTAL_RETRY_MAX_ATTEMPTS": "api.retry.max_attempts",
        "CBIOPORTAL_CACHE_ENABLED": "api.cache.enabled",
        "CBIOPORTAL_CACHE_TTL": "api.cache.ttl_seconds",
    }
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = Path(config_file) if config_file else None
        self._config = self._load_configuration()
        self._validate_configuration()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from all sources."""
        # Start with default configuration
        config = self._deep_copy_dict(self.DEFAULT_CONFIG)
        
        # Override with configuration file if provided
        if self.config_file:
            file_config = self._load_config_file()
            config = self._merge_configs(config, file_config)
        
        # Override with environment variables
        env_config = self._load_env_config()
        config = self._merge_configs(config, env_config)
        
        return config
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file or not self.config_file.exists():
            logger.warning(f"Configuration file not found: {self.config_file}")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from: {self.config_file}")
                return config
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file {self.config_file}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading config file {self.config_file}: {e}")
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        
        for env_var, config_path in self.ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value, config_path)
                self._set_nested_value(config, config_path, converted_value)
        
        return config
    
    def _convert_env_value(self, value: str, config_path: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if config_path.endswith(('.enabled', 'debug')):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        # Numeric conversion
        if config_path.endswith(('.timeout', '.port', '.requests_per_second', 
                                '.max_attempts', '.ttl_seconds', '.backoff_factor')):
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                logger.warning(f"Invalid numeric value for {config_path}: {value}")
                return value
        
        # String value
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set a nested configuration value using dot notation."""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries recursively."""
        result = self._deep_copy_dict(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_dict(value)
            else:
                result[key] = value
        return result
    
    def _validate_configuration(self):
        """Validate the loaded configuration."""
        # Validate required fields
        required_fields = [
            "server.base_url",
            "server.client_timeout",
            "logging.level",
        ]
        
        for field in required_fields:
            if not self._get_nested_value(field):
                raise ConfigurationError(f"Required configuration field missing: {field}")
        
        # Validate specific values
        self._validate_base_url()
        self._validate_timeout()
        self._validate_log_level()
        self._validate_transport()
        self._validate_numeric_ranges()
    
    def _validate_base_url(self):
        """Validate base URL format."""
        base_url = self.get("server.base_url")
        if not base_url or not isinstance(base_url, str):
            raise ConfigurationError("server.base_url must be a non-empty string")
        
        if not base_url.startswith(("http://", "https://")):
            raise ConfigurationError("server.base_url must start with http:// or https://")
    
    def _validate_timeout(self):
        """Validate client timeout."""
        timeout = self.get("server.client_timeout")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigurationError("server.client_timeout must be a positive number")
    
    def _validate_log_level(self):
        """Validate logging level."""
        level = self.get("logging.level")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            raise ConfigurationError(f"logging.level must be one of: {valid_levels}")
    
    def _validate_transport(self):
        """Validate transport protocol."""
        transport = self.get("server.transport")
        valid_transports = ["stdio"]  # Add more as supported
        if transport not in valid_transports:
            raise ConfigurationError(f"server.transport must be one of: {valid_transports}")
    
    def _validate_numeric_ranges(self):
        """Validate numeric configuration ranges."""
        # Validate port range
        port = self.get("server.port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            raise ConfigurationError("server.port must be an integer between 1 and 65535")
        
        # Validate rate limit
        rps = self.get("api.rate_limit.requests_per_second")
        if not isinstance(rps, (int, float)) or rps <= 0:
            raise ConfigurationError("api.rate_limit.requests_per_second must be positive")
        
        # Validate retry attempts
        max_attempts = self.get("api.retry.max_attempts")
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ConfigurationError("api.retry.max_attempts must be a positive integer")
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            path: Dot-separated path to the configuration value
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        value = self._get_nested_value(path)
        return value if value is not None else default
    
    def _get_nested_value(self, path: str) -> Any:
        """Get nested value from configuration using dot notation."""
        keys = path.split('.')
        current = self._config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current
    
    def update_from_cli_args(self, args: Dict[str, Any]):
        """
        Update configuration with CLI arguments.
        
        Args:
            args: Dictionary of CLI arguments
        """
        # Map CLI arguments to configuration paths
        cli_mappings = {
            "base_url": "server.base_url",
            "transport": "server.transport",
            "port": "server.port",
            "log_level": "logging.level",
        }
        
        for cli_arg, config_path in cli_mappings.items():
            if cli_arg in args and args[cli_arg] is not None:
                self._set_nested_value(self._config, config_path, args[cli_arg])
        
        # Re-validate after CLI updates
        self._validate_configuration()
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._deep_copy_dict(self._config)
    
    def save_to_file(self, file_path: Union[str, Path]):
        """
        Save current configuration to a YAML file.
        
        Args:
            file_path: Path where to save the configuration
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to: {file_path}")
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration to {file_path}: {e}")
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"Configuration(file={self.config_file}, base_url={self.get('server.base_url')})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Configuration(config_file={self.config_file}, config={self._config})"


def load_config(config_file: Optional[Union[str, Path]] = None) -> Configuration:
    """
    Load configuration from file, environment, and defaults.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Configuration instance
    """
    return Configuration(config_file)


def create_example_config(file_path: Union[str, Path]):
    """
    Create an example configuration file.
    
    Args:
        file_path: Path where to create the example file
    """
    example_config = {
        "server": {
            "base_url": "https://www.cbioportal.org/api",
            "client_timeout": 480.0,
            "transport": "stdio",
            "port": 8000,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None,  # Set to a file path to enable file logging
        },
        "api": {
            "rate_limit": {
                "enabled": False,
                "requests_per_second": 10,
            },
            "retry": {
                "enabled": True,
                "max_attempts": 3,
                "backoff_factor": 1.0,
            },
            "cache": {
                "enabled": False,
                "ttl_seconds": 300,
            },
        },
    }
    
    file_path = Path(file_path)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# cBioPortal MCP Server Configuration\n")
            f.write("# This is an example configuration file showing all available options\n\n")
            yaml.dump(example_config, f, default_flow_style=False, indent=2)
        logger.info(f"Example configuration created: {file_path}")
    except Exception as e:
        raise ConfigurationError(f"Error creating example config {file_path}: {e}")


if __name__ == "__main__":
    # Example usage and testing
    if len(sys.argv) > 1 and sys.argv[1] == "create-example":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "cbioportal-mcp-config.example.yaml"
        create_example_config(output_file)
        print(f"Example configuration created: {output_file}")
    else:
        # Test configuration loading
        config = load_config()
        print(f"Loaded configuration: {config}")
        print(f"Base URL: {config.get('server.base_url')}")
        print(f"Log Level: {config.get('logging.level')}")
