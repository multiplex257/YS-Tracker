# YS-Tracker
#YS-Tracker is to track live event
print("before import")
import os
import json
import time
from bse import BSE  # Use the BseIndiaApi package

print("before bse")
STATE_FILE = "last_announcement.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_alert(message):
    print(f"ALERT: {message}")
    
    # Optional: Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def check_announcements():
    try:
        # Use BseIndiaApi to fetch announcements
        bse = BSE()
        
        # Unitech Ltd Scrip Code: 507878
        announcements = bse.announcements(scripcode='507878')
        
        if not announcements or len(announcements) == 0:
            print("No announcements found")
            return
        
        # Get the latest announcement
        latest = announcements[0]
        
        # Extract details
        news_id = latest.get('NEWSID') or latest.get('news_id')
        head = latest.get('NEWSSUB') or latest.get('subject')
        details = latest.get('MORE') or latest.get('details', '')
        
        # Load previous state
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_state = json.load(f)
        else:
            last_state = {}
        
        # Check for new updates
        if last_state.get("NEWSID") != news_id:
            # Look for indicators regarding the CMD or Director changes
            keywords = ["CMD", "TENURE", "EXTENSION", "DIRECTOR", "MALIK", "YUDHVIR"]
            text_to_check = f"{head} {details}".upper()
            
            is_relevant = any(kw in text_to_check for kw in keywords)
            
            if is_relevant:
                alert_msg = f"⚠️ UNITECH REGULATORY UPDATE ⚠️\n\nHeading: {head}\nDetails: {details}"
                send_alert(alert_msg)
            
            # Save new state
            with open(STATE_FILE, "w") as f:
                json.dump({"NEWSID": news_id}, f)
                
    except Exception as e:
        print(f"Error checking BSE: {e}")

if __name__ == "__main__":
    print("Starting Unitech regulatory tracker...")
    check_announcements()
    print("Check completed successfully!")
