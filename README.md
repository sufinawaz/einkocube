# eInk InfoDisplay

A modular information display system for Pimoroni Inky Impression 7.3" e-ink displays on Raspberry Pi, featuring weather, prayer times, clock, and stock market data with a web-based control interface.

![eInk InfoDisplay Dashboard](https://via.placeholder.com/800x400/2c3e50/ffffff?text=eInk+InfoDisplay+Dashboard)

## Features

- **📺 High-Resolution Display**: Optimized for Pimoroni Inky Impression 7.3" (800x480)
- **🔌 Modular Plugin System**: Easy to add new display modes
- **🌐 Web Interface**: Remote control and configuration via web browser
- **⏰ Multiple Display Modes**:
  - Clock with date and time
  - Weather information and forecasts
  - Islamic prayer times
  - Stock market data
- **🔧 Easy Configuration**: JSON-based configuration with web interface
- **📊 System Monitoring**: Service status, logs, and diagnostics
- **🚀 Systemd Integration**: Runs as a system service

## Hardware Requirements

- Raspberry Pi (3B+ or newer recommended)
- Pimoroni Inky Impression 7.3" e-ink display
- MicroSD card (16GB or larger)
- Reliable power supply
- Internet connection for API data

## Quick Start

### 1. Hardware Setup

1. Connect the Inky Impression display to your Raspberry Pi's GPIO pins
2. Ensure SPI is enabled in `raspi-config`
3. Boot your Raspberry Pi with a fresh Raspberry Pi OS installation

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/sufinawaz/einkocube.git
cd einkocube

# Run the setup script
sudo python3 setup.py
```

The setup script will:
- Install required system packages
- Install Pimoroni Inky libraries
- Configure systemd services
- Create default configuration files
- Set up the web interface

### 3. Configuration

1. Edit the configuration file:
```bash
nano config.json
```

2. Add your API keys:
   - **OpenWeatherMap**: Get from [openweathermap.org](https://openweathermap.org/api)
   - **Finnhub**: Get from [finnhub.io](https://finnhub.io/register) (for stock data)

3. Configure plugin settings:
   - Weather: Set your city ID and units
   - Prayer times: Set your latitude/longitude
   - Stock: Set your preferred stock symbols

### 4. Start the Services

```bash
# Start the display service
sudo systemctl start eink-display

# Start the web interface
sudo systemctl start eink-web

# Enable auto-start on boot
sudo systemctl enable eink-display eink-web
```

### 5. Access the Web Interface

Open your browser and navigate to:
```
http://your-pi-ip-address:8080
```

## Usage

### Command Line Usage

```bash
# Run a specific plugin once
eink-display --plugin clock

# Test the display
eink-display --test

# Clear the display
eink-display --clear

# Run in daemon mode with custom update interval
eink-display --daemon --update-interval 300

# View help
eink-display --help
```

### Web Interface

The web dashboard provides:
- **System Status**: Service status and system information
- **Plugin Control**: Run plugins manually or view their status  
- **Configuration**: Edit settings without editing JSON files
- **Display Controls**: Test and clear the display
- **Logs**: View system logs and troubleshooting information

## Plugin System

### Available Plugins

#### Clock Plugin
- Large digital time display
- Full date with day of week
- 12/24 hour format support
- Timezone information

#### Weather Plugin
- Current conditions and temperature
- Weather description and icons
- Humidity, pressure, wind data
- 24-hour forecast
- Supports metric/imperial units

#### Prayer Plugin
- Five daily prayer times
- Hijri date display
- Next prayer highlighting
- Multiple calculation methods
- Customizable location

#### Stock Plugin
- Real-time stock quotes
- Price changes and percentages
- Market status indication
- Multiple stock symbols
- Daily high/low ranges

### Creating Custom Plugins

1. Create a new file in `src/plugins/`:
```python
# src/plugins/my_plugin.py
from .base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self, config_manager, display_manager, plugin_config=None):
        super().__init__(config_manager, display_manager, plugin_config)
        self.name = "my_plugin"
        self.description = "My custom plugin"
        self.update_interval = 600  # 10 minutes
    
    def render(self):
        # Create image
        image = self.create_image('white')
        draw = self.create_draw(image)
        
        # Draw your content
        self.draw_header(draw, "My Plugin")
        
        # Show the image
        self.show_image(image)
        return True
