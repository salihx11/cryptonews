#!/usr/bin/env python3
"""
Crypto Price Editor Bot
Edits existing banner images with live prices in bold font.
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
    "BTC": {"id": "bitcoin", "file": "btc.jpg", "interval": 120, "symbol": "BTCUSDT"},    # 2 minutes
    "ETH": {"id": "ethereum", "file": "eth.jpg", "interval": 300, "symbol": "ETHUSDT"},   # 5 minutes
    "TON": {"id": "toncoin", "file": "ton.jpg", "interval": 600, "symbol": "TONUSDT"},    # 10 minutes
    "LTC": {"id": "litecoin", "file": "ltc.jpg", "interval": 900, "symbol": "LTCUSDT"},   # 15 minutes
}

# Price history file to track previous prices
PRICE_HISTORY_FILE = "price_history.json"

# Try to find bold fonts
FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
    "C:/Windows/Fonts/verdana.ttf", 
    "C:/Windows/Fonts/tahomabd.ttf",  # Tahoma Bold
    "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
    "C:/Windows/Fonts/calibrib.ttf",  # Calibri Bold
    "C:/Windows/Fonts/arial.ttf"
]

FONT_SIZE = 90  # Large bold font size

# Price position - centered
PRICE_POSITION = (640, 150)

def load_price_history():
    """Load previous prices from file"""
    try:
        if os.path.exists(PRICE_HISTORY_FILE):
            with open(PRICE_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_price_history(history):
    """Save current prices to file"""
    try:
        with open(PRICE_HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except:
        pass

def get_price_change_direction(current_price, previous_price):
    """Determine if price increased or decreased compared to previous price"""
    if previous_price is None:
        return "up"  # Default to up if no previous price
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
            print(f"📡 Trying CoinGecko API: {api_url.split('?')[0]}...")
            response = requests.get(api_url, timeout=10)
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
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                price = float(data['price'])
                prices[coin] = {"usd": price, "usd_24h_change": 0}  # Binance doesn't provide 24h change in this endpoint
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
    # Try CoinGecko first
    data = get_prices_coingecko()
    
    # If CoinGecko fails or doesn't have TON, try Binance
    if not data or "toncoin" not in data:
        print("🔄 CoinGecko missing TON data, trying Binance...")
        binance_data = get_prices_binance()
        if binance_data:
            return binance_data
    
    return data

def get_bold_font(size):
    """Get a bold font"""
    for font_path in FONT_PATHS:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            continue
    # Fallback
    try:
        return ImageFont.truetype("arial", size)
    except:
        return ImageFont.load_default()

def format_price(price):
    """Format price professionally with correct decimals"""
    if price >= 1000:
        # For high prices like BTC, ETH - show with commas, no decimals
        return f"${price:,.0f}"
    elif price >= 1:
        # For medium prices like LTC - show 2 decimals
        return f"${price:,.2f}"
    else:
        # For low prices - show 4 decimals
        return f"${price:.4f}"

def edit_banner_price(symbol, price, file_name):
    """Edit banner with price only (no percentage)"""
    try:
        if not os.path.exists(file_name):
            print(f"❌ File not found: {file_name}")
            return None
            
        # Open image
        img = Image.open(file_name)
        draw = ImageDraw.Draw(img)
        
        # Format price text professionally
        price_text = format_price(price)
        
        # Load BOLD font (same font for all coins)
        font = get_bold_font(FONT_SIZE)
        
        # Calculate text position
        try:
            bbox = draw.textbbox((0, 0), price_text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            w, h = draw.textsize(price_text, font=font)
        
        # Center the price text
        x = PRICE_POSITION[0] - w / 2
        y = PRICE_POSITION[1] - h / 2
        
        # Draw price text in WHITE - BOLD and clean modern look
        draw.text((x, y), price_text, font=font, fill=(255, 255, 255))
        
        # Save
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
            print(f"❌ Telegram error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending: {e}")
        return False

def cleanup_temp_files():
    """Remove all temporary files from folder"""
    try:
        for file in os.listdir():
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
    print("🤖 Crypto Price Bot Started!")
    print("📊 Supported coins: BTC, ETH, TON, LTC")
    print("⏰ Post intervals:")
    print("   BTC: 2 minutes")
    print("   ETH: 5 minutes") 
    print("   TON: 10 minutes")
    print("   LTC: 15 minutes")
    print("💰 Professional price formatting")
    print("📈📉 Smart emoji based on price movement")
    print("📱 Channel: @cryptoprics")
    print("🌐 Multiple API fallbacks for reliability")
    print("─" * 50)
    
    # Load price history
    price_history = load_price_history()
    
    # Clean up any existing temp files first
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
                    
                    # Check if coin data exists in API response
                    # Try multiple ways to find the coin data
                    coin_data = None
                    
                    # Method 1: Try by coin ID
                    if coin_id in prices:
                        coin_data = prices[coin_id]
                    # Method 2: Try by symbol (for Binance data)
                    elif coin in prices:
                        coin_data = prices[coin]
                    # Method 3: Try alternative TON names
                    elif coin == "TON" and "the-open-network" in prices:
                        coin_data = prices["the-open-network"]
                    elif coin == "TON" and "ton" in prices:
                        coin_data = prices["ton"]
                    
                    if not coin_data:
                        print(f"⚠️ No data found for {coin} (tried: {coin_id}, {coin})")
                        continue
                        
                    # Check if it's time to post this coin
                    if current_time - last_post[coin] >= info["interval"]:
                        current_price = coin_data["usd"]
                        previous_price = price_history.get(coin)
                        
                        print(f"\n🔄 Processing {coin}...")
                        print(f"   Current Price: {format_price(current_price)}")
                        if previous_price:
                            print(f"   Previous Price: {format_price(previous_price)}")
                            change_percent = ((current_price - previous_price) / previous_price) * 100
                            print(f"   Change: {change_percent:+.2f}%")
                        else:
                            print(f"   Previous Price: First post")
                        
                        # Edit banner (PRICE ONLY on image)
                        edited_file = edit_banner_price(coin, current_price, info["file"])
                        
                        if edited_file:
                            # Determine emoji based on price change vs previous price
                            change_direction = get_price_change_direction(current_price, previous_price)
                            
                            # PERFECT EMOJI LOGIC
                            if change_direction == "up":
                                arrow = "📈"  # Up arrow for price increase
                            elif change_direction == "down":
                                arrow = "📉"  # Down arrow for price decrease
                            else:
                                arrow = "📈"  # Default to up arrow for same price (first post)
                            
                            # Create professional caption with correct channel name
                            formatted_price = format_price(current_price)
                            caption = f"{arrow} {coin} {formatted_price}\n\n@cryptoprics"
                            
                            # Send to Telegram
                            if send_photo(edited_file, caption):
                                last_post[coin] = current_time
                                # Update price history
                                price_history[coin] = current_price
                                save_price_history(price_history)
                                
                                print(f"✅ {coin} posted successfully!")
                                print(f"⏰ Next {coin} post in {info['interval']} seconds")
                                
                                # Show the exact caption that was sent
                                print(f"📝 Caption: {caption}")
                            else:
                                print(f"❌ Failed to send {coin} to Telegram")
                            
                            # Cleanup temp file immediately after sending
                            try:
                                os.remove(edited_file)
                                print(f"🧹 Removed temp file: {edited_file}")
                            except Exception as e:
                                print(f"⚠️ Could not remove temp file: {e}")
                        else:
                            print(f"❌ Failed to process {coin} banner")
            
            # Show next posting times
            print(f"\n⏰ Next posts:")
            current_time = time.time()
            for coin, info in COINS.items():
                time_passed = current_time - last_post[coin]
                time_left = max(0, info["interval"] - time_passed)
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                status = "READY" if time_left == 0 else "WAITING"
                print(f"   {coin}: {minutes:02d}:{seconds:02d} ({status})")
            
            print(f"📡 Monitoring... Next update in 30s | {time.strftime('%H:%M:%S')}")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        # Final cleanup
        cleanup_temp_files()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        cleanup_temp_files()

if __name__ == "__main__":
    main()