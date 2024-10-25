import os
import json
import subprocess
import time
import twitchAuth
import youtubeAuth
import kikSetup
import instaSetup
import twitchSetup
import youtubeSetup

def get_platforms():
    print("""
          Select streaming platforms.
          1. Youtube
          2. Twitch
          3. Kik
          4. Youtube (portrait)
          5. Instagram (portrait)
          Ex: <1, 3, 4>(1, 3, and 4), <2-4>(2, 3, and 4), <1, 5>(1 and 5)
          """)
    platformStr = input("Your Selection (enter for <1, 2>): ")
    if not platformStr:
        platformStr = "1, 2"

    platforms = []
    for item in platformStr.split(','):
        item = item.strip()
        if '-' in item:
            start, end = map(int, item.split('-'))
            platforms.extend(range(start, end + 1))
        else:
            platforms.append(int(item))

    platform_map = {1: "youtube", 2: "twitch",
                    3: "kik", 4: "youtubep",
                    5: "instagram"}
    return [platform_map[p] for p in platforms if p in platform_map]

def create_creds(platform):
    print(f"Credentials file for {platform} not found.")
    creds = {}
    if platform != 'twitch' and 'youtube' not in platform and platform != 'kik':
        return creds
    
    if platform == 'kik':
        username = input(f'Enter your {platform} username: ')
        url = f"https://www.kik.com/broadcast/{username}"
        print(f"Please visit {url} to find your stream key.")
        subprocess.run(["python", "-m", "webbrowser", "-t", url])
        creds['stream_key'] = input(f'Enter your {platform} stream key: ')
        return creds
    
    creds['client_id'] = input(f'Enter your {platform} client id: ')
    creds['client_secret'] = input(f'Enter your {platform} client secret: ')
    return creds

def load_credentials():
    platforms = get_platforms()
    path = input("Enter path to credsDir (enter for current directory): ")
    if not path:
        path = "./"
    elif not path.startswith('/') or '//' in path:
        print("Malformed path entered. Defaulting to current directory.")
        path = "./"
    
    creds = {}
    for platform in platforms:
        credsPath = os.path.join(path, f'{platform}Creds.json')
        try:
            with open(credsPath, 'r') as credsFile:
                creds[platform] = json.load(credsFile)
        except FileNotFoundError:
            if platform in ['youtube', 'youtubep']:
                other_platform = ('youtubep' if platform == 'youtube' 
                                             else 'youtube')
                other_credsPath = os.path.join(path,
                                                 f'{other_platform}Creds.json')
                if os.path.exists(other_credsPath):
                    copy_creds = input(f"""{platform}Creds.json not found.
Do you want to copy from {other_platform}Creds.json? (y/n): """).lower() == 'y'
                    if copy_creds:
                        with open(other_credsPath, 'r') as other_credsFile:
                            other_creds = json.load(other_credsFile)
                            if 'stream_key' in other_creds:
                                del other_creds['stream_key']
                            creds[platform] = other_creds
                        continue
            creds[platform] = create_creds(platform)
        except json.JSONDecodeError:
            print(f"Invalid JSON in credentials file for {platform}.")
    
    creds["path"] = path
    return creds
        
def get_stream_details():
    title = input("Enter stream title: ")
    description = input("Enter stream description: ")
    category = input("Enter stream category: ")
    game = input("Enter game (enter to skip): ")
    thumbnail = input("Enter thumbnail image file URL (enter to skip): ")
    return title, description, category, game, thumbnail

def main():
    creds = load_credentials()
    title, description, category, game, thumbnail = get_stream_details()
    if "twitch" in creds:
        twitchCreds = twitchAuth.perform_auth(creds)
        twitchSetup.setup_twitch_stream(twitchCreds, title, category)
    if any("youtube" in key for key in creds):
        youtubeCreds = youtubeAuth.perform_auth(creds)
        print(youtubeCreds)
        youtubeSetup.setup_youtube_streams(youtubeCreds, title, description, category, game, thumbnail)
    
if __name__ == "__main__":
    main()




