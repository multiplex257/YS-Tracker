# YS-Tracker
#YS-Tracker is to track live event
print("before import")
import os
import json
import time
import requests
from bs4 import BeautifulSoup

print("before bse")
STATE_FILE = "last_announcement.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"DEBUG: TELEGRAM_BOT_TOKEN = {TELEGRAM_BOT_TOKEN[:10] if TELEGRAM_BOT_TOKEN else 'NOT SET'}...")
print(f"DEBUG: TELEGRAM_CHAT_ID = {TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID else 'NOT SET'}")

def send_alert(message):
    print(f"ALERT: {message}")
    
    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            print(f"DEBUG: Sending Telegram alert to URL: {url}")
            print(f"DEBUG: Payload: {payload}")
            
            response = requests.post(url, json=payload, timeout=10)
            print(f"DEBUG: Telegram API Response Status: {response.status_code}")
            print(f"DEBUG: Telegram API Response: {response.text}")
            
            if response.status_code == 200:
                print("✓ Telegram alert sent successfully!")
            else:
                print(f"✗ Failed to send Telegram alert. Status: {response.status_code}")
        except Exception as e:
            print(f"✗ Exception while sending Telegram alert: {e}")
    else:
        print("⚠ Telegram credentials not set - alert not sent")

def check_announcements():
    try:
        print("Attempting to fetch BSE announcements...")
        
        # BSE India corporate announcements page for Unitech (Scrip: 507878)
        url = "https://www.bseindia.com/corporates/ann_date.aspx?Scrip=507878&Anntype=&FromDate=&ToDate=&Category=&Dept=&Sort=&yrflag="
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"DEBUG: Making GET request to: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"✓ Response status: {response.status_code}")
        print(f"✓ Response length: {len(response.text)} bytes")
        print(f"DEBUG: Response Content (first 500 chars):\n{response.text[:500]}")
        
        if not response.text or len(response.text) < 100:
            print("⚠ Empty or minimal response from BSE")
            return
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for announcement table rows
        rows = soup.find_all('tr')
        print(f"✓ Found {len(rows)} table rows in response")
        
        if not rows or len(rows) < 2:
            print("⚠ No announcement rows found in response")
            return
        
        # Get the first data row (skip header)
        latest_row = None
        for idx, row in enumerate(rows[1:]):  # Skip header row
            cells = row.find_all('td')
            if cells and len(cells) > 0:
                print(f"DEBUG: Found data row at index {idx}: {len(cells)} cells")
                latest_row = cells
                break
        
        if not latest_row or len(latest_row) == 0:
            print("⚠ Could not extract announcement data from rows")
            return
        
        # Extract announcement details
        try:
            announcement_date = latest_row[0].get_text(strip=True) if len(latest_row) > 0 else "N/A"
            news_sub = latest_row[1].get_text(strip=True) if len(latest_row) > 1 else "N/A"
            news_id = announcement_date + "_" + news_sub[:20]  # Create unique ID from date and subject
            
            print(f"✓ Latest announcement ID: {news_id}")
            print(f"✓ Announcement Date: {announcement_date}")
            print(f"✓ Announcement Subject: {news_sub}")
            
        except Exception as e:
            print(f"✗ Error extracting announcement details: {e}")
            return
        
        # Load previous state
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    last_state = json.load(f)
                print(f"✓ Loaded previous state: {last_state}")
            except Exception as e:
                print(f"⚠ Error loading state file: {e}")
                last_state = {}
        else:
            print("ℹ State file does not exist - first run")
            last_state = {}
        
        # Check for new updates
        if last_state.get("NEWSID") != news_id:
            print("✓ New announcement detected!")
            
            # Look for indicators regarding the CMD or Director changes
            keywords = ["CMD", "TENURE", "EXTENSION", "DIRECTOR", "MALIK", "YUDHVIR"]
            text_to_check = news_sub.upper()
            
            is_relevant = any(kw in text_to_check for kw in keywords)
            print(f"DEBUG: Is relevant: {is_relevant} (keywords checked: {keywords})")
            
            if is_relevant:
                alert_msg = f"⚠️ <b>UNITECH REGULATORY UPDATE</b> ⚠️\n\n<b>Date:</b> {announcement_date}\n<b>Subject:</b> {news_sub}\n<b>Link:</b> https://www.bseindia.com/corporates/ann_date.aspx?Scrip=507878"
                send_alert(alert_msg)
            else:
                print("ℹ Announcement not relevant - no alert sent")
            
            # Save new state
            try:
                with open(STATE_FILE, "w") as f:
                    json.dump({"NEWSID": news_id}, f)
                print("✓ State saved successfully")
            except Exception as e:
                print(f"✗ Error saving state: {e}")
        else:
            print(f"ℹ No new announcements (current: {news_id})")
                
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error checking BSE: {e}")
    except Exception as e:
        print(f"✗ Error checking BSE: {e}")

if __name__ == "__main__":
    print("Starting Unitech regulatory tracker...")
    check_announcements()
    print("Check completed successfully!")
