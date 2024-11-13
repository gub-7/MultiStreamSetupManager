import os
import json
import subprocess
import time
import getpass
import twitchAuth
import youtubeAuth
import kickSetup
import instaSetup
import twitchSetup
import youtubeSetup

def print_platform_selection_menu():
    print("""
          Select streaming platforms.
          1. Youtube
          2. Twitch
          3. Kik
          4. Youtube (portrait)
          5. Instagram (portrait)
          Ex: <1, 3, 4>(1, 3, and 4), <2-4>(2, 3, and 4), <1, 5>(1 and 5)
          """)

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
    platform_map = {
        1: "youtube", 2: "twitch", 3: "kick", 
        4: "youtubep", 5: "instagram"
    }
    return [platform_map[p] for p in platforms if p in platform_map]

def get_platforms():
    print_platform_selection_menu()
    platform_str = input("Your Selection (enter for <1, 2>): ") or "1, 2"
    platforms = parse_platform_selection(platform_str)
    return map_platforms_to_names(platforms)

def handle_kick_url(stream_url):
    if not (stream_url.endswith('/app/') or stream_url.endswith('/app')):
        if stream_url.endswith('/'):
            stream_url += 'app/'
        else:
            stream_url += '/app/'
    elif stream_url.endswith('/app'):
        stream_url += '/'
    return stream_url

def create_kick_creds():
    username = input('Enter your kick username: ')
    url = "https://kick.com/dashboard/settings/stream"
    print(f"Please visit {url} to find your stream url & key.")
    subprocess.run(["python", "-m", "webbrowser", "-t", url])
    stream_url = input('Enter your kick stream url: ')
    stream_url = handle_kick_url(stream_url)
    stream_key = getpass.getpass('Enter your kick stream key: ')
    return {
        'username': username,
        'stream_key': stream_key,
        'stream_url': stream_url
    }

def create_other_creds(platform):
    client_id = input(f'Enter your {platform} client id: ')
    client_secret = getpass.getpass(f'Enter your {platform} client secret: ')
    return {'client_id': client_id, 'client_secret': client_secret}

def create_creds(platform):
    print(f"Credentials file for {platform} not found.")
    if platform == 'kick':
        return create_kick_creds()
    elif platform in ['twitch', 'youtube', 'youtubep']:
        return create_other_creds(platform)
    return {}

def copy_youtube_creds(platform, path):
    other_platform = 'youtubep' if platform == 'youtube' else 'youtube'
    other_creds_path = os.path.join(path, f'{other_platform}Creds.json')
    if os.path.exists(other_creds_path):
        copy_creds = input(f"""{platform}Creds.json not found.
Do you want to copy from {other_platform}Creds.json? (y/n): """).lower() == 'y'
        if copy_creds:
            with open(other_creds_path, 'r') as other_creds_file:
                other_creds = json.load(other_creds_file)
                other_creds.pop('stream_key', None)
                return other_creds
    return None

def credentials_file_not_found(platform, path):
    if platform in ['youtube', 'youtubep']:
        copied_creds = copy_youtube_creds(platform, path)
        if copied_creds:
            return copied_creds
    return create_creds(platform)

def get_creds_path():
    path = input("Enter path to credsDir (enter for current directory): ")
    if not path or not path.startswith('/') or '//' in path:
        print("Using current directory for credentials.")
        return "./"
    return path

def load_platform_credentials(platform, path):
    creds_path = os.path.join(path, f'{platform}Creds.json')
    try:
        with open(creds_path, 'r') as creds_file:
            existing_creds = json.load(creds_file)
            update_creds = input(f"Would you like to enter new credential info for "
                                    f"{platform}? (y/n): ").lower() == 'y'
            if update_creds:
                return create_creds(platform)
            else:
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
    twitchSetup.open_chat(twitch_creds, creds['path'])

def setup_youtube(creds, title, description, category, game, thumbnail):
    youtube_creds = youtubeAuth.perform_auth(creds)
    youtubeSetup.setup_youtube_streams(youtube_creds, title, description,
                                       category, game, thumbnail)

def save_kick_creds(creds):
    kick_creds_path = os.path.join(creds["path"], "kickCreds.json")
    with open(kick_creds_path, 'w') as f:
        json.dump(creds["kick"], f, indent=4)

def setup_kick(creds, title, category):
    save_kick_creds(creds)
    kickSetup.setup_kick_stream(creds["kick"], title, category)
    kickSetup.open_kick_chat(creds["kick"]["username"])

def main():
    creds = load_credentials()
    title, description, category, game, thumbnail = get_stream_details()
    if "twitch" in creds:
        setup_twitch(creds, title, category)
    if any("youtube" in key for key in creds):
        setup_youtube(creds, title, description, category, game, thumbnail)
    if "kick" in creds:
        setup_kick(creds, title, category)
    if "instagram" in creds:
        instaSetup.open_instagram()
    print("All set to stream")

if __name__ == "__main__":
    main()
