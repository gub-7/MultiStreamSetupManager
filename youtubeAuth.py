import os
import json
import requests
from flask import Flask, request, redirect
import sys
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from constants import (
    YOUTUBE_AUTH_URL, YOUTUBE_TOKEN_URL, YOUTUBE_REDIRECT_URI, SCOPES,
    YOUTUBE_CREDS_FILE, YOUTUBE_PORTRAIT_CREDS_FILE,
    TOKEN_INFO_URL, YOUTUBE_SERVER_HOST, YOUTUBE_SERVER_PORT
)
app = Flask(__name__)
server = None

# Load environment variables
CLIENT_ID = "" 
CLIENT_SECRET = "" 
TOKEN_PATH = ""
IS_PORTRAIT = False

# Function to generate YouTube OAuth URL
def _create_flow_config():
    """Create the OAuth flow configuration dictionary."""
    return {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": YOUTUBE_AUTH_URL,
            "token_uri": YOUTUBE_TOKEN_URL,
        }
    }

def get_auth_url():
    """Generate YouTube OAuth URL."""
    flow = Flow.from_client_config(_create_flow_config(), scopes=SCOPES)
    flow.redirect_uri = YOUTUBE_REDIRECT_URI
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return authorization_url

# Function to exchange the authorization code for access and refresh tokens
def exchange_code_for_tokens(auth_code):
    """Exchange authorization code for access and refresh tokens."""
    flow = Flow.from_client_config(_create_flow_config(), scopes=SCOPES)
    flow.redirect_uri = YOUTUBE_REDIRECT_URI
    flow.fetch_token(code=auth_code)
    
    return {
        'access_token': flow.credentials.token,
        'refresh_token': flow.credentials.refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

# Function to save credentials to a file
def save_credentials(tokens, account_type):
    """Save credentials to a file."""
    tokens['client_id'] = CLIENT_ID
    tokens['client_secret'] = CLIENT_SECRET
    filename = (YOUTUBE_CREDS_FILE if account_type == 'youtube' 
               else YOUTUBE_PORTRAIT_CREDS_FILE)
    with open(f'{TOKEN_PATH}{filename}', 'w') as creds_file:
        json.dump(tokens, creds_file, indent=2)

# OAuth login page route
@app.route('/')
def index():
    auth_url = get_auth_url()
    return redirect(auth_url)

# OAuth callback route
@app.route('/callback')
def callback():
    global CLIENT_ID, CLIENT_SECRET, server, IS_PORTRAIT
    auth_code = request.args.get('code')
    if not auth_code:
        return "Error: No authorization code returned", 400

    # Exchange the authorization code for access and refresh tokens
    tokens = exchange_code_for_tokens(auth_code)

    if 'access_token' in tokens:
        save_credentials(tokens, 'youtubep' if IS_PORTRAIT else 'youtube')  # Default to 'youtube', adjust if needed
        # Schedule the server shutdown
        def shutdown():
            server.shutdown()
        from threading import Timer
        Timer(1.0, shutdown).start()
        return "YouTube authentication successful! This window will close automatically."
    else:
        return "Error: Failed to get tokens from YouTube", 500

def validate_token(access_token):
    """Validate the access token with Google's API."""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(TOKEN_INFO_URL, headers=headers)
    return response.status_code == 200

def refresh_token(refresh_token):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(YOUTUBE_TOKEN_URL, data=data)
    creds = response.json()
    creds['refresh_token'] = refresh_token
    return creds

# Function to start the Flask server and initiate the auth flow
def _handle_token_refresh(creds, account_type, copied):
    """Handle token refresh for an account type."""
    print(f"Refreshing token for {account_type}...")
    new_tokens = refresh_token(creds[account_type]['refresh_token'])
    
    if 'access_token' not in new_tokens:
        return copied, None
        
    save_credentials(new_tokens, account_type)
    print(f"Token for {account_type} refreshed successfully.")
    
    if account_type == 'youtube' and 'youtubep' in creds:
        if _should_copy_credentials():
            save_credentials(new_tokens, 'youtubep')
            creds['youtubep'] = new_tokens.copy()
            return True, new_tokens
    
    return copied, new_tokens

def _should_copy_credentials():
    """Ask user if credentials should be copied to portrait account."""
    prompt = ("Would you like to use the same credentials for your other "
             "youtubeStream? (y/n): ")
    return input(prompt).lower() == 'y'

def _start_auth_server():
    """Start the authentication server."""
    global server
    from werkzeug.serving import make_server
    server = make_server(YOUTUBE_SERVER_HOST, YOUTUBE_SERVER_PORT, app)
    server.serve_forever()

def perform_auth(creds):
    """Perform authentication for YouTube accounts."""
    global CLIENT_ID, CLIENT_SECRET, TOKEN_PATH
    TOKEN_PATH = creds['path']
    copied = False
    
    for account_type in ['youtube', 'youtubep']:
        global IS_PORTRAIT
        IS_PORTRAIT = account_type == 'youtubep'
        
        if account_type not in creds or copied:
            continue
            
        CLIENT_ID = creds[account_type]['client_id']
        CLIENT_SECRET = creds[account_type]['client_secret']

        if ('access_token' in creds[account_type] and 
                validate_token(creds[account_type]['access_token'])):
            print(f"Access token for {account_type} is valid.")
            continue

        if 'refresh_token' in creds[account_type]:
            copied, new_tokens = _handle_token_refresh(creds, account_type, copied)
            if new_tokens:
                creds[account_type] = new_tokens
                continue

        print(f"Starting authentication process for {account_type}...")
        print("Please go to the following URL to authenticate with YouTube: "
              f"http://{YOUTUBE_SERVER_HOST}:{YOUTUBE_SERVER_PORT}/")
        
        _start_auth_server()
            
        # After auth, load the new credentials
        try:
            with open(f'{TOKEN_PATH}{"youtubeCreds.json" if account_type == "youtube" else "youtubepCreds.json"}', 'r') as f:
                new_creds = json.load(f)
                creds[account_type] = new_creds
                
                if account_type == 'youtube' and 'youtubep' in creds and not copied:
                    copyOption = input("Would you like to use the same credentials for your other youtubeStream? (y/n): ").lower()
                    if copyOption == 'y':
                        save_credentials(new_creds, 'youtubep')
                        creds['youtubep'] = new_creds.copy()
                        copied = True
        except FileNotFoundError:
            print(f"Warning: Could not load credentials file for {account_type}")

    return_creds = {}
    try:
        with open(f'{TOKEN_PATH}youtubeCreds.json', 'r') as f:
            return_creds['youtube'] = json.load(f)
    except FileNotFoundError:
        pass
        
    try:
        with open(f'{TOKEN_PATH}youtubepCreds.json', 'r') as f:
            return_creds['youtubep'] = json.load(f)
    except FileNotFoundError:
        pass
        
    return return_creds

def get_live_streams(access_token):
    youtube = build('youtube', 'v3', credentials=None)
    youtube._http.credentials = Credentials(token=access_token)
    
    request = youtube.liveStreams().list(
        part="snippet,cdn",
        mine=True
    )
    response = request.execute()
    return response.get('items', [])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python youtubeAuth.py '<credentials_json>'")
        sys.exit(1)
    
    creds = json.loads(sys.argv[1])
    perform_auth(creds)
