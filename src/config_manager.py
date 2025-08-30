#!/usr/bin/env python3
"""
Configuration Manager for eInk InfoDisplay
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                # Create default configuration
                self.config = self._create_default_config()
                self.save_config()
                logger.info(f"Created default configuration at {self.config_path}")
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration
        
        Returns:
            Default configuration dictionary
        """
        return {
            "display": {
                "type": "inky_impression",
                "width": 800,
                "height": 480,
                "color": "7color",
                "update_interval": 300,
                "rotation": 0
            },
            "api_keys": {
                "openweathermap": "",
                "finnhub": ""
            },
            "plugins": {
                "enabled": ["clock", "weather", "prayer", "stock"],
                "default": "clock",
                "settings": {
                    "clock": {
                        "show_seconds": False,
                        "format_24h": True,
                        "timezone": "UTC"
                    },
                    "weather": {
                        "city_id": 4791160,
                        "units": "imperial",
                        "update_interval": 1800
                    },
                    "prayer": {
                        "latitude": 38.903481,
                        "longitude": -77.262817,
                        "method": 1,
                        "update_interval": 3600
                    },
                    "stock": {
                        "symbols": ["AAPL", "GOOGL", "MSFT"],
                        "api_key": "",
                        "update_interval": 1800
                    }
                }
            },
            "web": {
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, *keys, default=None):
        """Get configuration value
        
        Args:
            *keys: Configuration keys (nested access)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section, default=None):
        """Get an entire configuration section
        
        Args:
            section: Section name
            default: Default value if section not found
            
        Returns:
            Section dictionary or default
        """
        return self.config.get(section, default if default is not None else {})
    
    def update_section(self, section, data):
        """Update an entire configuration section
        
        Args:
            section: Section name
            data: New section data
        """
        self.config[section] = data
    
    def set(self, *keys, value):
        """Set configuration value
        
        Args:
            *keys: Configuration keys (nested access)
            value: Value to set
        """
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def get_all_config(self):
        """Get entire configuration
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()
    
    def reload_config(self):
        """Reload configuration from file"""
        self.load_config()
    
    def validate_config(self):
        """Validate configuration structure
        
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check required sections
        required_sections = ['display', 'api_keys', 'plugins', 'web']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Validate display section
        display = self.config.get('display', {})
        if 'width' not in display or 'height' not in display:
            errors.append("Display section missing width or height")
        
        # Validate plugins section
        plugins = self.config.get('plugins', {})
        if 'enabled' not in plugins or not isinstance(plugins['enabled'], list):
            errors.append("Plugins section missing or invalid enabled list")
        
        # Validate web section
        web = self.config.get('web', {})
        if 'port' not in web:
            errors.append("Web section missing port")
        
        return len(errors) == 0, errors
    
    def get_plugin_config(self, plugin_name):
        """Get configuration for specific plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration dictionary
        """
        return self.get('plugins', 'settings', plugin_name, default={})
    
    def update_plugin_config(self, plugin_name, config):
        """Update configuration for specific plugin
        
        Args:
            plugin_name: Name of the plugin
            config: New plugin configuration
        """
        if 'plugins' not in self.config:
            self.config['plugins'] = {}
        if 'settings' not in self.config['plugins']:
            self.config['plugins']['settings'] = {}
        
        self.config['plugins']['settings'][plugin_name] = config
    
    def add_api_key(self, service_name, api_key):
        """Add or update an API key
        
        Args:
            service_name: Name of the service
            api_key: API key value
        """
        if 'api_keys' not in self.config:
            self.config['api_keys'] = {}
        
        self.config['api_keys'][service_name] = api_key
    
    def get_api_key(self, service_name):
        """Get API key for service
        
        Args:
            service_name: Name of the service
            
        Returns:
            API key or None
        """
        return self.get('api_keys', service_name)