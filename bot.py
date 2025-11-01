#!/usr/bin/env python3
"""
Crypto Price Editor Bot - Railway Optimized with Dynamic Font Download
"""

import time
import requests
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import json

# === CONFIGURATION ===
BOT_TOKEN = "8353463001:AAFSeYXQ9LmDmCmOaDWAAqVsUNIwBV9RAGM"
CHAT_ID = "-1003177389386"

API_URLS = [
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,toncoin,litecoin&vs_currencies=usd&include_24hr_change=true",
]

ALTERNATIVE_API = "https://api.binance.com/api/v3/ticker/price"

COINS = {
    "BTC": {"id": "bitcoin", "file": "btc.jpg", "interval": 120, "symbol": "BTCUSDT"},
    "ETH": {"id": "ethereum", "file": "eth.jpg", "interval": 300, "symbol": "ETHUSDT"},
    "TON": {"id": "toncoin", "file": "ton.jpg", "interval": 600, "symbol": "TONUSDT"},
    "LTC": {"id": "litecoin", "file": "ltc.jpg", "interval": 900, "symbol": "LTCUSDT"},
}

PRICE_HISTORY_FILE = "price_history.json"

# EXTRA LARGE font settings
FONT_SIZE = 140
PRICE_POSITION = (640, 150)
FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
FONT_PATH = "/app/roboto-bold.ttf"

def download_font():
    """Download Roboto font if not exists"""
    if not os.path.exists(FONT_PATH):
        try:
            print("📥 Downloading Roboto font...")
            response = requests.get(FONT_URL, timeout=30)
            response.raise_for_status()
            with open(FONT_PATH, 'wb') as f:
                f.write(response.content)
            print("✅ Font downloaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to download font: {e}")
            return False
    return True

def get_large_font(size):
    """Get a large font - downloads if needed"""
    # Ensure font is available
    if not download_font():
        print("❌ Cannot download font, using fallback")
        return create_fallback_font(size)
    
    # Try the downloaded font
    try:
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, size)
            print(f"✅ Using Roboto Bold font size {size}")
            return font
    except Exception as e:
        print(f"❌ Roboto font failed: {e}")
    
    # Fallback to system fonts
    system_fonts = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    for font_path in system_fonts:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
                print(f"✅ Using system font: {os.path.basename(font_path)}")
                return font
        except:
            continue
    
    # Final fallback - create a large bitmap font
    return create_fallback_font(size)

def create_fallback_font(size):
    """Create a large fallback font"""
    print("⚠️ Creating fallback font")
    try:
        # Try to load default font at larger size
        return ImageFont.load_default()
    except:
        try:
            # Create a basic font
            from PIL import ImageFont
            return ImageFont.load_default()
        except:
            # Last resort - return None
            return None

