#!/usr/bin/env python3
"""
Prayer Times Plugin for eInk InfoDisplay
"""
import requests
import logging
from datetime import datetime
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class PrayerPlugin(BasePlugin):
    """Prayer times plugin showing daily prayer schedule"""
    
    def __init__(self, config_manager, display_manager, plugin_config=None):
        super().__init__(config_manager, display_manager, plugin_config)
        
        self.name = "prayer"
        self.description = "Islamic prayer times"
        self.update_interval = self.get_config_value('update_interval', 3600)  # 1 hour
        
        # Prayer data cache
        self.prayer_data = None
        
        # Prayer names in order
        self.prayer_names = [
            ('Fajr', 'Dawn'),
            ('Dhuhr', 'Noon'), 
            ('Asr', 'Afternoon'),
            ('Maghrib', 'Sunset'),
            ('Isha', 'Night')
        ]
    
    def _fetch_prayer_data(self):
        """Fetch prayer times from API"""
        latitude = self.get_config_value('latitude', 38.903481)
        longitude = self.get_config_value('longitude', -77.262817)
        method = self.get_config_value('method', 1)  # 1 = Islamic Society of North America
        
        try:
            url = "http://api.aladhan.com/v1/timings"
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'method': method,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.prayer_data = data.get('data', {})
                self.log_info("Prayer times fetched successfully")
                return True
            else:
                self.log_error(f"Prayer API error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Error fetching prayer data: {e}")
            return False
    
    def _get_next_prayer(self):
        """Determine the next prayer time
        
        Returns:
            Tuple of (prayer_name, prayer_time, is_today)
        """
        if not self.prayer_data:
            return None, None, True
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        timings = self.prayer_data.get('timings', {})
        
        # Check each prayer time
        for prayer_key, display_name in self.prayer_names:
            prayer_time = timings.get(prayer_key, "")
            if prayer_time and prayer_time > current_time:
                return display_name, prayer_time, True
        
        # If all prayers have passed, next is Fajr tomorrow
        return self.prayer_names[0][1], timings.get('Fajr', ''), False
    
    def render(self):
        """Render the prayer times display"""
        try:
            # Fetch fresh data
            if not self._fetch_prayer_data():
                return self._render_error()
            
            # Create image
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            # Get current date info
            now = datetime.now()
            hijri_date = self.prayer_data.get('date', {}).get('hijri', {})
            
            # Draw header
            header_text = "Prayer Times"
            if hijri_date.get('date'):
                header_text += f" - {hijri_date['date']}"
            header_y = self.draw_header(draw, header_text)
            
            # Current date
            date_str = self.format_date(now, 'full')
            date_font = self.get_font("regular", 24)
            date_y = header_y + 10
            self.draw_text_centered(draw, date_str, date_y, date_font, 'blue')
            
            # Prayer times table
            timings = self.prayer_data.get('timings', {})
            table_y = date_y + 60
            
            # Get next prayer info
            next_prayer, next_time, is_today = self._get_next_prayer()
            
            # Table headers
            header_font = self.get_font("bold", 22)
            time_font = self.get_font("regular", 20)
            
            # Column positions
            name_x = 150
            time_x = 450
            
            draw.text((name_x, table_y), "Prayer", font=header_font, fill=self.colors['black'])
            draw.text((time_x, table_y), "Time", font=header_font, fill=self.colors['black'])
            
            # Draw line under headers
            line_y = table_y + 30
            draw.line([(100, line_y), (self.width - 100, line_y)], 
                     fill=self.colors['black'], width=2)
            
            # Draw prayer times
            row_height = 35
            for i, (prayer_key, display_name) in enumerate(self.prayer_names):
                y_pos = line_y + 20 + (i * row_height)
                
                prayer_time = timings.get(prayer_key, "N/A")
                
                # Highlight next prayer
                text_color = 'green' if display_name == next_prayer else 'black'
                font_style = "bold" if display_name == next_prayer else "regular"
                
                prayer_font = self.get_font(font_style, 20)
                time_display_font = self.get_font(font_style, 20)
                
                # Format time for display (convert from 24h to 12h if needed)
                if prayer_time != "N/A":
                    try:
                        time_obj = datetime.strptime(prayer_time, "%H:%M")
                        formatted_time = time_obj.strftime("%I:%M %p").lstrip('0')
                    except:
                        formatted_time = prayer_time
                else:
                    formatted_time = "N/A"
                
                draw.text((name_x, y_pos), display_name, font=prayer_font, 
                         fill=self.colors[text_color])
                draw.text((time_x, y_pos), formatted_time, font=time_display_font, 
                         fill=self.colors[text_color])
            
            # Next prayer info box
            if next_prayer and next_time:
                box_y = line_y + 20 + (len(self.prayer_names) * row_height) + 30
                
                # Draw box background
                box_left = 100
                box_right = self.width - 100
                box_top = box_y
                box_bottom = box_y + 80
                
                draw.rectangle([box_left, box_top, box_right, box_bottom], 
                              outline=self.colors['green'], width=3)
                
                # Next prayer text
                next_font = self.get_font("bold", 24)
                next_text = "Next Prayer:"
                self.draw_text_centered(draw, next_text, box_y + 15, next_font, 'green')
                
                # Prayer name and time
                prayer_info = f"{next_prayer} at {next_time}"
                if not is_today:
                    prayer_info += " (Tomorrow)"
                
                info_font = self.get_font("regular", 22)
                self.draw_text_centered(draw, prayer_info, box_y + 45, info_font, 'black')
            
            # Location info in footer
            location_text = f"Location: {self.get_config_value('latitude', 38.90):.2f}, {self.get_config_value('longitude', -77.26):.2f}"
            self.draw_footer(draw, location_text)
            
            # Show the image
            self.show_image(image)
            self.log_info("Prayer times updated")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to render prayer times: {e}")
            return self._render_error()
    
    def _render_error(self):
        """Render error message"""
        try:
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            self.draw_header(draw, "Prayer Times Error")
            
            error_font = self.get_font("regular", 32)
            self.draw_text_centered(draw, "Unable to fetch prayer times", 
                                  self.height // 2 - 50, error_font, 'red')
            
            self.draw_text_centered(draw, "Please check your internet connection", 
                                  self.height // 2, error_font, 'red')
            
            self.draw_footer(draw, f"Error at: {datetime.now().strftime('%H:%M')}")
            
            self.show_image(image)
            return False
            
        except Exception as e:
            self.log_error(f"Failed to render error message: {e}")
            return False