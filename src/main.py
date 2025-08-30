#!/usr/bin/env python3
"""
Main application for eInk InfoDisplay using Pimoroni Inky Impression 7.3"
"""
import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.display.eink_manager import EInkDisplayManager
from src.display.plugin_manager import PluginManager
from src.config_manager import ConfigManager

# Set up logging
def setup_logging():
    """Set up logging configuration"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "eink_display.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="eInk InfoDisplay")
    parser.add_argument("--config", help="Path to config file", 
                       default=str(project_root / "config.json"))
    parser.add_argument("--plugin", help="Specific plugin to run")
    parser.add_argument("--test", action="store_true", 
                       help="Test display with sample content")
    parser.add_argument("--clear", action="store_true", 
                       help="Clear the display and exit")
    parser.add_argument("--daemon", action="store_true", 
                       help="Run as daemon (continuous mode)")
    parser.add_argument("--update-interval", type=int, default=300,
                       help="Update interval in seconds (default: 300)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    
    return parser.parse_args()

class EInkInfoDisplay:
    """Main eInk InfoDisplay application"""
    
    def __init__(self, config_path, logger):
        """Initialize the display application
        
        Args:
            config_path: Path to configuration file
            logger: Logger instance
        """
        self.logger = logger
        self.config_manager = ConfigManager(config_path)
        self.display_manager = None
        self.plugin_manager = None
        self.last_update = datetime.now()
        self.running = False
        
    def initialize(self):
        """Initialize display and plugin managers"""
        try:
            # Initialize display manager
            self.display_manager = EInkDisplayManager(self.config_manager)
            self.logger.info("Display manager initialized")
            
            # Initialize plugin manager
            self.plugin_manager = PluginManager(self.config_manager, self.display_manager)
            self.logger.info("Plugin manager initialized")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            return False
    
    def test_display(self):
        """Test the display with sample content"""
        if not self.initialize():
            return False
            
        try:
            self.logger.info("Running display test...")
            self.display_manager.test_display()
            self.logger.info("Display test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Display test failed: {e}")
            return False
    
    def clear_display(self):
        """Clear the display"""
        if not self.initialize():
            return False
            
        try:
            self.logger.info("Clearing display...")
            self.display_manager.clear()
            self.logger.info("Display cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear display: {e}")
            return False
    
    def run_single_update(self, plugin_name=None):
        """Run a single update cycle
        
        Args:
            plugin_name: Specific plugin to run, or None for current plugin
        """
        if not self.initialize():
            return False
            
        try:
            if plugin_name:
                # Run specific plugin
                self.logger.info(f"Running plugin: {plugin_name}")
                success = self.plugin_manager.run_plugin(plugin_name)
            else:
                # Run current/default plugin
                success = self.plugin_manager.update_display()
            
            if success:
                self.logger.info("Display updated successfully")
                return True
            else:
                self.logger.error("Display update failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return False
    
    def run_daemon(self, update_interval=300):
        """Run in daemon mode with periodic updates
        
        Args:
            update_interval: Update interval in seconds
        """
        if not self.initialize():
            return False
        
        self.running = True
        self.logger.info(f"Starting daemon mode (update interval: {update_interval}s)")
        
        # Initial update
        self.plugin_manager.update_display()
        self.last_update = datetime.now()
        
        try:
            while self.running:
                current_time = datetime.now()
                
                # Check if it's time to update
                if (current_time - self.last_update).total_seconds() >= update_interval:
                    self.logger.info("Performing scheduled update...")
                    
                    try:
                        success = self.plugin_manager.update_display()
                        if success:
                            self.last_update = current_time
                            self.logger.info("Scheduled update completed")
                        else:
                            self.logger.error("Scheduled update failed")
                    
                    except Exception as e:
                        self.logger.error(f"Error during scheduled update: {e}")
                
                # Sleep for 30 seconds before checking again
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("Daemon mode interrupted by user")
        except Exception as e:
            self.logger.error(f"Daemon mode error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the application"""
        self.running = False
        self.logger.info("Stopping eInk InfoDisplay...")
        
        if self.plugin_manager:
            self.plugin_manager.cleanup()
        
        if self.display_manager:
            self.display_manager.cleanup()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting eInk InfoDisplay...")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Config file: {args.config}")
    
    # Create display application
    app = EInkInfoDisplay(args.config, logger)
    
    try:
        if args.clear:
            # Clear display and exit
            success = app.clear_display()
            sys.exit(0 if success else 1)
        
        elif args.test:
            # Test display and exit
            success = app.test_display()
            sys.exit(0 if success else 1)
        
        elif args.daemon:
            # Run in daemon mode
            app.run_daemon(args.update_interval)
        
        else:
            # Single update
            success = app.run_single_update(args.plugin)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        app.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        app.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()