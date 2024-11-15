import os
import json
import getpass
from encrypt import unjumble_and_load_json
import twitchAuth
import youtubeAuth
import kickSetup
import twitchSetup
import youtubeSetup
import instaSetup
from constants import *

def print_platform_selection_menu():
    print(PLATFORM_SELECTION_MENU)

def parse_platform_selection(platform_str):
    platforms = []
    for item in platform_str.split(','):
        item = item.strip()
        if '-' in item:
            start, end = map(int, item.split('-'))
            platforms.extend(range(start, end + 1))
        else:
            platforms.append(int(item))
    return platforms

def map_platforms_to_names(platforms):
    return [PLATFORM_MAP[p] for p in platforms if p in PLATFORM_MAP]

def get_platforms():
    print_platform_selection_menu()
    platform_str = input("Your Selection (enter for <1, 2>): ") or DEFAULT_PLATFORM_SELECTION
    platforms = parse_platform_selection(platform_str)
    return map_platforms_to_names(platforms)

def create_kick_creds():
    username = input('Enter your kick username: ')
    password = getpass.getpass('Enter your kick password: ')
    use_2fa = input('Do you use 2FA? (y/n): ').lower() == 'y'
    one_time_password = None
    if use_2fa:
        one_time_password = getpass.getpass('Enter your 2FA code: ')
    return {
        'username': username,
        'password': password,
        'one_time_password': one_time_password
    }

def create_other_creds(platform):
    filename = TWITCH_APP_DATA_FILE if platform == PLATFORM_TWITCH else YOUTUBE_APP_DATA_FILE
    try:
        decrypted_data = unjumble_and_load_json(filename, 5)
        return decrypted_data
    except FileNotFoundError:
        print(f"Could not find {filename}")
        return {}
    except Exception as e:
        print(f"Error loading {filename}: {str(e)}")
        return {}

def create_creds(platform):
    print(f"Credentials file for {platform} not found.")
    if platform == PLATFORM_KICK:
        return create_kick_creds()
    elif platform in [PLATFORM_TWITCH, PLATFORM_YOUTUBE, PLATFORM_YOUTUBE_PORTRAIT]:
        return create_other_creds(platform)
    return {}

def prompt_copy_creds(platform, other_platform):
    prompt = (f"{platform}Creds.json not found.\n"
             f"Do you want to copy from {other_platform}Creds.json? (y/n): ")
    return input(prompt).lower() == 'y'

def copy_youtube_creds(platform, path):
    other_platform = PLATFORM_YOUTUBE_PORTRAIT if platform == PLATFORM_YOUTUBE else PLATFORM_YOUTUBE
    other_creds_path = os.path.join(path, CREDS_FILE_TEMPLATE.format(other_platform))
    
    if not os.path.exists(other_creds_path):
        return None
        
    if prompt_copy_creds(platform, other_platform):
        try:
            with open(other_creds_path, 'r') as other_creds_file:
                other_creds = json.load(other_creds_file)
                other_creds.pop('stream_key', None)
                return other_creds
        except (FileNotFoundError, json.JSONDecodeError):
            return None 

    return None

def credentials_file_not_found(platform, path):
    if platform in [PLATFORM_YOUTUBE, PLATFORM_YOUTUBE_PORTRAIT]:
        copied_creds = copy_youtube_creds(platform, path)
        if copied_creds:
            return copied_creds
    return create_creds(platform)

def get_creds_path():
    path = input("Enter path to credsDir (enter for current directory): ")
    if not path or not path.startswith('/') or '//' in path:
        print("Using current directory for credentials.")
        return DEFAULT_CREDS_PATH
    return path

def prompt_creds_update(platform):
    prompt = (f"Would you like to enter new credential info for "
             f"{platform}? (y/n): ")
    return input(prompt).lower() == 'y'

def load_platform_credentials(platform, path):
    creds_path = os.path.join(path, CREDS_FILE_TEMPLATE.format(platform))
    print(creds_path)
    try:
        with open(creds_path, 'r') as creds_file:
            existing_creds = json.load(creds_file)
        if prompt_creds_update(platform):
            os.remove(creds_path)
            return create_creds(platform)
        return existing_creds
    except FileNotFoundError:
        return credentials_file_not_found(platform, path)
    except json.JSONDecodeError:
        print(f"Invalid JSON in credentials file for {platform}.")
        return {}

def load_credentials():
    platforms = get_platforms()
    path = get_creds_path()
    creds = {platform: load_platform_credentials(platform, path) 
             for platform in platforms}
    creds["path"] = path
    return creds

def get_stream_details():
    title = input("Enter stream title: ")
    description = input("Enter stream description: ")
    category = input("Enter stream category: ")
    game = input("Enter game (enter to skip): ")
    thumbnail = input("Enter thumbnail image file URL (enter to skip): ")
    return title, description, category, game, thumbnail

def setup_twitch(creds, title, category):
    twitch_creds = twitchAuth.perform_auth(creds)
    twitchSetup.setup_twitch_stream(twitch_creds, title, category)
    return twitchSetup.get_chat_url(twitch_creds, creds['path'])

def setup_youtube(creds, title, description, category, game, thumbnail):
    youtube_creds = youtubeAuth.perform_auth(creds)
    return youtubeSetup.setup_youtube_streams(
        youtube_creds, 
        title, 
        description,
        category, 
        game, 
        thumbnail
    )

def save_kick_creds(creds):
    kick_creds_path = os.path.join(creds["path"], 
                                   CREDS_FILE_TEMPLATE.format("kick"))

    with open(kick_creds_path, 'w') as f:
        json.dump(creds["kick"], f, indent=4)

def setup_kick(creds, title, category):
    save_kick_creds(creds)
    return kickSetup.setup_kick_stream(creds["kick"], title, category)

def setup_platform_streams(creds, title, description, category, game, thumbnail):
    if "twitch" in creds:
        category_or_game = game if game else category
        setup_twitch(creds, title, category_or_game)
        
    if any("youtube" in key for key in creds):
        setup_youtube(creds, title, description, category, game, thumbnail)
        
    if "kick" in creds:
        category_or_game = game if game else category
        setup_kick(creds, title, category_or_game)
        
    if "instagram" in creds:
        instaSetup.open_instagram()

def main():
    creds = load_credentials()
    title, description, category, game, thumbnail = get_stream_details()
    setup_platform_streams(creds, title, description, category, game, thumbnail)
    print("Stream setup complete")

if __name__ == "__main__":
    main()
