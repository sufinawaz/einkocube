#!/usr/bin/env python3
"""
Weather Plugin for eInk InfoDisplay
"""
import requests
import logging
from datetime import datetime
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class WeatherPlugin(BasePlugin):
    """Weather plugin showing current conditions and forecast"""
    
    def __init__(self, config_manager, display_manager, plugin_config=None):
        super().__init__(config_manager, display_manager, plugin_config)
        
        self.name = "weather"
        self.description = "Current weather and forecast"
        self.update_interval = self.get_config_value('update_interval', 1800)  # 30 minutes
        
        # Weather data cache
        self.weather_data = None
        self.forecast_data = None
        
    def _fetch_weather_data(self):
        """Fetch weather data from OpenWeatherMap API"""
        api_key = self.config.get("api_keys", {}).get("openweathermap", "")
        if not api_key:
            self.log_error("No OpenWeatherMap API key configured")
            return False
        
        city_id = self.get_config_value('city_id', 4791160)  # Default: Washington, DC
        units = self.get_config_value('units', 'imperial')
        
        try:
            # Fetch current weather
            current_url = "https://api.openweathermap.org/data/2.5/weather"
            current_params = {
                'id': city_id,
                'appid': api_key,
                'units': units
            }
            
            response = requests.get(current_url, params=current_params, timeout=10)
            if response.status_code == 200:
                self.weather_data = response.json()
                self.log_info("Weather data fetched successfully")
            else:
                self.log_error(f"Weather API error: {response.status_code}")
                return False
            
            # Fetch 5-day forecast
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                'id': city_id,
                'appid': api_key,
                'units': units,
                'cnt': 8  # Next 24 hours (8 x 3-hour periods)
            }
            
            response = requests.get(forecast_url, params=forecast_params, timeout=10)
            if response.status_code == 200:
                self.forecast_data = response.json()
                self.log_info("Forecast data fetched successfully")
            else:
                self.log_warning(f"Forecast API error: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error fetching weather data: {e}")
            return False
    
    def render(self):
        """Render the weather display"""
        try:
            # Fetch fresh data
            if not self._fetch_weather_data():
                return self._render_error()
            
            # Create image
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            # Get units symbol
            units = self.get_config_value('units', 'imperial')
            temp_unit = '°F' if units == 'imperial' else '°C'
            speed_unit = 'mph' if units == 'imperial' else 'm/s'
            
            # Draw header with city name
            city_name = self.weather_data.get('name', 'Unknown')
            header_y = self.draw_header(draw, f"Weather - {city_name}")
            
            # Current weather section
            current_y = header_y + 20
            
            # Main temperature (large)
            temp = self.weather_data['main']['temp']
            temp_str = f"{temp:.0f}{temp_unit}"
            temp_font = self.get_font("bold", 72)
            self.draw_text_centered(draw, temp_str, current_y, temp_font, 'red')
            
            # Weather description
            description = self.weather_data['weather'][0]['description'].title()
            desc_font = self.get_font("regular", 28)
            desc_y = current_y + 90
            self.draw_text_centered(draw, description, desc_y, desc_font, 'blue')
            
            # Additional details in two columns
            details_y = desc_y + 50
            left_x = 80
            right_x = self.width // 2 + 40
            detail_font = self.get_font("regular", 20)
            
            # Left column
            feels_like = f"Feels like: {self.weather_data['main']['feels_like']:.0f}{temp_unit}"
            draw.text((left_x, details_y), feels_like, font=detail_font, fill=self.colors['black'])
            
            humidity = f"Humidity: {self.weather_data['main']['humidity']}%"
            draw.text((left_x, details_y + 30), humidity, font=detail_font, fill=self.colors['black'])
            
            pressure = f"Pressure: {self.weather_data['main']['pressure']} hPa"
            draw.text((left_x, details_y + 60), pressure, font=detail_font, fill=self.colors['black'])
            
            # Right column
            wind = self.weather_data.get('wind', {})
            wind_speed = wind.get('speed', 0)
            wind_dir = wind.get('deg', 0)
            wind_str = f"Wind: {wind_speed:.0f} {speed_unit}"
            draw.text((right_x, details_y), wind_str, font=detail_font, fill=self.colors['black'])
            
            wind_dir_str = self._wind_direction(wind_dir)
            draw.text((right_x, details_y + 30), f"Direction: {wind_dir_str}", font=detail_font, fill=self.colors['black'])
            
            visibility = self.weather_data.get('visibility', 0) / 1000  # Convert to km
            if units == 'imperial':
                visibility *= 0.621371  # Convert to miles
                vis_unit = 'mi'
            else:
                vis_unit = 'km'
            draw.text((right_x, details_y + 60), f"Visibility: {visibility:.1f} {vis_unit}", 
                     font=detail_font, fill=self.colors['black'])
            
            # Forecast section (if available)
            if self.forecast_data and len(self.forecast_data.get('list', [])) > 0:
                forecast_y = details_y + 120
                
                # Forecast header
                forecast_font = self.get_font("bold", 24)
                draw.text((50, forecast_y), "Next 24 Hours:", font=forecast_font, fill=self.colors['green'])
                
                # Show next few forecasts
                forecast_items = self.forecast_data['list'][:4]  # Next 4 periods (12 hours)
                forecast_detail_font = self.get_font("regular", 18)
                
                for i, forecast in enumerate(forecast_items):
                    y_pos = forecast_y + 35 + (i * 25)
                    
                    # Time
                    forecast_time = datetime.fromtimestamp(forecast['dt'])
                    time_str = forecast_time.strftime("%H:%M")
                    
                    # Temperature and description
                    temp_forecast = f"{forecast['main']['temp']:.0f}{temp_unit}"
                    desc_forecast = forecast['weather'][0]['main']
                    
                    forecast_line = f"{time_str}: {temp_forecast}, {desc_forecast}"
                    draw.text((70, y_pos), forecast_line, font=forecast_detail_font, fill=self.colors['black'])
            
            # Footer with update time
            update_time = datetime.now().strftime("%H:%M")
            self.draw_footer(draw, f"Updated: {update_time}")
            
            # Show the image
            self.show_image(image)
            self.log_info(f"Weather updated for {city_name}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to render weather: {e}")
            return self._render_error()
    
    def _render_error(self):
        """Render error message"""
        try:
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            self.draw_header(draw, "Weather Error")
            
            error_font = self.get_font("regular", 32)
            self.draw_text_centered(draw, "Unable to fetch weather data", 
                                  self.height // 2 - 50, error_font, 'red')
            
            self.draw_text_centered(draw, "Please check your API key and connection", 
                                  self.height // 2, error_font, 'red')
            
            self.draw_footer(draw, f"Error at: {datetime.now().strftime('%H:%M')}")
            
            self.show_image(image)
            return False
            
        except Exception as e:
            self.log_error(f"Failed to render error message: {e}")
            return False
    
    def _wind_direction(self, degrees):
        """Convert wind direction degrees to compass direction
        
        Args:
            degrees: Wind direction in degrees
            
        Returns:
            Compass direction string
        """
        if degrees is None:
            return "N/A"
        
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        
        index = round(degrees / 22.5) % 16
        return directions[index]