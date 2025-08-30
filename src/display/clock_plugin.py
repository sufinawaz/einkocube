#!/usr/bin/env python3
"""
Clock Plugin for eInk InfoDisplay
"""
from datetime import datetime
from .base_plugin import BasePlugin

class ClockPlugin(BasePlugin):
    """Clock plugin showing time and date"""
    
    def __init__(self, config_manager, display_manager, plugin_config=None):
        super().__init__(config_manager, display_manager, plugin_config)
        
        self.name = "clock"
        self.description = "Digital clock with date"
        self.update_interval = 60  # Update every minute
        
    def render(self):
        """Render the clock display"""
        try:
            # Create image
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            # Get current time
            now = datetime.now()
            
            # Draw header
            header_y = self.draw_header(draw, "Clock")
            
            # Draw time (large)
            time_str = self.format_timestamp(now, self.get_config_value('show_seconds', False))
            time_font = self.get_font("bold", 96)
            time_y = header_y + 50
            self.draw_text_centered(draw, time_str, time_y, time_font, 'black')
            
            # Draw date
            date_str = self.format_date(now, 'full')
            date_font = self.get_font("regular", 32)
            date_y = time_y + 120
            self.draw_text_centered(draw, date_str, date_y, date_font, 'blue')
            
            # Draw day of week if not already in date
            day_str = now.strftime("%A")
            day_font = self.get_font("bold", 24)
            day_y = date_y + 50
            self.draw_text_centered(draw, day_str, day_y, day_font, 'green')
            
            # Draw timezone info
            timezone_str = now.strftime("%Z %z")
            if timezone_str.strip():
                self.draw_footer(draw, f"Timezone: {timezone_str}")
            else:
                self.draw_footer(draw, f"Updated: {now.strftime('%H:%M')}")
            
            # Show the image
            self.show_image(image)
            self.log_info(f"Clock updated: {time_str}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to render clock: {e}")
            return False