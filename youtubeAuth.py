import os
import json
import requests
from flask import Flask, request, redirect
import sys
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
app = Flask(__name__)

# Load environment variables
CLIENT_ID = "" 
CLIENT_SECRET = "" 
TOKEN_PATH = ""
REDIRECT_URI = 'http://localhost:3000/callback'
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# Function to generate YouTube OAuth URL
def get_auth_url():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": AUTH_URL,
                "token_uri": TOKEN_URL,
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return authorization_url

# Function to exchange the authorization code for access and refresh tokens
def exchange_code_for_tokens(auth_code):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": AUTH_URL,
                "token_uri": TOKEN_URL,
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=auth_code)
    return {
        'access_token': flow.credentials.token,
        'refresh_token': flow.credentials.refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

# Function to save credentials to a file
def save_credentials(tokens, account_type):
    tokens['client_id'] = CLIENT_ID
    tokens['client_secret'] = CLIENT_SECRET
    filename = 'youtubeCreds.json' if account_type == 'youtube' else 'youtubepCreds.json'
    with open(f'{TOKEN_PATH}{filename}', 'w') as creds_file:
        json.dump(tokens, creds_file, indent=2)
        print(tokens)

# OAuth login page route
@app.route('/')
def index():
    auth_url = get_auth_url()
    return redirect(auth_url)

# OAuth callback route
@app.route('/callback')
def callback():
    global CLIENT_ID, CLIENT_SECRET
    auth_code = request.args.get('code')
    if not auth_code:
        return "Error: No authorization code returned", 400

    # Exchange the authorization code for access and refresh tokens
    tokens = exchange_code_for_tokens(auth_code)

    if 'access_token' in tokens:
        save_credentials(tokens, 'youtube')  # Default to 'youtube', adjust if needed
        return "YouTube authentication successful! You can close this window, close the server, and re-run main.py"
    else:
        return "Error: Failed to get tokens from YouTube", 500

def validate_token(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get('https://www.googleapis.com/oauth2/v1/tokeninfo', headers=headers)
    return response.status_code == 200

def refresh_token(refresh_token):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(TOKEN_URL, data=data)
    creds = response.json()
    creds['refresh_token'] = refresh_token
    return creds

# Function to start the Flask server and initiate the auth flow
def perform_auth(creds):
    global CLIENT_ID, CLIENT_SECRET, TOKEN_PATH
    TOKEN_PATH = creds['path']

    for account_type in ['youtube', 'youtubep']:
        if account_type in creds:
            CLIENT_ID = creds[account_type]['client_id']
            CLIENT_SECRET = creds[account_type]['client_secret']

            if 'access_token' in creds[account_type] and validate_token(creds[account_type]['access_token']):
                print(f"Access token for {account_type} is valid.")
                continue

            if 'refresh_token' in creds[account_type]:
                print(f"Refreshing token for {account_type}...")
                new_tokens = refresh_token(creds[account_type]['refresh_token'])
                if 'access_token' in new_tokens:
                    save_credentials(new_tokens, account_type)
                    print(f"Token for {account_type} refreshed successfully.")
                    continue

            print(f"Starting authentication process for {account_type}...")
            print(f"Please go to the following URL to authenticate with YouTube: http://localhost:3000/")
            
            app.run(port=3000)

    return creds

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
    print(creds)
    print(sys.argv)
    perform_auth(creds)