def load_price_history():
    try:
        if os.path.exists(PRICE_HISTORY_FILE):
            with open(PRICE_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_price_history(history):
    try:
        with open(PRICE_HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except:
        pass

def get_price_change_direction(current_price, previous_price):
    if previous_price is None:
        return "up"
    if current_price > previous_price:
        return "up"
    elif current_price < previous_price:
        return "down"
    else:
        return "same"

def get_prices_coingecko():
    for api_url in API_URLS:
        try:
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            print("✅ CoinGecko prices fetched")
            return data
        except Exception as e:
            print(f"❌ CoinGecko API failed: {e}")
            continue
    return None

def get_prices_binance():
    try:
        prices = {}
        for coin, info in COINS.items():
            try:
                url = f"{ALTERNATIVE_API}?symbol={info['symbol']}"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                price = float(data['price'])
                prices[coin] = {"usd": price, "usd_24h_change": 0}
            except Exception as e:
                print(f"❌ Binance failed for {coin}: {e}")
                continue
        
        if prices:
            print("✅ Binance prices fetched")
            return prices
        return None
    except Exception as e:
        print(f"❌ Binance API failed: {e}")
        return None

def get_prices():
    data = get_prices_coingecko()
    
    if not data or "toncoin" not in data:
        binance_data = get_prices_binance()
        if binance_data:
            return binance_data
    
    return data

def format_price(price):
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:.4f}"

def edit_banner_price(symbol, price, file_name):
    try:
        if not os.path.exists(file_name):
            print(f"❌ File not found: {file_name}")
            return None
            
        img = Image.open(file_name)
        draw = ImageDraw.Draw(img)
        
        price_text = format_price(price)
        font = get_large_font(FONT_SIZE)
        
        if font is None:
            print("❌ No font available, cannot add text")
            output_file = f"temp_{file_name}"
            img.save(output_file, "JPEG", quality=95)
            return output_file
        
        # Calculate text dimensions
        try:
            bbox = draw.textbbox((0, 0), price_text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            w, h = draw.textsize(price_text, font=font)
        
        print(f"📏 Text dimensions: {w}x{h} for '{price_text}'")
        
        # Center the text
        x = PRICE_POSITION[0] - w / 2
        y = PRICE_POSITION[1] - h / 2
        
        # Add black background for better visibility
        margin = 10
        draw.rectangle(
            [x - margin, y - margin, x + w + margin, y + h + margin],
            fill=(0, 0, 0)
        )
        
        # Draw white text
        draw.text((x, y), price_text, font=font, fill=(255, 255, 255))
        
        output_file = f"temp_{file_name}"
        img.save(output_file, "JPEG", quality=95)
        print(f"✅ Created banner with {FONT_SIZE}px font")
        return output_file
        
    except Exception as e:
        print(f"❌ Error editing {file_name}: {e}")
        return None

def send_photo(file_path, caption):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        
        with open(file_path, "rb") as photo:
            response = requests.post(
                url,
                data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
                files={"photo": photo},
                timeout=30
            )
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return False

def cleanup_temp_files():
    try:
        for file in os.listdir('.'):
            if file.startswith("temp_") and file.endswith(".jpg"):
                os.remove(file)
    except:
        pass

def check_files():
    all_exist = True
    for coin, info in COINS.items():
        if not os.path.exists(info["file"]):
            print(f"❌ Missing: {info['file']}")
            all_exist = False
        else:
            print(f"✅ Found: {info['file']}")
    return all_exist

def main():
    print("🚀 Crypto Bot with Dynamic Font Download Started!")
    print(f"🔠 Font Size: {FONT_SIZE}px")
    print(f"📏 Banner Size: 1280x334")
    print("─" * 50)
    
    # Download font at startup
    download_font()
    
    price_history = load_price_history()
    cleanup_temp_files()
    
    if not check_files():
        print("❌ Missing banner files")
        return
    
    last_post = {coin: 0 for coin in COINS}
    
    try:
        while True:
            prices = get_prices()
            
            if prices:
                current_time = time.time()
                
                for coin, info in COINS.items():
                    coin_data = None
                    if info["id"] in prices:
                        coin_data = prices[info["id"]]
                    elif coin in prices:
                        coin_data = prices[coin]
                    elif coin == "TON" and "the-open-network" in prices:
                        coin_data = prices["the-open-network"]
                    
                    if coin_data and current_time - last_post[coin] >= info["interval"]:
                        current_price = coin_data["usd"]
                        previous_price = price_history.get(coin)
                        
                        print(f"🔄 Processing {coin}: {format_price(current_price)}")
                        
                        edited_file = edit_banner_price(coin, current_price, info["file"])
                        
                        if edited_file:
                            change_direction = get_price_change_direction(current_price, previous_price)
                            arrow = "📈" if change_direction in ["up", "same"] else "📉"
                            caption = f"{arrow} {coin} {format_price(current_price)}\n\n@cryptoprics"
                            
                            if send_photo(edited_file, caption):
                                last_post[coin] = current_time
                                price_history[coin] = current_price
                                save_price_history(price_history)
                                print(f"✅ {coin} posted successfully!")
                            
                            try:
                                os.remove(edited_file)
                            except:
                                pass
            
            print("📡 Monitoring... (30s)")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
