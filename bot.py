#!/usr/bin/env python3
"""
Crypto Price Bot - Text Only Version
Posts crypto prices with percentage changes to Telegram without images.
"""

import time
import requests
import json
import os

# === CONFIGURATION ===
BOT_TOKEN = "8353463001:AAFSeYXQ9LmDmCmOaDWAAqVsUNIwBV9RAGM"
CHAT_ID = "-1003177389386"

API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,toncoin,litecoin&vs_currencies=usd&include_24hr_change=true"

# Coin configuration with different intervals (in seconds)
COINS = {
    "BTC": {"id": "bitcoin", "interval": 120},    # 2 minutes
    "ETH": {"id": "ethereum", "interval": 300},   # 5 minutes
    "TON": {"id": "toncoin", "interval": 600},    # 10 minutes
    "LTC": {"id": "litecoin", "interval": 900},   # 15 minutes
}

# Price history file to track previous prices
PRICE_HISTORY_FILE = "price_history.json"

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

def get_price_change_percentage(current_price, previous_price):
    """Calculate percentage change"""
    if previous_price is None or previous_price == 0:
        return 0
    return ((current_price - previous_price) / previous_price) * 100

def get_prices():
    """Fetch current cryptocurrency prices"""
    try:
        print("📡 Fetching prices from CoinGecko...")
        response = requests.get(API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
        print("✅ Prices fetched successfully")
        return data
    except Exception as e:
        print(f"❌ Error fetching prices: {e}")
        return None

def send_message(text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def format_price_message(coin, current_price, change_percentage, is_24h_change=False):
    """Format the price message with emojis and percentage"""
    
    # Select emoji based on percentage change
    if change_percentage > 0:
        arrow = "📈"
        change_text = f"+{change_percentage:.2f}%"
    elif change_percentage < 0:
        arrow = "📉"
        change_text = f"{change_percentage:.2f}%"
    else:
        arrow = "➡️"
        change_text = "0.00%"
    
    # Format price based on value
    if current_price >= 1000:
        price_text = f"${current_price:,.0f}"
    elif current_price >= 1:
        price_text = f"${current_price:,.2f}"
    else:
        price_text = f"${current_price:.4f}"
    
    # Create message
    if is_24h_change:
        message = f"{arrow} <b>{coin}</b>\n💰 {price_text}\n📊 24h: {change_text}"
    else:
        message = f"{arrow} <b>{coin}</b>\n💰 {price_text}\n📈 Change: {change_text}"
    
    return message

def format_24h_message(coin_data):
    """Format message using 24h change from API"""
    messages = []
    for coin, info in COINS.items():
        if info["id"] in coin_data:
            data = coin_data[info["id"]]
            current_price = data["usd"]
            change_24h = data["usd_24h_change"]
            
            # Select emoji based on 24h change
            if change_24h > 0:
                arrow = "📈"
                change_text = f"+{change_24h:.2f}%"
            elif change_24h < 0:
                arrow = "📉"
                change_text = f"{change_24h:.2f}%"
            else:
                arrow = "➡️"
                change_text = "0.00%"
            
            # Format price
            if current_price >= 1000:
                price_text = f"${current_price:,.0f}"
            elif current_price >= 1:
                price_text = f"${current_price:,.2f}"
            else:
                price_text = f"${current_price:.4f}"
            
            message = f"{arrow} <b>{coin}</b>\n💰 {price_text}\n📊 24h: {change_text}"
            messages.append(message)
    
    return "\n\n".join(messages)

def main():
    print("🤖 Crypto Price Bot Started! (Text Only)")
    print("📊 Supported coins: BTC, ETH, TON, LTC")
    print("⏰ Post intervals:")
    print("   BTC: 2 minutes")
    print("   ETH: 5 minutes") 
    print("   TON: 10 minutes")
    print("   LTC: 15 minutes")
    print("📈 Shows 24h percentage changes")
    print("📱 Channel: @cryptopricedrop")
    print("─" * 50)
    
    # Load price history
    price_history = load_price_history()
    
    last_post = {coin: 0 for coin in COINS}
    
    try:
        while True:
            prices = get_prices()
            
            if prices:
                current_time = time.time()
                
                for coin, info in COINS.items():
                    coin_id = info["id"]
                    
                    if coin_id in prices:
                        coin_data = prices[coin_id]
                        current_price = coin_data["usd"]
                        change_24h = coin_data["usd_24h_change"]
                        
                        # Check if it's time to post this coin
                        if current_time - last_post[coin] >= info["interval"]:
                            print(f"\n🔄 Processing {coin}...")
                            print(f"   Current Price: ${current_price:,.2f}")
                            print(f"   24h Change: {change_24h:+.2f}%")
                            
                            # Format message using 24h change from API
                            message = format_price_message(coin, current_price, change_24h, is_24h_change=True)
                            
                            # Add channel tag
                            full_message = f"{message}\n\n@cryptoprics"
                            
                            # Send to Telegram
                            if send_message(full_message):
                                last_post[coin] = current_time
                                
                                # Update price history for tracking
                                price_history[coin] = current_price
                                save_price_history(price_history)
                                
                                print(f"✅ {coin} posted successfully!")
                                print(f"⏰ Next {coin} post in {info['interval']} seconds")
                                print(f"📝 Message: {message.split('@')[0]}")
                            
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
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

