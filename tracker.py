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
print(TELEGRAM_BOT_TOKEN)
print(TELEGRAM_CHAT_ID)
def send_alert(message):
    print(f"ALERT: {message}")
    
    # Optional: Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")

def check_announcements():
    try:
        print("Attempting to fetch BSE announcements...")
        
        # BSE India corporate announcements page for Unitech (Scrip: 507878)
        url = "https://www.bseindia.com/corporates/ann_date.aspx?Scrip=507878&Anntype=&FromDate=&ToDate=&Category=&Dept=&Sort=&yrflag="
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)} bytes")
        
        if not response.text or len(response.text) < 100:
            print("Empty or minimal response from BSE")
            return
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for announcement table rows
        # BSE typically has announcement data in table format
        rows = soup.find_all('tr')
        print(f"Found {len(rows)} table rows")
        
        if not rows or len(rows) < 2:
            print("No announcement rows found in response")
            return
        
        # Get the first data row (skip header)
        latest_row = None
        for row in rows[1:]:  # Skip header row
            cells = row.find_all('td')
            if cells and len(cells) > 0:
                latest_row = cells
                break
        
        if not latest_row or len(latest_row) == 0:
            print("Could not extract announcement data from rows")
            return
        
        # Extract announcement details
        # BSE typically has: Date, Subject, Category, Department, etc.
        try:
            announcement_date = latest_row[0].get_text(strip=True) if len(latest_row) > 0 else "N/A"
            news_sub = latest_row[1].get_text(strip=True) if len(latest_row) > 1 else "N/A"
            news_id = announcement_date + "_" + news_sub[:20]  # Create unique ID from date and subject
            
            print(f"Latest announcement: {news_id}")
            print(f"Subject: {news_sub}")
            
        except Exception as e:
            print(f"Error extracting announcement details: {e}")
            return
        
        # Load previous state
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    last_state = json.load(f)
            except:
                last_state = {}
        else:
            last_state = {}
        
        # Check for new updates
        if last_state.get("NEWSID") != news_id:
            print("New announcement detected!")
            
            # Look for indicators regarding the CMD or Director changes
            keywords = ["CMD", "TENURE", "EXTENSION", "DIRECTOR", "MALIK", "YUDHVIR"]
            text_to_check = news_sub.upper()
            
            is_relevant = any(kw in text_to_check for kw in keywords)
            
            if is_relevant:
                alert_msg = f"⚠️ UNITECH REGULATORY UPDATE ⚠️\n\nDate: {announcement_date}\nSubject: {news_sub}\nLink: https://www.bseindia.com/corporates/ann_date.aspx?Scrip=507878"
                send_alert(alert_msg)
            
            # Save new state
            try:
                with open(STATE_FILE, "w") as f:
                    json.dump({"NEWSID": news_id}, f)
                print("State saved successfully")
            except Exception as e:
                print(f"Error saving state: {e}")
        else:
            print("No new announcements")
                
    except requests.exceptions.RequestException as e:
        print(f"Network error checking BSE: {e}")
    except Exception as e:
        print(f"Error checking BSE: {e}")

if __name__ == "__main__":
    print("Starting Unitech regulatory tracker...")
    check_announcements()
    print("Check completed successfully!")
