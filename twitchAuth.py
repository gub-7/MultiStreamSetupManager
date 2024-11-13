import os
import json
import requests
from flask import Flask, request, redirect
import sys

app = Flask(__name__)

# Load environment variables
CLIENT_ID = "" 
CLIENT_SECRET = "" 
TOKEN_PATH = ""
REDIRECT_URI = 'http://localhost:3000/callback'
AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TOKEN_URL = "https://id.twitch.tv/oauth2/token"

# Function to generate Twitch OAuth URL
def get_auth_url():
    return (f"{AUTH_URL}?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=user:read:email+channel:manage:broadcast")

# Function to exchange the authorization code for access and refresh tokens
def exchange_code_for_tokens(auth_code):
    response = requests.post(TOKEN_URL, params={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    })
    return response.json()

# Function to save credentials to a file
def save_credentials(tokens, altPath = ""):
    if CLIENT_ID != "" and CLIENT_SECRET != "":
        tokens['client_id'] = CLIENT_ID
        tokens['client_secret'] = CLIENT_SECRET
    path  = TOKEN_PATH if altPath == "" else altPath
    with open(f'{path}twitchCreds.json', 'w') as creds_file:
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
        return "Twitch authentication successful! You can close this window, close the server, and re-run main.py"
    else:
        return "Error: Failed to get tokens from Twitch", 500

def validate_token(access_token):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get('https://id.twitch.tv/oauth2/validate', headers=headers)
    return response.status_code == 200

def refresh_token(refresh_token):
    response = requests.post(TOKEN_URL, params={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    return response.json()

# Function to start the Flask server and initiate the auth flow
def perform_auth(creds):
    global CLIENT_ID, CLIENT_SECRET, TOKEN_PATH
    CLIENT_ID = creds['twitch']['client_id']
    CLIENT_SECRET = creds['twitch']['client_secret']
    TOKEN_PATH = creds['path']

    if 'access_token' in creds['twitch'] and validate_token(creds['twitch']['access_token']):
        print("Access token is valid.")
        return creds['twitch']

    if 'refresh_token' in creds['twitch']:
        print("Refreshing token...")
        new_tokens = refresh_token(creds['twitch']['refresh_token'])
        if 'access_token' in new_tokens:
            save_credentials(new_tokens)
            print("Token refreshed successfully.")
            return new_tokens

    print("Starting authentication process...")
    print(f"Please go to the following URL to authenticate with Twitch: http://localhost:3000/")
    
    app.run(port=3000)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python twitchAuth.py '<credentials_json>'")
        sys.exit(1)
    
    creds = json.loads(sys.argv[1])
    print(creds)
    print(sys.argv)
    perform_auth(creds)
    
