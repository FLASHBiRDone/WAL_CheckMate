import os
import time
import threading
import logging
import sys
from datetime import datetime
import pytz
from flask import Flask, render_template, Response, jsonify, request, stream_with_context
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.user import User
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
import json
import sqlite3
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables
load_dotenv()

# Set timezone
oslo_tz = pytz.timezone('Europe/Oslo')

# Initialize Slack client
slack_token = os.getenv('SLACK_BOT_TOKEN')
slack_client = WebClient(token=slack_token)
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#checkmate')
NGROK_URL = os.getenv('NGROK_URL')

app = Flask(__name__)

# Global variables to store the campaign data and last update time
campaign_data = {'visible': {}, 'hidden': {}}
last_update_time = None

def init_db():
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hidden_accounts
                 (account_id TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hidden_campaigns
                 (campaign_id TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notified_campaigns
                 (campaign_id TEXT PRIMARY KEY, notification_time TIMESTAMP)''')
    conn.commit()
    conn.close()
    logging.info("Database initialized")

def is_account_hidden(account_id):
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM hidden_accounts WHERE account_id = ?", (account_id,))
    result = c.fetchone() is not None
    conn.close()
    return result

def toggle_account_visibility(account_id, hide=True):
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    if hide:
        c.execute("INSERT OR REPLACE INTO hidden_accounts (account_id) VALUES (?)", (account_id,))
        logging.info(f"Account {account_id} is now hidden")
    else:
        c.execute("DELETE FROM hidden_accounts WHERE account_id = ?", (account_id,))
        logging.info(f"Account {account_id} is now visible")
    conn.commit()
    conn.close()

def is_campaign_hidden(campaign_id):
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM hidden_campaigns WHERE campaign_id = ?", (campaign_id,))
    result = c.fetchone() is not None
    conn.close()
    return result

def hide_campaign(campaign_id):
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO hidden_campaigns (campaign_id) VALUES (?)", (campaign_id,))
    conn.commit()
    conn.close()
    logging.info(f"Campaign {campaign_id} is now hidden")

def is_campaign_notified(campaign_id):
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM notified_campaigns WHERE campaign_id = ?", (campaign_id,))
    result = c.fetchone() is not None
    conn.close()
    return result

def mark_campaign_notified(campaign_id):
    conn = sqlite3.connect('hidden_accounts.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO notified_campaigns (campaign_id, notification_time) VALUES (?, ?)", 
              (campaign_id, datetime.now(oslo_tz).strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_accessible_ad_accounts(access_token):
    FacebookAdsApi.init(access_token=access_token)
    me = User(fbid='me')
    ad_accounts = me.get_ad_accounts(fields=['name', 'id'])
    logging.info(f"Retrieved {len(ad_accounts)} ad accounts")
    return ad_accounts

def send_slack_message(message, blocks=None):
    try:
        response = slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=message, blocks=blocks)
        logging.info(f"Message sent to Slack channel {SLACK_CHANNEL}")
    except SlackApiError as e:
        logging.error(f"Error sending message to Slack: {e}")

def check_daily_budget_campaigns(ad_account):
    campaigns = []
    params = {'limit': 100}  # Adjust the limit as needed
    
    while True:
        page = ad_account.get_campaigns(
            fields=['name', 'daily_budget', 'lifetime_budget', 'status', 'effective_status', 'stop_time'],
            params=params
        )
        campaigns.extend(page)
        
        if 'next' in page:
            params = {'after': page['next']}
            time.sleep(1)  # Add a 1-second delay between requests
        else:
            break
    
    daily_budget_campaigns = []
    hidden_daily_budget_campaigns = []
    new_daily_budget_campaigns = []
    current_time = datetime.now(oslo_tz)
    
    for campaign in campaigns:
        stop_time = campaign.get('stop_time')
        if stop_time:
            stop_time = datetime.strptime(stop_time, "%Y-%m-%dT%H:%M:%S%z").astimezone(oslo_tz)
        
        if (campaign.get('daily_budget') and 
            not campaign.get('lifetime_budget') and 
            campaign.get('effective_status') in ['ACTIVE', 'SCHEDULED', 'IN_PROCESS'] and
            (not stop_time or stop_time > current_time)):
            campaign_info = {
                'name': campaign.get('name', 'Unknown'),
                'id': campaign.get('id', 'Unknown'),
                'status': campaign.get('status', 'Unknown'),
                'effective_status': campaign.get('effective_status', 'Unknown'),
                'stop_time': stop_time.strftime("%Y-%m-%d %H:%M:%S") if stop_time else 'No end date',
                'url': f"https://business.facebook.com/adsmanager/manage/campaigns?act={ad_account['id']}&selected_campaign_ids={campaign.get('id', '')}"
            }
            if is_campaign_hidden(campaign_info['id']):
                hidden_daily_budget_campaigns.append(campaign_info)
            else:
                daily_budget_campaigns.append(campaign_info)
                if not is_campaign_notified(campaign_info['id']):
                    new_daily_budget_campaigns.append(campaign_info)
                    mark_campaign_notified(campaign_info['id'])
    
    if new_daily_budget_campaigns:
        message = f"New daily budget campaigns found for account {ad_account['name']} (ID: {ad_account['id']}):"
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            }
        ]
        for campaign in new_daily_budget_campaigns:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Campaign:* {campaign['name']}\n*Ad Account:* {ad_account['name']}\n*URL:* {campaign['url']}"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Stop notifications for this campaign"},
                    "value": f"stop_notif_{campaign['id']}",
                    "action_id": f"stop_notif_{campaign['id']}"
                }
            })
        send_slack_message(message, blocks)
    
    logging.info(f"Found {len(daily_budget_campaigns)} visible, {len(hidden_daily_budget_campaigns)} hidden, and {len(new_daily_budget_campaigns)} new campaigns with daily budget for account {ad_account['id']}")
    return daily_budget_campaigns, hidden_daily_budget_campaigns

def update_campaign_data(selected_accounts=None):
    global campaign_data, last_update_time
    logging.info("Starting campaign data update...")
    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    
    if not access_token:
        logging.error("Access token not found. Make sure FACEBOOK_ACCESS_TOKEN is set in your .env file.")
        return
    
    FacebookAdsApi.init(access_token=access_token)
    
    ad_accounts = get_accessible_ad_accounts(access_token)
    
    new_campaign_data = {'visible': {}, 'hidden': {}}
    
    total_accounts = len(ad_accounts)
    processed_accounts = 0

    for ad_account in ad_accounts:
        account_is_hidden = is_account_hidden(ad_account['id'])
        if selected_accounts is not None:
            if ad_account['id'] not in selected_accounts and not account_is_hidden:
                toggle_account_visibility(ad_account['id'], hide=True)
                account_is_hidden = True
            elif ad_account['id'] in selected_accounts and account_is_hidden:
                toggle_account_visibility(ad_account['id'], hide=False)
                account_is_hidden = False
        
        if account_is_hidden:
            logging.info(f"Skipping hidden account {ad_account['name']} (ID: {ad_account['id']})")
            new_campaign_data['hidden'][ad_account['name']] = {'id': ad_account['id'], 'campaigns': [], 'hidden_campaigns': []}
        else:
            logging.info(f"Checking ad account: {ad_account['name']} (ID: {ad_account['id']})")
            daily_budget_campaigns, hidden_daily_budget_campaigns = check_daily_budget_campaigns(ad_account)
            account_data = {
                'id': ad_account['id'],
                'campaigns': daily_budget_campaigns,
                'hidden_campaigns': hidden_daily_budget_campaigns
            }
            new_campaign_data['visible'][ad_account['name']] = account_data
            logging.info(f"Added {len(daily_budget_campaigns)} visible and {len(hidden_daily_budget_campaigns)} hidden campaigns to visible account {ad_account['name']}")
        
        processed_accounts += 1
        progress = int((processed_accounts / total_accounts) * 100)
        yield f"data: {progress}\n\n"
        
        time.sleep(2)  # Add a 2-second delay between checking different ad accounts
    
    campaign_data = new_campaign_data
    last_update_time = datetime.now(oslo_tz).strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Campaign data update completed. Last update time: {last_update_time}")
    yield f"data: 100\n\n"

def scheduled_update():
    while True:
        logging.info("Starting scheduled update")
        list(update_campaign_data())  # Convert generator to list to execute it
        logging.info("Scheduled update completed. Sleeping for 3 hours.")
        time.sleep(3 * 60 * 60)  # Sleep for 3 hours

@app.route('/')
def index():
    logging.info("Serving index page")
    return render_template('index.html')

@app.route('/data')
def data():
    logging.info("Serving campaign data")
    return Response(json.dumps(campaign_data), mimetype='application/json')

@app.route('/check', methods=['POST'])
def manual_check():
    logging.info("Manual check initiated")
    selected_accounts = request.json.get('selected_accounts', None)
    if selected_accounts:
        logging.info(f"Checking {len(selected_accounts)} selected accounts")
    else:
        logging.info("Checking all accounts")
    return Response(stream_with_context(update_campaign_data(selected_accounts)), content_type='text/event-stream')

@app.route('/last_update')
def get_last_update():
    logging.info(f"Serving last update time: {last_update_time}")
    return jsonify({"last_update": last_update_time})

@app.route('/toggle_visibility', methods=['POST'])
def toggle_visibility():
    account_id = request.json['account_id']
    hide = request.json.get('hide', True)
    logging.info(f"{'Hiding' if hide else 'Showing'} account {account_id}")
    toggle_account_visibility(account_id, hide)
    return jsonify({"status": "success"})

@app.route('/hide_campaign', methods=['POST'])
def hide_campaign_route():
    campaign_id = request.json['campaign_id']
    logging.info(f"Hiding campaign {campaign_id}")
    hide_campaign(campaign_id)
    return jsonify({"status": "success"})

@app.route('/get_accounts')
def get_accounts():
    logging.info("Fetching account list")
    access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    FacebookAdsApi.init(access_token=access_token)
    ad_accounts = get_accessible_ad_accounts(access_token)
    accounts = [{"id": account['id'], "name": account['name'], "hidden": is_account_hidden(account['id'])} for account in ad_accounts]
    logging.info(f"Returning list of {len(accounts)} accounts")
    return jsonify(accounts)

@app.route('/slack/actions', methods=['POST'])
def slack_actions():
    logging.info("Received Slack action")
    logging.info(f"Content-Type: {request.headers.get('Content-Type')}")
    logging.info(f"Request data: {request.get_data(as_text=True)}")

    if request.headers.get('Content-Type') == 'application/json':
        logging.info("Handling JSON request")
        data = request.get_json()
        logging.info(f"JSON data: {data}")
        if data and 'challenge' in data:
            return jsonify({"challenge": data["challenge"]})
        elif data and 'event' in data and data['event'].get('type') == 'message':
            text = data['event'].get('text', '').strip().lower()
            if text == '/sjekk':
                logging.info("Received /sjekk command. Initiating scan.")
                threading.Thread(target=handle_sjekk_command).start()
                return jsonify({"status": "success"})
    elif request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        logging.info("Handling form data request")
        payload = request.form.get('payload')
        if payload:
            data = json.loads(payload)
            logging.info(f"Form payload: {data}")
            if 'actions' in data and len(data['actions']) > 0:
                action = data['actions'][0]
                if action['action_id'].startswith('stop_notif_'):
                    campaign_id = action['value'].split('_')[-1]
                    hide_campaign(campaign_id)
                    return jsonify({"response_action": "clear"})

    logging.error("Unknown Slack action received")
    return jsonify({"error": "Unknown action"}), 400

def handle_sjekk_command():
    send_slack_message("Starting a new scan. This may take a few minutes...")
    list(update_campaign_data())  # Run the update
    send_slack_message("Scan completed. You can view the results on the web interface.")

if __name__ == '__main__':
    logging.info("Initializing application")
    init_db()
    # Start the scheduled update in a separate thread
    update_thread = threading.Thread(target=scheduled_update)
    update_thread.start()
    logging.info("Scheduled update thread started")
    
    # Run the Flask app
    logging.info("Starting Flask app...")
    app.run(host='0.0.0.0', port=5003)