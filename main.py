import os
import signal
import asyncio
import json
import sys
import getpass
import logging
from encrypt import unjumble_and_load_json
import twitchAuth
import youtubeAuth
import kickSetup
import twitchSetup
import youtubeSetup
import instaSetup
from chatManager import ChatManager, ChatMessage
from chatDisplay import ChatDisplay, create_chat_display
from constants import *

# Silence all logging
logging.getLogger().setLevel(logging.ERROR)
# Silence urllib3 (used by many HTTP clients)
logging.getLogger('urllib3').setLevel(logging.ERROR)
# Silence asyncio logging
logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('websockets').setLevel(logging.ERROR)
logging.getLogger('instagrapi').setLevel(logging.ERROR)
logging.getLogger('youtube').setLevel(logging.ERROR)

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

def create_account_creds(platform):
    username = input(f'Enter your {platform} username: ')
    password = getpass.getpass(f'Enter your {platform} password: ')
    return {
        'username': username,
        'password': password,
    }

def create_auth_creds(platform):
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
    if platform in [PLATFORM_KICK, PLATFORM_INSTAGRAM]:
        return create_account_creds(platform)
    else:
        return create_auth_creds(platform)

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

def setup_twitch(creds, title, game=None):
    twitch_creds = twitchAuth.perform_auth(creds)
    twitchSetup.setup_twitch_stream(twitch_creds, title, game)
    return twitchSetup.get_chat_url(twitch_creds, creds['path'])

def setup_youtube(creds, title, game=None):
    youtube_creds = youtubeAuth.perform_auth(creds)
    return youtubeSetup.setup_youtube_streams(
        youtube_creds,
        title,
        game
    )

def save_creds(creds, platform):
    kick_creds_path = os.path.join(creds["path"],
                                   CREDS_FILE_TEMPLATE.format(platform))

    with open(kick_creds_path, 'w') as f:
        json.dump(creds[platform], f, indent=4)

async def setup_kick(creds, title, game=None):
    save_creds(creds, "kick")
    return await kickSetup.setup_kick_stream(creds["kick"], title, game)

def setup_instagram(creds, title):
    save_creds(creds, "instagram")
    return instaSetup.setup_instagram_stream(creds["instagram"], title)

async def setup_platform_streams(creds):
    chat_urls = []
    forward_processes = []

    title = input("Enter stream title: ")
    game = input("Enter Game title (Enter to skip): ")

    if "twitch" in creds:
        twitch_chat_url = setup_twitch(creds, title, game if game != "" else None)
        chat_urls.append(twitch_chat_url)

    if any("youtube" in key for key in creds):
        youtube_urls = setup_youtube(creds, title, game if game != "" else None)
        if youtube_urls:
            for url in youtube_urls:
                chat_urls.append(url)

    if "kick" in creds:
        kick_url, forward_process = await setup_kick(creds, title, game if game != "" else None)
        if kick_url:
            chat_urls.append(kick_url)
        if forward_process:
            forward_processes.append(forward_process)

    if "instagram" in creds:
        insta_url, forward_process = setup_instagram(creds, title)
        if insta_url:
            chat_urls.append(insta_url)
        if forward_process:
            forward_processes.append(forward_process)

    return chat_urls, forward_processes

def signal_handler(sig, frame):
    print("\nShutting down chat display...")
    sys.exit(0)

async def run_chat_manager(creds, chat_sources, chat_display):
    """Run the chat manager with WebSocket connections and clients"""
    # Initialize chat manager
    cm = ChatManager()

    # Create message handler for chat display
    def handle_chat_message(message: ChatMessage):
        try:
            # Convert ChatManager message to ChatDisplay format
            chat_display.add_message(
                platform=message.platform,
                username=message.username,
                message=message.message
            )
        except Exception as e:
            print(f"Error handling chat message: {str(e)}")

    # Add the message handler to ChatManager
    cm.add_listener(handle_chat_message)

    # Start connections for each platform
    connection_tasks = []
    for source in chat_sources:
        try:
            # Create task and await it immediately to ensure proper setup
            connection_task = asyncio.create_task(cm.start(source))
            await connection_task
            connection_tasks.append(connection_task)
            print(f"Connected to chat: {source if isinstance(source, str) else 'Kick Client'}")
        except Exception as e:
            print(f"Failed to connect to chat {source}: {str(e)}")

    return cm, connection_tasks

async def main():
    try:
        # Load credentials and setup streams
        creds = load_credentials()

        # Ensure stream setup completes before continuing
        try:
            chat_urls, forward_processes = await setup_platform_streams(creds)
            if not chat_urls:
                print("No chat URLs were returned from stream setup. Exiting...")
                return
            print("Stream setup complete")
        except Exception as e:
            print(f"Failed to setup streams: {str(e)}")
            return

        # Initialize chat display with stream processes for monitoring
        process1 = forward_processes[0] if len(forward_processes) > 0 else None
        process2 = forward_processes[1] if len(forward_processes) > 1 else None
        chat_display = create_chat_display(process1, process2)
        chat_display.start()
        signal.signal(signal.SIGINT, signal_handler)

        # Start chat manager and wait for all connections to be established
        chat_manager, connection_tasks = await run_chat_manager(creds, chat_urls, chat_display)
        if not connection_tasks:
            print("No chat connections were established. Exiting...")
            return
        print("\nChat display initialized.")
        if forward_processes:
            print(f"Monitoring {len(forward_processes)} stream processes.")
        print("Press Ctrl+C to exit.")

        # Wait for connections and keep running
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            # Cleanup
            await chat_manager.stop()
            chat_display.stop()

            # Terminate any running stream processes
            for process in forward_processes:
                if process and process.poll() is None:
                    try:
                        process.terminate()
                        process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
                    except:
                        process.kill()  # Force kill if graceful shutdown fails

            # Cancel any pending tasks
            for task in connection_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            print("Chat display stopped.")

    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Program terminated with error: {str(e)}")
