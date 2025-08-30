#!/usr/bin/env python3
"""
Stock Market Plugin for eInk InfoDisplay
"""
import requests
import logging
from datetime import datetime
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)

class StockPlugin(BasePlugin):
    """Stock market plugin showing current prices and changes"""
    
    def __init__(self, config_manager, display_manager, plugin_config=None):
        super().__init__(config_manager, display_manager, plugin_config)
        
        self.name = "stock"
        self.description = "Stock market quotes"
        self.update_interval = self.get_config_value('update_interval', 1800)  # 30 minutes
        
        # Stock data cache
        self.stock_data = {}
        
    def _fetch_stock_data(self):
        """Fetch stock data from API"""
        api_key = self.get_config_value('api_key', '')
        if not api_key:
            # Try to get from main config
            api_key = self.config.get("api_keys", {}).get("finnhub", "")
        
        if not api_key:
            self.log_error("No Finnhub API key configured")
            return False
        
        symbols = self.get_config_value('symbols', ['AAPL', 'GOOGL', 'MSFT'])
        
        try:
            self.stock_data = {}
            
            for symbol in symbols:
                # Use Finnhub quote endpoint (free tier)
                url = "https://finnhub.io/api/v1/quote"
                params = {
                    'symbol': symbol,
                    'token': api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('c', 0) > 0:  # Check if we got valid data
                        self.stock_data[symbol] = {
                            'current': data['c'],           # Current price
                            'previous_close': data['pc'],   # Previous close
                            'high': data['h'],              # Day high
                            'low': data['l'],               # Day low
                            'open': data['o'],              # Day open
                            'change': data['c'] - data['pc'],
                            'change_percent': ((data['c'] - data['pc']) / data['pc']) * 100 if data['pc'] > 0 else 0
                        }
                    else:
                        self.log_warning(f"No data received for {symbol}")
                else:
                    self.log_error(f"Stock API error for {symbol}: {response.status_code}")
            
            if self.stock_data:
                self.log_info(f"Stock data fetched for {len(self.stock_data)} symbols")
                return True
            else:
                self.log_error("No valid stock data received")
                return False
                
        except Exception as e:
            self.log_error(f"Error fetching stock data: {e}")
            return False
    
    def render(self):
        """Render the stock display"""
        try:
            # Fetch fresh data
            if not self._fetch_stock_data():
                return self._render_error()
            
            # Create image
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            # Draw header
            header_y = self.draw_header(draw, "Stock Market")
            
            # Market status (simple time-based check)
            now = datetime.now()
            market_hours = self._is_market_hours(now)
            status_text = "Market Open" if market_hours else "Market Closed"
            status_color = 'green' if market_hours else 'red'
            
            status_font = self.get_font("bold", 20)
            self.draw_text_centered(draw, status_text, header_y + 10, status_font, status_color)
            
            # Stock table
            table_y = header_y + 60
            
            # Table headers
            header_font = self.get_font("bold", 20)
            
            # Column positions for stock table
            symbol_x = 80
            price_x = 250
            change_x = 400
            percent_x = 550
            
            draw.text((symbol_x, table_y), "Symbol", font=header_font, fill=self.colors['black'])
            draw.text((price_x, table_y), "Price", font=header_font, fill=self.colors['black'])
            draw.text((change_x, table_y), "Change", font=header_font, fill=self.colors['black'])
            draw.text((percent_x, table_y), "Change %", font=header_font, fill=self.colors['black'])
            
            # Draw line under headers
            line_y = table_y + 30
            draw.line([(50, line_y), (self.width - 50, line_y)], 
                     fill=self.colors['black'], width=2)
            
            # Draw stock data
            row_height = 40
            data_font = self.get_font("regular", 18)
            bold_font = self.get_font("bold", 18)
            
            sorted_stocks = sorted(self.stock_data.items())
            
            for i, (symbol, data) in enumerate(sorted_stocks):
                if i >= 8:  # Limit to 8 stocks to fit on screen
                    break
                    
                y_pos = line_y + 20 + (i * row_height)
                
                # Symbol
                draw.text((symbol_x, y_pos), symbol, font=bold_font, fill=self.colors['black'])
                
                # Current price
                price_str = f"${data['current']:.2f}"
                draw.text((price_x, y_pos), price_str, font=data_font, fill=self.colors['black'])
                
                # Change amount and color
                change = data['change']
                change_str = f"${change:+.2f}"
                change_color = 'green' if change >= 0 else 'red'
                
                draw.text((change_x, y_pos), change_str, font=data_font, fill=self.colors[change_color])
                
                # Change percent
                percent = data['change_percent']
                percent_str = f"{percent:+.1f}%"
                
                draw.text((percent_x, y_pos), percent_str, font=data_font, fill=self.colors[change_color])
            
            # Market summary section (if space allows)
            if len(sorted_stocks) <= 5:  # Only show if we have room
                summary_y = line_y + 20 + (len(sorted_stocks) * row_height) + 30
                
                summary_font = self.get_font("bold", 18)
                detail_font = self.get_font("regular", 16)
                
                draw.text((50, summary_y), "Today's Range:", font=summary_font, fill=self.colors['blue'])
                
                # Show range for first stock as example
                if sorted_stocks:
                    first_stock = sorted_stocks[0]
                    symbol, data = first_stock
                    
                    range_text = f"{symbol}: ${data['low']:.2f} - ${data['high']:.2f}"
                    draw.text((50, summary_y + 25), range_text, font=detail_font, fill=self.colors['black'])
                    
                    open_text = f"Open: ${data['open']:.2f}, Previous: ${data['previous_close']:.2f}"
                    draw.text((50, summary_y + 45), open_text, font=detail_font, fill=self.colors['black'])
            
            # Footer with update time and disclaimer
            footer_text = f"Updated: {now.strftime('%H:%M')} • Data delayed"
            self.draw_footer(draw, footer_text)
            
            # Show the image
            self.show_image(image)
            self.log_info(f"Stock display updated with {len(self.stock_data)} symbols")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to render stocks: {e}")
            return self._render_error()
    
    def _is_market_hours(self, dt):
        """Simple check if it's during market hours (US Eastern Time)
        
        Args:
            dt: datetime object
            
        Returns:
            True if likely during market hours
        """
        # This is a simplified check - doesn't account for holidays or timezone
        weekday = dt.weekday()  # 0 = Monday, 6 = Sunday
        hour = dt.hour
        
        # Market typically open Monday-Friday, 9:30 AM - 4:00 PM ET
        # This is a rough approximation
        if weekday >= 5:  # Weekend
            return False
        
        if hour < 9 or hour >= 16:  # Before 9 AM or after 4 PM
            return False
        
        return True
    
    def _render_error(self):
        """Render error message"""
        try:
            image = self.create_image('white')
            draw = self.create_draw(image)
            
            self.draw_header(draw, "Stock Market Error")
            
            error_font = self.get_font("regular", 32)
            self.draw_text_centered(draw, "Unable to fetch stock data", 
                                  self.height // 2 - 50, error_font, 'red')
            
            self.draw_text_centered(draw, "Please check your API key", 
                                  self.height // 2, error_font, 'red')
            
            self.draw_footer(draw, f"Error at: {datetime.now().strftime('%H:%M')}")
            
            self.show_image(image)
            return False
            
        except Exception as e:
            self.log_error(f"Failed to render error message: {e}")
            return False