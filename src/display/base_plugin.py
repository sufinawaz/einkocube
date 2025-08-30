#!/usr/bin/env python3
"""
Base Plugin Class for eInk InfoDisplay
"""
from abc import ABC, abstractmethod
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """Base class for all display plugins"""
    
    def __init__(self, config_manager, display_manager, plugin_config=None):
        """Initialize the plugin
        
        Args:
            config_manager: ConfigManager instance
            display_manager: EInkDisplayManager instance  
            plugin_config: Plugin-specific configuration
        """
        self.config = config_manager
        self.display = display_manager
        self.plugin_config = plugin_config or {}
        
        # Plugin metadata
        self.name = "base"
        self.description = "Base plugin class"
        self.update_interval = 300  # 5 minutes default
        
        # Display properties
        self.width, self.height = self.display.get_dimensions()
        self.colors = self.display.colors
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        # Plugin initialization
        self.setup()
    
    def _load_fonts(self):
        """Load fonts for the plugin
        
        Returns:
            Dictionary of fonts
        """
        try:
            return self.display.get_fonts()
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            return {"default_24": ImageFont.load_default()}
    
    def setup(self):
        """Plugin-specific setup (override in subclasses)"""
        pass
    
    @abstractmethod
    def render(self):
        """Render the plugin content to the display
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def create_image(self, background_color='white'):
        """Create a new image for the plugin
        
        Args:
            background_color: Background color
            
        Returns:
            PIL Image object
        """
        return self.display.create_image(background_color)
    
    def create_draw(self, image):
        """Create a drawing context for the image
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL ImageDraw object
        """
        return self.display.create_draw(image)
    
    def show_image(self, image):
        """Display an image on the screen
        
        Args:
            image: PIL Image object to display
        """
        self.display.show_image(image)
    
    def get_font(self, font_name="regular", size=24):
        """Get a font object
        
        Args:
            font_name: Font style name
            size: Font size
            
        Returns:
            PIL Font object
        """
        font_key = f"{font_name}_{size}"
        return self.fonts.get(font_key, self.fonts.get(f"default_{size}", ImageFont.load_default()))
    
    def draw_text_centered(self, draw, text, y_position, font=None, color='black'):
        """Draw text centered horizontally
        
        Args:
            draw: PIL ImageDraw object
            text: Text to draw
            y_position: Y coordinate
            font: Font object (optional)
            color: Text color
        """
        if font is None:
            font = self.get_font()
        
        # Get text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        except (AttributeError, TypeError):
            text_width = draw.textsize(text, font=font)[0]
        
        x_position = (self.width - text_width) // 2
        color_value = self.colors.get(color, color) if isinstance(color, str) else color
        
        draw.text((x_position, y_position), text, font=font, fill=color_value)
        
        return x_position, y_position
    
    def draw_text_right_aligned(self, draw, text, x_right, y_position, font=None, color='black'):
        """Draw text right-aligned
        
        Args:
            draw: PIL ImageDraw object
            text: Text to draw
            x_right: Right edge X coordinate
            y_position: Y coordinate
            font: Font object (optional)
            color: Text color
        """
        if font is None:
            font = self.get_font()
        
        # Get text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        except (AttributeError, TypeError):
            text_width = draw.textsize(text, font=font)[0]
        
        x_position = x_right - text_width
        color_value = self.colors.get(color, color) if isinstance(color, str) else color
        
        draw.text((x_position, y_position), text, font=font, fill=color_value)
        
        return x_position, y_position
    
    def draw_header(self, draw, title, font_size=32):
        """Draw a header at the top of the screen
        
        Args:
            draw: PIL ImageDraw object
            title: Header title
            font_size: Font size for header
        """
        header_font = self.get_font("bold", font_size)
        self.draw_text_centered(draw, title, 20, header_font, 'black')
        
        # Draw a line under the header
        line_y = 20 + font_size + 10
        draw.line([(50, line_y), (self.width - 50, line_y)], fill=self.colors['black'], width=2)
        
        return line_y + 20  # Return Y position after header
    
    def draw_footer(self, draw, text, font_size=16):
        """Draw a footer at the bottom of the screen
        
        Args:
            draw: PIL ImageDraw object
            text: Footer text
            font_size: Font size for footer
        """
        footer_font = self.get_font("regular", font_size)
        footer_y = self.height - font_size - 20
        self.draw_text_centered(draw, text, footer_y, footer_font, 'black')
        
        return footer_y
    
    def format_timestamp(self, dt=None, include_seconds=False):
        """Format a timestamp for display
        
        Args:
            dt: datetime object (current time if None)
            include_seconds: Include seconds in format
            
        Returns:
            Formatted time string
        """
        if dt is None:
            dt = datetime.now()
        
        format_24h = self.plugin_config.get('format_24h', True)
        
        if format_24h:
            if include_seconds:
                return dt.strftime("%H:%M:%S")
            else:
                return dt.strftime("%H:%M")
        else:
            if include_seconds:
                return dt.strftime("%I:%M:%S %p")
            else:
                return dt.strftime("%I:%M %p")
    
    def format_date(self, dt=None, format_style='full'):
        """Format a date for display
        
        Args:
            dt: datetime object (current date if None)
            format_style: 'full', 'short', or 'day'
            
        Returns:
            Formatted date string
        """
        if dt is None:
            dt = datetime.now()
        
        if format_style == 'full':
            return dt.strftime("%A, %B %d, %Y")
        elif format_style == 'short':
            return dt.strftime("%m/%d/%Y")
        elif format_style == 'day':
            return dt.strftime("%A")
        else:
            return dt.strftime("%Y-%m-%d")
    
    def cleanup(self):
        """Clean up plugin resources (override in subclasses if needed)"""
        pass
    
    def get_config_value(self, key, default=None):
        """Get a configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.plugin_config.get(key, default)
    
    def log_info(self, message):
        """Log an info message with plugin name"""
        logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message):
        """Log an error message with plugin name"""
        logger.error(f"[{self.name}] {message}")
    
    def log_warning(self, message):
        """Log a warning message with plugin name"""
        logger.warning(f"[{self.name}] {message}")