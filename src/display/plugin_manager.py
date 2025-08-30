#!/usr/bin/env python3
"""
Plugin Manager for eInk InfoDisplay
"""
import os
import sys
import importlib
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages and executes display plugins"""
    
    def __init__(self, config_manager, display_manager):
        """Initialize the plugin manager
        
        Args:
            config_manager: ConfigManager instance
            display_manager: EInkDisplayManager instance
        """
        self.config = config_manager
        self.display = display_manager
        self.plugins = {}
        self.current_plugin = None
        self.last_update_times = {}
        
        # Load plugins
        self._load_plugins()
        
    def _load_plugins(self):
        """Load all available plugins"""
        plugins_dir = Path(__file__).parent.parent / "plugins"
        
        if not plugins_dir.exists():
            logger.error(f"Plugins directory not found: {plugins_dir}")
            return
        
        # Add plugins directory to Python path
        sys.path.insert(0, str(plugins_dir.parent))
        
        # Get enabled plugins from config
        enabled_plugins = self.config.get("plugins", {}).get("enabled", [])
        logger.info(f"Loading enabled plugins: {enabled_plugins}")
        
        # Load each enabled plugin
        for plugin_name in enabled_plugins:
            try:
                self._load_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
    
    def _load_plugin(self, plugin_name):
        """Load a specific plugin
        
        Args:
            plugin_name: Name of the plugin to load
        """
        try:
            # Import the plugin module
            module_name = f"plugins.{plugin_name}_plugin"
            plugin_module = importlib.import_module(module_name)
            
            # Find the plugin class
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (isinstance(attr, type) and 
                    hasattr(attr, 'render') and 
                    attr.__name__.lower().endswith('plugin')):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No plugin class found in {module_name}")
                return
            
            # Get plugin configuration
            plugin_config = self.config.get("plugins", {}).get("settings", {}).get(plugin_name, {})
            
            # Create plugin instance
            plugin_instance = plugin_class(self.config, self.display, plugin_config)
            self.plugins[plugin_name] = plugin_instance
            
            logger.info(f"Loaded plugin: {plugin_name}")
            
        except ImportError as e:
            logger.error(f"Could not import plugin {plugin_name}: {e}")
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
    
    def get_available_plugins(self):
        """Get list of available plugin names
        
        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())
    
    def get_plugin(self, plugin_name):
        """Get a specific plugin instance
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)
    
    def run_plugin(self, plugin_name, force_update=False):
        """Run a specific plugin
        
        Args:
            plugin_name: Name of the plugin to run
            force_update: Force update even if recently updated
            
        Returns:
            True if successful, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Check if plugin needs update
        if not force_update and not self._should_update_plugin(plugin_name, plugin):
            logger.info(f"Plugin {plugin_name} doesn't need update yet")
            return True
        
        try:
            logger.info(f"Running plugin: {plugin_name}")
            
            # Run the plugin
            success = plugin.render()
            
            if success:
                self.current_plugin = plugin_name
                self.last_update_times[plugin_name] = datetime.now()
                logger.info(f"Plugin {plugin_name} completed successfully")
            else:
                logger.error(f"Plugin {plugin_name} failed to render")
            
            return success
            
        except Exception as e:
            logger.error(f"Error running plugin {plugin_name}: {e}")
            return False
    
    def _should_update_plugin(self, plugin_name, plugin):
        """Check if a plugin should be updated
        
        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance
            
        Returns:
            True if plugin should be updated
        """
        # Always update if never run before
        if plugin_name not in self.last_update_times:
            return True
        
        # Get plugin update interval
        update_interval = getattr(plugin, 'update_interval', 300)  # Default 5 minutes
        
        # Check if enough time has passed
        last_update = self.last_update_times[plugin_name]
        time_since_update = (datetime.now() - last_update).total_seconds()
        
        return time_since_update >= update_interval
    
    def update_display(self):
        """Update the display with the current or default plugin
        
        Returns:
            True if successful, False otherwise
        """
        # Get current or default plugin
        if self.current_plugin and self.current_plugin in self.plugins:
            plugin_name = self.current_plugin
        else:
            # Use default plugin
            default_plugin = self.config.get("plugins", {}).get("default", "clock")
            plugin_name = default_plugin if default_plugin in self.plugins else None
            
            if not plugin_name and self.plugins:
                # Use first available plugin
                plugin_name = next(iter(self.plugins))
        
        if not plugin_name:
            logger.error("No plugins available")
            return False
        
        return self.run_plugin(plugin_name)
    
    def cycle_plugins(self):
        """Cycle through all available plugins"""
        plugin_names = list(self.plugins.keys())
        
        if not plugin_names:
            logger.error("No plugins available for cycling")
            return False
        
        # Find current plugin index
        current_index = -1
        if self.current_plugin in plugin_names:
            current_index = plugin_names.index(self.current_plugin)
        
        # Move to next plugin
        next_index = (current_index + 1) % len(plugin_names)
        next_plugin = plugin_names[next_index]
        
        logger.info(f"Cycling from {self.current_plugin} to {next_plugin}")
        return self.run_plugin(next_plugin, force_update=True)
    
    def get_plugin_status(self):
        """Get status of all plugins
        
        Returns:
            Dictionary with plugin status information
        """
        status = {}
        
        for plugin_name, plugin in self.plugins.items():
            last_update = self.last_update_times.get(plugin_name)
            update_interval = getattr(plugin, 'update_interval', 300)
            
            needs_update = self._should_update_plugin(plugin_name, plugin)
            
            status[plugin_name] = {
                'loaded': True,
                'current': plugin_name == self.current_plugin,
                'last_update': last_update.isoformat() if last_update else None,
                'update_interval': update_interval,
                'needs_update': needs_update,
                'description': getattr(plugin, 'description', 'No description')
            }
        
        return status
    
    def cleanup(self):
        """Clean up plugin manager resources"""
        logger.info("Cleaning up plugin manager...")
        
        # Cleanup individual plugins
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'cleanup'):
                    plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_name}: {e}")
        
        self.plugins.clear()
        self.current_plugin = None