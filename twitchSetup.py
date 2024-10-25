import os
import json
import requests

# Load environment variables
TWITCH_CLIENT_ID = ""
TWITCH_CLIENT_SECRET = ""
TWITCH_API_BASE_URL = "https://api.twitch.tv/helix"

# Function to get broadcaster ID
def get_broadcaster_id(creds):
    headers = {
        "Authorization": f"Bearer {creds['token']}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    url = f"{TWITCH_API_BASE_URL}/users"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        broadcaster_id = data['data'][0]['id']
        return broadcaster_id
    else:
        raise Exception(f"Error fetching broadcaster ID: {response.status_code} {response.text}")

# Function to search for the game/category by name
def search_game(category, creds):
    headers = {
        "Authorization": f"Bearer {creds['token']}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    url = f"{TWITCH_API_BASE_URL}/search/categories?query={category}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if len(data['data']) > 0:
            game_data = data['data'][0]  # Take the first match
            return game_data['id'], game_data['name']
        else:
            raise Exception(f"No matching category found for {category}")
    else:
        raise Exception(f"Error searching game: {response.status_code} {response.text}")

# Function to update the Twitch stream with title, game, and description
def update_twitch_stream(broadcaster_id, title, category_id, creds):
    headers = {
        "Authorization": f"Bearer {creds['token']}",
        "Client-Id": TWITCH_CLIENT_ID,
        "Content-Type": "application/json"
    }
    data = {
        "broadcaster_id": broadcaster_id,
        "title": title,
        "game_id": category_id
    }

    url = f"{TWITCH_API_BASE_URL}/channels"
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 204:
        print(f"Stream successfully updated on Twitch with title: {title} and category: {category_id}")
    else:
        raise Exception(f"Error updating Twitch stream: {response.status_code} {response.text}")

# Main function to handle Twitch setup
def setup_twitch_stream(creds, title, category):
    try:
        broadcaster_id = get_broadcaster_id(creds)
        print(f"Broadcaster ID: {broadcaster_id}")
        
        category_id, game_name = search_game(category, creds)
        print(f"Selected game: {game_name} (ID: {category_id})")
        
        update_twitch_stream(broadcaster_id, title, category_id, creds)
    except Exception as e:
        print(f"Error: {e}")

# Example usage (integrated with main.py or other files)
if __name__ == "__main__":
    stream_title = "Exciting Gameplay"
    stream_category = "Fortnite"
    
    setup_twitch_stream(stream_title, stream_category, {})

