#!/usr/bin/env python3
"""
Setup script for eInk InfoDisplay using Pimoroni Inky Impression 7.3"
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def print_header(message):
    """Print a formatted header message"""
    logger.info("\n" + "=" * 60)
    logger.info(f" {message}")
    logger.info("=" * 60)

def run_command(command, cwd=None, shell=False):
    """Run a shell command and log output"""
    logger.info(f"Running: {command}")
    if not shell and isinstance(command, str):
        command = command.split()

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            shell=shell
        )

        for line in iter(process.stdout.readline, ''):
            line = line.rstrip()
            if line:
                logger.info(f"  {line}")

        process.wait()
        return process.returncode
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1

def create_directory(directory):
    """Create a directory if it doesn't exist"""
    try:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

def create_project_structure():
    """Create the project directory structure"""
    print_header("Setting up project structure")

    project_root = os.path.abspath(os.path.dirname(__file__))
    
    directories = [
        "src",
        "src/plugins",
        "src/display",
        "src/web",
        "resources",
        "resources/fonts",
        "resources/images",
        "templates",
        "static",
        "static/css",
        "static/js",
        "logs"
    ]

    for directory in directories:
        create_directory(os.path.join(project_root, directory))

    return project_root

def install_system_packages():
    """Install required system packages"""
    print_header("Installing system packages")

    packages = [
        "python3-dev",
        "python3-pip",
        "python3-pil",
        "python3-numpy",
        "python3-requests",
        "python3-flask",
        "libfreetype6-dev",
        "libjpeg-dev",
        "build-essential",
        "libopenjp2-7",
        "libtiff5",
        "fonts-dejavu-core"
    ]

    # Update package list
    if run_command(["sudo", "apt-get", "update"]) != 0:
        logger.error("Failed to update package list")
        return False

    # Install packages
    apt_command = ["sudo", "apt-get", "install", "-y"] + packages
    if run_command(apt_command) != 0:
        logger.error("Failed to install system packages")
        return False

    return True

def install_pimoroni_libraries():
    """Install Pimoroni Inky libraries"""
    print_header("Installing Pimoroni Inky libraries")

    # Install the inky library
    pip_packages = [
        "inky[rpi,fonts]==1.5.0",
        "pillow>=8.0.0",
        "requests>=2.25.0",
        "flask>=2.0.0",
        "numpy>=1.19.0"
    ]

    for package in pip_packages:
        logger.info(f"Installing {package}")
        if run_command([sys.executable, "-m", "pip", "install", package]) != 0:
            logger.error(f"Failed to install {package}")
            return False

    return True

def enable_spi():
    """Enable SPI interface"""
    print_header("Enabling SPI interface")

    # Check if SPI is already enabled
    try:
        with open('/boot/config.txt', 'r') as f:
            content = f.read()
            if 'dtparam=spi=on' in content and not content.count('dtparam=spi=on') > 1:
                logger.info("SPI is already enabled")
                return True
    except FileNotFoundError:
        # Try the new boot config location
        try:
            with open('/boot/firmware/config.txt', 'r') as f:
                content = f.read()
                if 'dtparam=spi=on' in content:
                    logger.info("SPI is already enabled")
                    return True
        except FileNotFoundError:
            pass

    # Enable SPI using raspi-config
    logger.info("Enabling SPI interface")
    if run_command(["sudo", "raspi-config", "nonint", "do_spi", "0"]) != 0:
        logger.warning("Failed to enable SPI automatically")
        logger.info("Please manually enable SPI using 'sudo raspi-config'")
        logger.info("Go to: Interfacing Options -> SPI -> Yes")

    return True