```

2. Add to enabled plugins in `config.json`:
```json
{
  "plugins": {
    "enabled": ["clock", "weather", "prayer", "stock", "my_plugin"]
  }
}
```

## Configuration Reference

### Display Configuration
```json
{
  "display": {
    "type": "inky_impression",
    "width": 800,
    "height": 480,
    "color": "7color",
    "update_interval": 300,
    "rotation": 0
  }
}
```

### API Keys
```json
{
  "api_keys": {
    "openweathermap": "your_api_key_here",
    "finnhub": "your_finnhub_key_here"
  }
}
```

### Plugin Settings
```json
{
  "plugins": {
    "enabled": ["clock", "weather", "prayer", "stock"],
    "default": "clock",
    "settings": {
      "clock": {
        "show_seconds": false,
        "format_24h": true
      },
      "weather": {
        "city_id": 4791160,
        "units": "imperial",
        "update_interval": 1800
      },
      "prayer": {
        "latitude": 38.903481,
        "longitude": -77.262817,
        "method": 1
      },
      "stock": {
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "update_interval": 1800
      }
    }
  }
}
```

## API Endpoints

The web interface provides REST API endpoints:

- `GET /api/status` - System and plugin status
- `POST /api/plugin/<name>/run` - Run a specific plugin
- `POST /api/service/<action>` - Control system service (start/stop/restart)

Example:
```bash
# Run weather plugin via API
curl -X POST http://your-pi:8080/api/plugin/weather/run

# Get system status
curl http://your-pi:8080/api/status
```

## Troubleshooting

### Common Issues

**Display not updating:**
1. Check SPI is enabled: `sudo raspi-config`
2. Verify connections between Pi and display
3. Check service status: `sudo systemctl status eink-display`
4. View logs: `sudo journalctl -u eink-display -f`

**API errors:**
1. Verify API keys in `config.json`
2. Check internet connectivity
3. Confirm API key permissions and quotas

**Web interface not accessible:**
1. Check if service is running: `sudo systemctl status eink-web`
2. Verify port 8080 is not blocked by firewall
3. Try accessing from Pi directly: `http://localhost:8080`

**Permission errors:**
```bash
# Fix file permissions
sudo chown -R pi:pi /path/to/einkocube
sudo chmod +x run_eink_display
```

### Log Files

- Application logs: `logs/eink_display.log`
- System service logs: `sudo journalctl -u eink-display`
- Web interface logs: `sudo journalctl -u eink-web`

## Development

### Project Structure
```
einkocube/
├── src/
│   ├── display/
│   │   ├── eink_manager.py      # Display hardware interface
│   │   └── plugin_manager.py    # Plugin management
│   ├── plugins/
│   │   ├── base_plugin.py       # Base plugin class
│   │   ├── clock_plugin.py      # Clock plugin
│   │   ├── weather_plugin.py    # Weather plugin
│   │   ├── prayer_plugin.py     # Prayer times plugin
│   │   └── stock_plugin.py      # Stock market plugin
│   ├── config_manager.py        # Configuration management
│   ├── main.py                  # Main application
│   └── web_app.py              # Web interface
├── templates/                   # HTML templates
├── static/                      # CSS/JS assets
├── resources/                   # Images and fonts
├── logs/                       # Log files
├── config.json                 # Main configuration
└── setup.py                    # Installation script
```

### Testing

```bash
# Test display hardware
python3 src/main.py --test

# Test specific plugin
python3 src/main.py --plugin weather

# Run in debug mode
python3 src/main.py --daemon --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Pimoroni](https://pimoroni.com/) for the excellent Inky display libraries
- [OpenWeatherMap](https://openweathermap.org/) for weather data API  
- [Al Adhan API](https://aladhan.com/prayer-times-api) for prayer times
- [Finnhub](https://finnhub.io/) for stock market data

## Support

If you encounter issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search [existing issues](https://github.com/sufinawaz/einkocube/issues)
3. Create a [new issue](https://github.com/sufinawaz/einkocube/issues/new) with:
   - Your hardware setup
   - Error messages or logs
   - Steps to reproduce the problem

---

**Made with ❤️ for the Raspberry Pi and e-ink display community**