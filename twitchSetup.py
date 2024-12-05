import os
import json
import requests
import webbrowser

from twitchAuth import save_credentials
import twitchAuth
from constants import (
    TWITCH_API_BASE_URL,
    USERS_ENDPOINT,
    SEARCH_CATEGORIES_ENDPOINT,
    CHANNELS_ENDPOINT,
    AUTH_HEADER,
    CLIENT_ID_HEADER,
    CONTENT_TYPE_HEADER,
    JSON_CONTENT_TYPE,
    CHAT_URL_TEMPLATE
)

def _create_auth_headers(creds, include_content_type=False):
    """Create authentication headers for Twitch API requests."""
    headers = {
        AUTH_HEADER: f"Bearer {creds['access_token']}",
        CLIENT_ID_HEADER: creds['client_id']
    }
    if include_content_type:
        headers[CONTENT_TYPE_HEADER] = JSON_CONTENT_TYPE
    return headers

def get_broadcaster_id(creds):
    """Get broadcaster ID from Twitch API."""
    headers = _create_auth_headers(creds)
    url = f"{TWITCH_API_BASE_URL}{USERS_ENDPOINT}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()['data'][0]['id']

    raise Exception(
        f"Error fetching broadcaster ID: {response.status_code} {response.text}"
    )

# Function to search for the game/category by name
def _find_best_matching_game(games, category):
    """Helper function to find the best matching game from search results."""
    best_match = None
    best_score = float('inf')
    category_lower = category.lower()

    for game in games:
        game_name_lower = game['name'].lower()
        if not game_name_lower.startswith(category_lower):
            continue

        score = abs(len(game_name_lower) - len(category_lower))
        if score < best_score:
            best_score = score
            best_match = game

    return best_match

def search_game(category, creds):
    """Search for a game category on Twitch."""
    headers = _create_auth_headers(creds)
    url = (
        f"{TWITCH_API_BASE_URL}"
        f"{SEARCH_CATEGORIES_ENDPOINT}?query={category}"
    )
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(
            f"Error searching game: {response.status_code} {response.text}"
        )

    data = response.json()
    if not data['data']:
        raise Exception(f"No matching category found for {category}")

    best_match = _find_best_matching_game(data['data'], category)
    if not best_match:
        raise Exception(f"No matching category found for {category}")

    return data['data']

# Function to update the Twitch stream with title, game, and description
def update_twitch_stream(broadcaster_id, title, category_id, creds):
    """Update Twitch stream information."""
    headers = _create_auth_headers(creds, include_content_type=True)
    data = {
        "broadcaster_id": broadcaster_id,
        "title": title,
        "game_id": category_id
    }

    url = f"{TWITCH_API_BASE_URL}{CHANNELS_ENDPOINT}"
    response = requests.patch(url, headers=headers, json=data)

    if response.status_code == 204:
        print(
            f"Stream successfully updated on Twitch with "
            f"title: {title} and category: {category_id}"
        )
        return

    raise Exception(
        f"Error updating Twitch stream: {response.status_code} {response.text}"
    )

# Main function to handle Twitch setup
def setup_twitch_stream(creds, title, game = None):
    try:
        broadcaster_id = get_broadcaster_id(creds)
        print(f"Broadcaster ID: {broadcaster_id}")

        games = []
        search_query = game if game else input("Please enter a twitch category: ")

        while not games:
            try:
                games = search_game(search_query, creds)
                if not games:
                    search_query = input(
                        "No games found. Enter another category: "
                    )
            except Exception as e:
                print(f"Search error: {e}")
                search_query = input("Enter another category: ")

        # Only show up to 5 games, but handle smaller lists
        max_display = min(len(games), 5)
        while True:
            for i, game in enumerate(games[:max_display], 1):
                print(f"{i}. {game['name']}")

            try:
                selection = input(f"Select a game (1-{max_display}): ")
                selection_idx = int(selection) - 1

                if 0 <= selection_idx < max_display:
                    selected_game = games[selection_idx]
                    break
                else:
                    print(f"Please enter a number between 1 and {max_display}")
            except ValueError:
                print("Please enter a valid number")

        game_name = selected_game['name']
        category_id = selected_game['id']
        print(f"Selected game: {game_name} (ID: {category_id})")

        update_twitch_stream(broadcaster_id, title, category_id, creds)
    except Exception as e:
        print(f"Error: {e}")

def _fetch_and_save_username(creds, path):
    """Fetch username from Twitch API and save to credentials."""
    headers = _create_auth_headers(creds)
    url = f"{TWITCH_API_BASE_URL}{USERS_ENDPOINT}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(
            f"Error fetching username: {response.status_code} {response.text}"
        )

    username = response.json()['data'][0]['login']
    creds['username'] = username
    twitchAuth.save_credentials(creds, path)
    return username

def get_chat_url(creds, path):
    """Get the Twitch chat URL for the current user."""
    if 'username' not in creds:
        username = _fetch_and_save_username(creds, path)
    else:
        username = creds['username']

    return CHAT_URL_TEMPLATE.format(username=username)

# Example usage (integrated with main.py or other files)
if __name__ == "__main__":
    stream_title = "Exciting Gameplay"
    stream_category = "Fortnite"

    setup_twitch_stream(stream_title, stream_category, {})