def create_config_file(project_root):
    """Create configuration file"""
    print_header("Creating configuration file")

    config_content = """{
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
        "aladhan": ""
    },
    "plugins": {
        "enabled": ["clock", "weather", "prayer", "stock"],
        "default": "clock",
        "settings": {
            "clock": {
                "show_seconds": false,
                "format_24h": true,
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
        "debug": false
    }
}"""

    config_path = os.path.join(project_root, "config.json")
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created config file at {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create config file: {e}")
        return False

def create_systemd_services(project_root):
    """Create systemd service files"""
    print_header("Creating systemd services")

    # Main display service
    display_service = f"""[Unit]
Description=eInk InfoDisplay
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory={project_root}
ExecStart=/usr/bin/python3 {project_root}/src/main.py
Environment=PYTHONPATH={project_root}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    # Web interface service
    web_service = f"""[Unit]
Description=eInk InfoDisplay Web Interface
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory={project_root}
ExecStart=/usr/bin/python3 {project_root}/src/web_app.py
Environment=PYTHONPATH={project_root}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    # Write service files
    services = [
        ("/tmp/eink-display.service", display_service),
        ("/tmp/eink-web.service", web_service)
    ]

    for temp_path, content in services:
        try:
            with open(temp_path, 'w') as f:
                f.write(content)
            
            service_name = os.path.basename(temp_path)
            system_path = f"/etc/systemd/system/{service_name}"
            
            if run_command(["sudo", "cp", temp_path, system_path]) != 0:
                logger.error(f"Failed to install {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create service file: {e}")
            return False

    # Reload systemd and enable services
    if run_command(["sudo", "systemctl", "daemon-reload"]) != 0:
        logger.error("Failed to reload systemd")
        return False

    for service in ["eink-display.service", "eink-web.service"]:
        if run_command(["sudo", "systemctl", "enable", service]) != 0:
            logger.error(f"Failed to enable {service}")
            return False

    logger.info("Services created and enabled successfully")
    return True

def create_launcher_script(project_root):
    """Create launcher script"""
    print_header("Creating launcher script")

    launcher_content = f"""#!/bin/bash
# eInk InfoDisplay Launcher

PROJECT_ROOT="{project_root}"
cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Check if running as root (not recommended for eInk)
if [ "$EUID" -eq 0 ]; then
    echo "Warning: Running as root. Consider running as 'pi' user instead."
fi

# Run the main application
python3 "$PROJECT_ROOT/src/main.py" "$@"
"""

    launcher_path = os.path.join(project_root, "run_eink_display")
    
    try:
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        os.chmod(launcher_path, 0o755)
        logger.info(f"Created launcher script at {launcher_path}")

        # Create global symlink
        if run_command(["sudo", "ln", "-sf", launcher_path, "/usr/local/bin/eink-display"]) == 0:
            logger.info("Created global command 'eink-display'")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create launcher script: {e}")
        return False

def main():
    """Main setup function"""
    print_header("eInk InfoDisplay Setup for Pimoroni Inky Impression 7.3\"")

    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' not in cpuinfo and 'BCM' not in cpuinfo:
                logger.warning("This doesn't appear to be a Raspberry Pi")
                cont = input("Continue anyway? (y/n): ").lower()
                if cont != 'y':
                    return False
    except FileNotFoundError:
        logger.warning("Cannot detect Raspberry Pi")

    # Create project structure
    project_root = create_project_structure()

    # Install system packages
    if not install_system_packages():
        logger.error("Failed to install system packages")
        return False

    # Install Pimoroni libraries
    if not install_pimoroni_libraries():
        logger.error("Failed to install Pimoroni libraries")
        return False

    # Enable SPI
    enable_spi()

    # Create config file
    if not create_config_file(project_root):
        return False

    # Create systemd services
    if not create_systemd_services(project_root):
        return False

    # Create launcher script
    if not create_launcher_script(project_root):
        return False

    print_header("Setup Complete!")
    logger.info("eInk InfoDisplay has been set up successfully!")
    logger.info(f"Project directory: {project_root}")
    logger.info("\nNext steps:")
    logger.info("1. Add your API keys to config.json")
    logger.info("2. Test the display: eink-display --test")
    logger.info("3. Start the services:")
    logger.info("   sudo systemctl start eink-display")
    logger.info("   sudo systemctl start eink-web")
    logger.info("4. Access web interface at: http://YOUR_PI_IP:8080")
    logger.info("\nNote: eInk displays update slowly - be patient!")

    return True

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)