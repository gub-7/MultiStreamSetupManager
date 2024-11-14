import os
import json
import requests
from flask import Flask, request, redirect
import sys
from constants import (
    TWITCH_AUTH_URL, TWITCH_TOKEN_URL, TWITCH_VALIDATE_URL, TWITCH_REDIRECT_URI,
    TWITCH_SERVER_HOST, TWITCH_SERVER_PORT, OAUTH_SCOPES, CREDS_FILENAME
)

app = Flask(__name__)
server = None

# Load environment variables
CLIENT_ID = "" 
CLIENT_SECRET = "" 
TOKEN_PATH = ""

# Function to generate Twitch OAuth URL
def get_auth_url():
    scopes = '+'.join(OAUTH_SCOPES)
    return (
        f"{TWITCH_AUTH_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={TWITCH_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scopes}"
    )

# Function to exchange the authorization code for access and refresh tokens
def exchange_code_for_tokens(auth_code):
    response = requests.post(TWITCH_TOKEN_URL, params={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': TWITCH_REDIRECT_URI
    })
    return response.json()

# Function to save credentials to a file
def save_credentials(tokens, alt_path=""):
    if CLIENT_ID and CLIENT_SECRET:
        tokens.update({
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        })
    path = TOKEN_PATH if not alt_path else alt_path
    creds_path = os.path.join(path, CREDS_FILENAME)
    with open(creds_path, 'w') as creds_file:
        json.dump(tokens, creds_file, indent=2)

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
        save_credentials(tokens)
        # Schedule the server to stop after sending the response
        def shutdown():
            global server
            if server:
                server.shutdown()
        from threading import Timer
        Timer(1.0, shutdown).start()
        return "Twitch authentication successful! You can close this window."
    else:
        return "Error: Failed to get tokens from Twitch", 500

def validate_token(access_token):
    headers = {'Authorization': f'OAuth {access_token}'}
    response = requests.get(TWITCH_VALIDATE_URL, headers=headers)
    return response.status_code == 200

def refresh_token(refresh_token):
    response = requests.post(TWITCH_TOKEN_URL, params={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    return response.json()

# Function to start the Flask server and initiate the auth flow
def handle_existing_token(twitch_creds):
    """Handle cases where we already have tokens"""
    if ('access_token' in twitch_creds and 
            validate_token(twitch_creds['access_token'])):
        print("Access token is valid.")
        return twitch_creds

    if 'refresh_token' in twitch_creds:
        print("Refreshing token...")
        new_tokens = refresh_token(twitch_creds['refresh_token'])
        if 'access_token' in new_tokens:
            save_credentials(new_tokens)
            print("Token refreshed successfully.")
            return new_tokens
    return None

def start_auth_server():
    """Start the local authentication server"""
    from werkzeug.serving import make_server
    global server
    server = make_server(TWITCH_SERVER_HOST, TWITCH_SERVER_PORT, app)
    server.serve_forever()

def perform_auth(creds):
    global CLIENT_ID, CLIENT_SECRET, TOKEN_PATH
    CLIENT_ID = creds['twitch']['client_id']
    CLIENT_SECRET = creds['twitch']['client_secret']
    TOKEN_PATH = creds['path']

    # Try to use existing tokens
    result = handle_existing_token(creds['twitch'])
    if result:
        return result

    # Start new auth flow
    print("Starting authentication process...")
    print(f"Please go to: http://{TWITCH_SERVER_HOST}:{TWITCH_SERVER_PORT}/")
    
    start_auth_server()
    
    # After server stops, read and return the token file
    creds_path = os.path.join(TOKEN_PATH, CREDS_FILENAME)
    with open(creds_path, 'r') as creds_file:
        return json.load(creds_file)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python twitchAuth.py '<credentials_json>'")
        sys.exit(1)
    
    creds = json.loads(sys.argv[1])
    print(creds)
    print(sys.argv)
    perform_auth(creds)
    
