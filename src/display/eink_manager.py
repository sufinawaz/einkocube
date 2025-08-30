#!/usr/bin/env python3
"""
eInk Display Manager for Pimoroni Inky Impression 7.3"
"""
import logging
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

logger = logging.getLogger(__name__)

class EInkDisplayManager:
    """Manages the eInk display hardware"""
    
    def __init__(self, config_manager):
        """Initialize the eInk display manager
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.display = None
        self.width = 800
        self.height = 480
        self.color_mode = "7color"  # Inky Impression 7-color
        self.rotation = 0
        
        # Get display config
        display_config = self.config.get_section("display", {})
        self.width = display_config.get("width", 800)
        self.height = display_config.get("height", 480)
        self.color_mode = display_config.get("color", "7color")
        self.rotation = display_config.get("rotation", 0)
        
        # Initialize display
        self._initialize_display()
        
        # Color palette for 7-color display
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'orange': (255, 165, 0),
            'yellow': (255, 255, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'clean': (255, 255, 255)  # Clean/clear color
        }
        
        # Inky palette mapping
        self.inky_palette = [
            0,   # Black
            1,   # White  
            2,   # Green
            3,   # Blue
            4,   # Red
            5,   # Yellow
            6,   # Orange
            7    # Clean
        ]
        
    def _initialize_display(self):
        """Initialize the Inky display"""
        try:
            from inky.auto import auto
            
            # Auto-detect the display
            self.display = auto()
            logger.info(f"Detected display: {type(self.display).__name__}")
            logger.info(f"Display resolution: {self.display.width}x{self.display.height}")
            
            # Update dimensions from detected display
            self.width = self.display.width
            self.height = self.display.height
            
            # Set rotation if specified
            if self.rotation:
                self.display.set_rotation(self.rotation)
                logger.info(f"Display rotation set to: {self.rotation}")
                
        except ImportError as e:
            logger.error("Inky library not found. Please install with: pip install inky[rpi,fonts]")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            # Create a dummy display for testing
            logger.warning("Creating dummy display for testing")
            self.display = None
    
    def create_image(self, background_color='white'):
        """Create a new PIL image for the display
        
        Args:
            background_color: Background color name
            
        Returns:
            PIL Image object
        """
        bg_color = self.colors.get(background_color, self.colors['white'])
        return Image.new('RGB', (self.width, self.height), bg_color)
    
    def create_draw(self, image):
        """Create a PIL ImageDraw object
        
        Args:
            image: PIL Image object
            
        Returns:
            PIL ImageDraw object
        """
        return ImageDraw.Draw(image)
    
    def show_image(self, image):
        """Display an image on the eInk screen
        
        Args:
            image: PIL Image object to display
        """
        if self.display is None:
            logger.warning("No display available - saving image for testing")
            image.save(f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            return
        
        try:
            # Convert image if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if necessary
            if image.size != (self.width, self.height):
                logger.info(f"Resizing image from {image.size} to {self.width}x{self.height}")
                image = image.resize((self.width, self.height), Image.LANCZOS)
            
            # Set the image on the display
            logger.info("Updating eInk display...")
            start_time = time.time()
            
            self.display.set_image(image)
            self.display.show()
            
            end_time = time.time()
            logger.info(f"Display update completed in {end_time - start_time:.1f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to show image: {e}")
            raise
    
    def clear(self, color='white'):
        """Clear the display
        
        Args:
            color: Color to clear with
        """
        logger.info(f"Clearing display with {color}")
        clear_image = self.create_image(color)
        self.show_image(clear_image)
    
    def test_display(self):
        """Test the display with sample content"""
        logger.info("Running display test...")
        
        # Create test image
        image = self.create_image('white')
        draw = self.create_draw(image)
        
        # Draw title
        try:
            # Try to load a font
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except Exception:
            # Fallback to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Title
        draw.text((50, 50), "eInk InfoDisplay", font=font_large, fill=self.colors['black'])
        
        # Subtitle
        draw.text((50, 120), "Pimoroni Inky Impression 7.3\"", font=font_medium, fill=self.colors['red'])
        
        # Info
        draw.text((50, 180), f"Resolution: {self.width}x{self.height}", font=font_small, fill=self.colors['blue'])
        draw.text((50, 220), f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                 font=font_small, fill=self.colors['green'])
        
        # Color test squares
        colors_test = [
            ('Black', self.colors['black']),
            ('Red', self.colors['red']),
            ('Orange', self.colors['orange']),
            ('Yellow', self.colors['yellow']),
            ('Green', self.colors['green']),
            ('Blue', self.colors['blue'])
        ]
        
        y_pos = 280
        for i, (name, color) in enumerate(colors_test):
            x_pos = 50 + i * 120
            # Draw colored square
            draw.rectangle([x_pos, y_pos, x_pos + 60, y_pos + 60], fill=color)
            # Label
            draw.text((x_pos, y_pos + 70), name, font=font_small, fill=self.colors['black'])
        
        # Display the test image
        self.show_image(image)
    
    def get_dimensions(self):
        """Get display dimensions
        
        Returns:
            Tuple of (width, height)
        """
        return (self.width, self.height)
    
    def get_fonts(self):
        """Get available fonts
        
        Returns:
            Dictionary of font names and font objects
        """
        fonts = {}
        
        font_paths = [
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "bold"),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "regular"),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "mono")
        ]
        
        sizes = [16, 20, 24, 32, 48, 64]
        
        for font_path, font_name in font_paths:
            try:
                for size in sizes:
                    key = f"{font_name}_{size}"
                    fonts[key] = ImageFont.truetype(font_path, size)
            except Exception as e:
                logger.warning(f"Could not load font {font_path}: {e}")
        
        # Always provide defaults
        if not fonts:
            for size in sizes:
                fonts[f"default_{size}"] = ImageFont.load_default()
        
        return fonts
    
    def cleanup(self):
        """Clean up display resources"""
        logger.info("Cleaning up display manager...")
        # eInk displays don't need special cleanup, but we can clear if desired
        pass