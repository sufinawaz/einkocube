#!/usr/bin/env python3
"""
Web Interface for eInk InfoDisplay
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.config_manager import ConfigManager
from src.display.plugin_manager import PluginManager
from src.display.eink_manager import EInkDisplayManager

# Flask app setup
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Template and static folders
app.template_folder = str(project_root / "templates")
app.static_folder = str(project_root / "static")

# Global instances
config_manager = None
plugin_manager = None
display_manager = None

def initialize_managers():
    """Initialize the manager instances"""
    global config_manager, plugin_manager, display_manager
    
    try:
        config_path = project_root / "config.json"
        config_manager = ConfigManager(str(config_path))
        
        display_manager = EInkDisplayManager(config_manager)
        plugin_manager = PluginManager(config_manager, display_manager)
        
        return True
    except Exception as e:
        app.logger.error(f"Failed to initialize managers: {e}")
        return False

def get_service_status():
    """Get the status of the eInk display service"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "eink-display.service"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False

def get_service_logs(lines=20):
    """Get recent service logs"""
    try:
        result = subprocess.run(
            ["journalctl", "-u", "eink-display.service", "-n", str(lines), "--no-pager"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.split('\n')
    except Exception as e:
        return [f"Error getting logs: {e}"]

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Initialize if needed
        if not config_manager:
            initialize_managers()
        
        # Get system status
        service_status = get_service_status()
        
        # Get plugin status
        plugin_status = {}
        if plugin_manager:
            plugin_status = plugin_manager.get_plugin_status()
        
        # Get last update times from logs
        logs = get_service_logs(10)
        last_update = None
        for log in logs:
            if "updated" in log.lower():
                try:
                    # Try to extract timestamp
                    parts = log.split()
                    if len(parts) >= 3:
                        timestamp_str = f"{parts[0]} {parts[1]} {parts[2]}"
                        last_update = timestamp_str
                        break
                except:
                    continue
        
        return render_template('index.html',
                             service_active=service_status,
                             plugins=plugin_status,
                             last_update=last_update,
                             current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    except Exception as e:
        app.logger.error(f"Error in index route: {e}")
        flash(f"Error loading dashboard: {e}", "error")
        return render_template('error.html', error=str(e))

@app.route('/plugin/<plugin_name>')
def run_plugin(plugin_name):
    """Run a specific plugin"""
    try:
        if not plugin_manager:
            initialize_managers()
        
        if plugin_name not in plugin_manager.get_available_plugins():
            flash(f"Plugin '{plugin_name}' not found", "error")
            return redirect(url_for('index'))
        
        # Run the plugin
        success = plugin_manager.run_plugin(plugin_name, force_update=True)
        
        if success:
            flash(f"Plugin '{plugin_name}' executed successfully", "success")
        else:
            flash(f"Plugin '{plugin_name}' failed to execute", "error")
        
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Error running plugin {plugin_name}: {e}")
        flash(f"Error running plugin: {e}", "error")
        return redirect(url_for('index'))

@app.route('/service/<action>')
def service_control(action):
    """Control the eInk display service"""
    try:
        if action not in ['start', 'stop', 'restart']:
            flash("Invalid service action", "error")
            return redirect(url_for('index'))
        
        # Execute systemctl command
        result = subprocess.run(
            ["sudo", "systemctl", action, "eink-display.service"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            flash(f"Service {action} successful", "success")
        else:
            flash(f"Service {action} failed: {result.stderr}", "error")
        
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Error controlling service: {e}")
        flash(f"Error controlling service: {e}", "error")
        return redirect(url_for('index'))

@app.route('/config')
def config_page():
    """Configuration page"""
    try:
        if not config_manager:
            initialize_managers()
        
        config_data = config_manager.get_all_config()
        return render_template('config.html', config=config_data)
    
    except Exception as e:
        app.logger.error(f"Error in config route: {e}")
        flash(f"Error loading configuration: {e}", "error")
        return redirect(url_for('index'))

@app.route('/config/save', methods=['POST'])
def save_config():
    """Save configuration changes"""
    try:
        if not config_manager:
            initialize_managers()
        
        # Get form data
        form_data = request.form.to_dict()
        
        # Update API keys
        api_keys = {}
        for key in ['openweathermap', 'finnhub']:
            if f'api_key_{key}' in form_data:
                value = form_data[f'api_key_{key}'].strip()
                if value:
                    api_keys[key] = value
        
        if api_keys:
            config_manager.update_section('api_keys', api_keys)
        
        # Update plugin settings
        plugin_settings = {}
        
        # Clock plugin
        if 'clock_format_24h' in form_data:
            plugin_settings['clock'] = {
                'format_24h': form_data['clock_format_24h'] == 'true',
                'show_seconds': form_data.get('clock_show_seconds') == 'true'
            }
        
        # Weather plugin
        weather_settings = {}
        if 'weather_city_id' in form_data:
            try:
                weather_settings['city_id'] = int(form_data['weather_city_id'])
            except ValueError:
                pass
        if 'weather_units' in form_data:
            weather_settings['units'] = form_data['weather_units']
        if 'weather_update_interval' in form_data:
            try:
                weather_settings['update_interval'] = int(form_data['weather_update_interval'])
            except ValueError:
                pass
        
        if weather_settings:
            plugin_settings['weather'] = weather_settings
        
        # Prayer plugin
        prayer_settings = {}
        if 'prayer_latitude' in form_data:
            try:
                prayer_settings['latitude'] = float(form_data['prayer_latitude'])
            except ValueError:
                pass
        if 'prayer_longitude' in form_data:
            try:
                prayer_settings['longitude'] = float(form_data['prayer_longitude'])
            except ValueError:
                pass
        if 'prayer_method' in form_data:
            try:
                prayer_settings['method'] = int(form_data['prayer_method'])
            except ValueError:
                pass
        
        if prayer_settings:
            plugin_settings['prayer'] = prayer_settings
        
        # Stock plugin
        stock_settings = {}
        if 'stock_symbols' in form_data:
            symbols = [s.strip().upper() for s in form_data['stock_symbols'].split(',') if s.strip()]
            if symbols:
                stock_settings['symbols'] = symbols
        if 'stock_update_interval' in form_data:
            try:
                stock_settings['update_interval'] = int(form_data['stock_update_interval'])
            except ValueError:
                pass
        
        if stock_settings:
            plugin_settings['stock'] = stock_settings
        
        # Save plugin settings
        if plugin_settings:
            current_plugins = config_manager.get('plugins', {})
            current_settings = current_plugins.get('settings', {})
            
            for plugin_name, settings in plugin_settings.items():
                if plugin_name in current_settings:
                    current_settings[plugin_name].update(settings)
                else:
                    current_settings[plugin_name] = settings
            
            current_plugins['settings'] = current_settings
            config_manager.update_section('plugins', current_plugins)
        
        # Save configuration
        config_manager.save_config()
        
        flash("Configuration saved successfully", "success")
        return redirect(url_for('config_page'))
    
    except Exception as e:
        app.logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {e}", "error")
        return redirect(url_for('config_page'))

@app.route('/logs')
def logs_page():
    """View system logs"""
    try:
        lines = request.args.get('lines', 50, type=int)
        logs = get_service_logs(lines)
        
        return render_template('logs.html', logs=logs, lines=lines)
    
    except Exception as e:
        app.logger.error(f"Error in logs route: {e}")
        flash(f"Error loading logs: {e}", "error")
        return redirect(url_for('index'))

@app.route('/test')
def test_display():
    """Test the display"""
    try:
        if not display_manager:
            initialize_managers()
        
        success = display_manager.test_display()
        
        if success:
            flash("Display test completed successfully", "success")
        else:
            flash("Display test failed", "error")
        
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Error testing display: {e}")
        flash(f"Error testing display: {e}", "error")
        return redirect(url_for('index'))

@app.route('/clear')
def clear_display():
    """Clear the display"""
    try:
        if not display_manager:
            initialize_managers()
        
        display_manager.clear()
        flash("Display cleared", "success")
        return redirect(url_for('index'))
    
    except Exception as e:
        app.logger.error(f"Error clearing display: {e}")
        flash(f"Error clearing display: {e}", "error")
        return redirect(url_for('index'))

# API Routes
@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    try:
        status = {
            'service_active': get_service_status(),
            'plugins': plugin_manager.get_plugin_status() if plugin_manager else {},
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/plugin/<plugin_name>/run', methods=['POST'])
def api_run_plugin(plugin_name):
    """API endpoint to run a plugin"""
    try:
        if not plugin_manager:
            initialize_managers()
        
        success = plugin_manager.run_plugin(plugin_name, force_update=True)
        
        return jsonify({
            'success': success,
            'message': f"Plugin {plugin_name} {'executed successfully' if success else 'failed'}"
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/<action>', methods=['POST'])
def api_service_control(action):
    """API endpoint for service control"""
    try:
        if action not in ['start', 'stop', 'restart']:
            return jsonify({'error': 'Invalid action'}), 400
        
        result = subprocess.run(
            ["sudo", "systemctl", action, "eink-display.service"],
            capture_output=True, text=True, timeout=30
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'message': f"Service {action} {'successful' if result.returncode == 0 else 'failed'}",
            'output': result.stdout,
            'error': result.stderr
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """Main entry point for web application"""
    # Initialize managers
    if not initialize_managers():
        print("Warning: Could not initialize all managers")
    
    # Get web configuration
    web_config = config_manager.get('web', {}) if config_manager else {}
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 8080)
    debug = web_config.get('debug', False)
    
    print(f"Starting eInk InfoDisplay Web Interface...")
    print(f"Access at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nWeb interface stopped by user")
    except Exception as e:
        print(f"Error starting web interface: {e}")

if __name__ == '__main__':
    main()