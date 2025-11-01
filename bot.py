#!/usr/bin/env python3
"""
Crypto Price Editor Bot - Docker Optimized with LARGE FONT
Edits existing banner images with live prices in EXTRA LARGE bold font.
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

# Multiple API endpoints for reliability
API_URLS = [
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,toncoin,litecoin&vs_currencies=usd&include_24hr_change=true",
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,the-open-network,litecoin&vs_currencies=usd&include_24hr_change=true",
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,ton,litecoin&vs_currencies=usd&include_24hr_change=true"
]

# Alternative API as backup
ALTERNATIVE_API = "https://api.binance.com/api/v3/ticker/price"

# Coin configuration with different intervals (in seconds)
COINS = {
    "BTC": {"id": "bitcoin", "file": "btc.jpg", "interval": 120, "symbol": "BTCUSDT"},
    "ETH": {"id": "ethereum", "file": "eth.jpg", "interval": 300, "symbol": "ETHUSDT"},
    "TON": {"id": "toncoin", "file": "ton.jpg", "interval": 600, "symbol": "TONUSDT"},
    "LTC": {"id": "litecoin", "file": "ltc.jpg", "interval": 900, "symbol": "LTCUSDT"},
}

# Price history file path (in data directory for Docker)
PRICE_HISTORY_FILE = "/app/data/price_history.json"

# EXTRA LARGE font settings for Railway
FONT_SIZE = 140  # Increased from 120 to 140 for Railway
PRICE_POSITION = (640, 150)  # Adjusted position

def load_price_history():
    """Load previous prices from file"""
    try:
        if os.path.exists(PRICE_HISTORY_FILE):
            with open(PRICE_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load price history: {e}")
    return {}

def save_price_history(history):
    """Save current prices to file"""
    try:
        os.makedirs(os.path.dirname(PRICE_HISTORY_FILE), exist_ok=True)
        with open(PRICE_HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except Exception as e:
        print(f"⚠️ Could not save price history: {e}")

def get_price_change_direction(current_price, previous_price):
    """Determine if price increased or decreased compared to previous price"""
    if previous_price is None:
        return "up"
    if current_price > previous_price:
        return "up"
    elif current_price < previous_price:
        return "down"
    else:
        return "same"

def get_prices_coingecko():
    """Fetch prices from CoinGecko with multiple URL attempts"""
    for api_url in API_URLS:
        try:
            print(f"📡 Trying CoinGecko API...")
            response = requests.get(api_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            print(f"✅ CoinGecko prices fetched successfully")
            print(f"📊 API returned data for: {list(data.keys())}")
            return data
        except Exception as e:
            print(f"❌ CoinGecko API failed: {e}")
            continue
    return None

def get_prices_binance():
    """Fetch prices from Binance as backup"""
    try:
        print("📡 Trying Binance API...")
        prices = {}
        for coin, info in COINS.items():
            try:
                url = f"{ALTERNATIVE_API}?symbol={info['symbol']}"
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                data = response.json()
                price = float(data['price'])
                prices[coin] = {"usd": price, "usd_24h_change": 0}
                print(f"✅ {coin}: ${price:,.2f}")
            except Exception as e:
                print(f"❌ Binance failed for {coin}: {e}")
                continue
        
        if prices:
            print("✅ Binance prices fetched successfully")
            return prices
        return None
    except Exception as e:
        print(f"❌ Binance API completely failed: {e}")
        return None

def get_prices():
    """Fetch prices with fallback APIs"""
    data = get_prices_coingecko()
    
    if not data or "toncoin" not in data:
        print("🔄 CoinGecko missing TON data, trying Binance...")
        binance_data = get_prices_binance()
        if binance_data:
            return binance_data
    
    return data

def get_large_font(size):
    """Get a large font - Railway compatible"""
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/custom/arial.ttf",
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                print(f"✅ Using font: {font_path}")
                return ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"⚠️ Font {font_path} failed: {e}")
            continue
    
    # Final fallback - create a large default font
    print("⚠️ Using default font (fallback)")
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            # Try to create a large bitmap font
            from PIL import ImageFont
            return ImageFont.load_default()
        except:
            # Last resort - manual font creation
            return None

def format_price(price):
    """Format price professionally with correct decimals"""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:.4f}"

def edit_banner_price(symbol, price, file_name):
    """Edit banner with EXTRA LARGE price text"""
    try:
        if not os.path.exists(file_name):
            print(f"❌ File not found: {file_name}")
            return None
            
        img = Image.open(file_name)
        draw = ImageDraw.Draw(img)
        
        price_text = format_price(price)
        font = get_large_font(FONT_SIZE)
        
        if font is None:
            print("❌ No font available, using basic text")
            # Manual text drawing as last resort
            img.save(f"temp_{file_name}", "JPEG", quality=95)
            return f"temp_{file_name}"
        
        # Calculate text position
        try:
            bbox = draw.textbbox((0, 0), price_text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            # Fallback for older Pillow
            w, h = draw.textsize(price_text, font=font)
        
        print(f"📏 Text size: {w}x{h} for '{price_text}'")
        
        # Center the price text
        x = PRICE_POSITION[0] - w / 2
        y = PRICE_POSITION[1] - h / 2
        
        # Draw price text in WHITE - EXTRA LARGE and BOLD
        draw.text((x, y), price_text, font=font, fill=(255, 255, 255))
        
        output_file = f"temp_{file_name}"
        img.save(output_file, "JPEG", quality=95)
        print(f"✅ Created: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error editing {file_name}: {e}")
        return None

def send_photo(file_path, caption):
    """Send photo to Telegram"""
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
            print("✅ Posted to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return False

def cleanup_temp_files():
    """Remove all temporary files from folder"""
    try:
        for file in os.listdir('.'):
            if file.startswith("temp_") and (file.endswith(".jpg") or file.endswith(".jpeg")):
                os.remove(file)
                print(f"🧹 Cleaned up: {file}")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def check_files():
    """Check if all image files exist"""
    print("🔍 Checking files...")
    all_exist = True
    for coin, info in COINS.items():
        if os.path.exists(info["file"]):
            print(f"✅ {coin}: {info['file']} - FOUND")
        else:
            print(f"❌ {coin}: {info['file']} - MISSING")
            all_exist = False
    return all_exist

def main():
    print("🚀 Railway Crypto Price Bot Started!")
    print("📊 Supported coins: BTC, ETH, TON, LTC")
    print("⏰ Post intervals: BTC:2m, ETH:5m, TON:10m, LTC:15m")
    print("💰 Professional price formatting")
    print("📈📉 Smart emoji based on price movement")
    print("📱 Channel: @cryptoprics")
    print(f"🔠 EXTRA LARGE FONT SIZE: {FONT_SIZE}")
    print("─" * 50)
    
    # Load price history
    price_history = load_price_history()
    
    # Clean up any existing temp files
    cleanup_temp_files()
    
    # Check files
    if not check_files():
        print("\n❌ Missing some image files!")
        print("Please make sure you have: btc.jpg, eth.jpg, ton.jpg, ltc.jpg")
        return
    
    print("\n✅ All files found! Starting bot...")
    
    last_post = {coin: 0 for coin in COINS}
    
    try:
        while True:
            prices = get_prices()
            
            if prices:
                current_time = time.time()
                
                for coin, info in COINS.items():
                    coin_id = info["id"]
                    
                    # Multiple ways to find coin data
                    coin_data = None
                    if coin_id in prices:
                        coin_data = prices[coin_id]
                    elif coin in prices:
                        coin_data = prices[coin]
                    elif coin == "TON" and "the-open-network" in prices:
                        coin_data = prices["the-open-network"]
                    elif coin == "TON" and "ton" in prices:
                        coin_data = prices["ton"]
                    
                    if not coin_data:
                        print(f"⚠️ No data found for {coin}")
                        continue
                        
                    if current_time - last_post[coin] >= info["interval"]:
                        current_price = coin_data["usd"]
                        previous_price = price_history.get(coin)
                        
                        print(f"\n🔄 Processing {coin}...")
                        print(f"   Price: {format_price(current_price)}")
                        
                        # Edit banner
                        edited_file = edit_banner_price(coin, current_price, info["file"])
                        
                        if edited_file:
                            # Determine emoji
                            change_direction = get_price_change_direction(current_price, previous_price)
                            arrow = "📈" if change_direction in ["up", "same"] else "📉"
                            
                            caption = f"{arrow} {coin} {format_price(current_price)}\n\n@cryptoprics"
                            
                            # Send to Telegram
                            if send_photo(edited_file, caption):
                                last_post[coin] = current_time
                                price_history[coin] = current_price
                                save_price_history(price_history)
                                print(f"✅ {coin} posted successfully!")
                                
                                # Cleanup temp file
                                try:
                                    os.remove(edited_file)
                                    print(f"🧹 Removed temp file")
                                except Exception as e:
                                    print(f"⚠️ Could not remove temp file: {e}")
            
            # Show next posting times
            print(f"\n⏰ Next posts:")
            current_time = time.time()
            for coin, info in COINS.items():
                time_left = max(0, info["interval"] - (current_time - last_post[coin]))
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                status = "READY" if time_left == 0 else "WAITING"
                print(f"   {coin}: {minutes:02d}:{seconds:02d} ({status})")
            
            print(f"📡 Monitoring... Next update in 30s")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
