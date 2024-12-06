import os
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from datetime import datetime, timezone, timedelta
import webbrowser
from difflib import get_close_matches
from constants import *

IS_PORTRAIT = False
def _fetch_categories(youtube):
    """Fetch available YouTube categories."""
    try:
        request = youtube.videoCategories().list(
            part="snippet",
            regionCode=REGION_CODE
        )
        response = request.execute()

        if not response or 'items' not in response:
            print("Error: Failed to fetch YouTube categories. No data received.")
            return None

        return response
    except Exception as e:
        print(f"Error fetching YouTube categories: {str(e)}")
        raise

def _create_category_mapping(response):
    """Create a mapping of category names to IDs."""
    return {
        item['snippet']['title'].lower(): item['id']
        for item in response.get('items', [])
    }

def get_category_id(youtube, category_name):
    """Get category ID from category name with fuzzy matching."""
    try:
        # Special handling for Gaming category
        if category_name.lower() == 'gaming':
            return "20"  # Gaming category ID

        response = _fetch_categories(youtube)
        if not response:
            return DEFAULT_CATEGORY_ID

        categories = _create_category_mapping(response)
        category_names = list(categories.keys())

        matches = get_close_matches(
            category_name.lower(),
            category_names,
            n=CATEGORY_MATCH_COUNT,
            cutoff=CATEGORY_MATCH_CUTOFF
        )

        if matches:
            matched_name = matches[0]
            category_id = categories[matched_name]
            return category_id

        return DEFAULT_CATEGORY_ID

    except Exception as e:
        print(f"Error getting category ID: {e}")
        return DEFAULT_CATEGORY_ID

def create_stream_key(youtube, title):
    """Create a new YouTube stream key."""
    try:
        stream_body = {
            "snippet": {"title": title},
            "cdn": {
                "frameRate": FRAME_RATE,
                "ingestionType": INGESTION_TYPE,
                "resolution": RESOLUTION
            }
        }

        request = youtube.liveStreams().insert(
            part="snippet,cdn",
            body=stream_body
        )
        response = request.execute()

        return {
            'key': response['cdn']['ingestionInfo']['streamName'],
            'id': response['id']
        }
    except Exception as e:
        print(f"Error creating stream key: {str(e)}")
        return None

def _process_stream_item(item):
    """Process a single stream item from YouTube API response."""
    return {
        'key': item['cdn']['ingestionInfo']['streamName'],
        'id': item['id']
    }

def get_existing_stream_keys(youtube):
    """Retrieve existing stream keys from YouTube."""
    try:
        request = youtube.liveStreams().list(
            part="snippet,cdn,id",
            mine=True
        )
        response = request.execute()

        stream_keys = []
        for item in response.get('items', []):
            stream_data = _process_stream_item(item)
            stream_data['title'] = item['snippet']['title']
            stream_keys.append(stream_data)

        return stream_keys
    except Exception:
        return []

# Upload a thumbnail to a YouTube live stream
def upload_thumbnail(youtube, video_id, thumbnail_fileURL):
    """Upload a thumbnail to a YouTube live stream."""
    try:
        if not os.path.exists(thumbnail_fileURL):
            print(f"Error: Thumbnail file not found at {thumbnail_fileURL}")
            raise FileNotFoundError(
                f"Thumbnail file not found at {thumbnail_fileURL}"
            )

        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumbnail_fileURL
        )
        request.execute()
    except Exception as e:
        print(f"Error uploading thumbnail: {str(e)}")

# Function to set up YouTube live streams
def _build_youtube_client(creds, key):
    """Build YouTube API client from credentials."""
    return googleapiclient.discovery.build(
        "youtube",
        "v3",
        credentials=Credentials.from_authorized_user_info(creds[key])
    )

def _get_stream_clients(creds):
    """Get list of YouTube clients to set up."""
    streams = []
    for key in creds:
        if 'youtube' in key.lower():
            streams.append((key, _build_youtube_client(creds, key)))
    return streams

def _create_stream_details(title, description, category_id, start_time, made_for_kids, game=None):
    """Create stream details dictionary."""
    details = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": str(category_id),
            "scheduledStartTime": start_time
        },
        "status": {
            "privacyStatus": PRIVACY_STATUS,
            "selfDeclaredMadeForKids": made_for_kids
        },
        "contentDetails": {
            "enableAutoStart": ENABLE_AUTO_START,
            "enableAutoStop": ENABLE_AUTO_STOP,
            "enableDvr": ENABLE_DVR,
            "enableContentEncryption": ENABLE_CONTENT_ENCRYPTION,
            "enableEmbed": ENABLE_EMBED,
            "recordFromStart": RECORD_FROM_START,
            "startWithSlate": START_WITH_SLATE
        }
    }

    if category_id == DEFAULT_CATEGORY_ID and game:
        details["snippet"]["gameTitle"] = game

    return details

def _handle_single_stream(yt_client, stream_type, stream_info, details,
                         thumbnail_fileURL):
    """Handle setup for a single stream."""
    print(stream_info)
    info = stream_info.get(stream_type)
    if not info:
        print(f"No stream information found for {stream_type}. Skipping.")
        return None

    broadcast_request = yt_client.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body=details
    )
    broadcast_response = broadcast_request.execute()
    broadcast_id = broadcast_response["id"]

    bind_request = yt_client.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=info['id']
    )
    bind_request.execute()

    if thumbnail_fileURL:
        upload_thumbnail(yt_client, broadcast_id, thumbnail_fileURL)

    # Generate chat URL using broadcast ID
    chat_url = f"https://youtube.com/live_chat?v={broadcast_id}"
    print(f"Chat URL for {stream_type}: {chat_url}")

    return {
        'broadcast_id': broadcast_id,
        'chat_url': chat_url
    }

def _select_category(yt_client, game=None):
    """Present category selection to user"""
    if game:
        print("Game specified, using Gaming category")
        return "20"  # Gaming category ID

    response = _fetch_categories(yt_client)
    if not response or 'items' not in response:
        print("Failed to fetch categories, using default category")
        return DEFAULT_CATEGORY_ID

    # Display 12 categories at a time
    categories = response['items']
    total_categories = len(categories)
    page = 0
    page_size = 12
    total_pages = (total_categories + page_size - 1) // page_size

    while True:
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, total_categories)

        # Clear screen for better readability
        os.system('cls' if os.name == 'nt' else 'clear')

        print("\nYouTube Categories:")
        print("=" * 50)

        # Display categories in two vertical columns
        items_per_column = (end_idx - start_idx + 1) // 2 + (end_idx - start_idx) % 2
        max_name_length = 30

        # Print both columns simultaneously
        for row in range(items_per_column):
            # Left column
            left_idx = start_idx + row
            left_num = left_idx - start_idx + 1
            left_cat = categories[left_idx]['snippet']['title']
            left_part = f"{left_num:2d}. {left_cat:<{max_name_length}}"

            # Right column (if it exists)
            right_idx = left_idx + items_per_column
            if right_idx < end_idx:
                right_num = right_idx - start_idx + 1
                right_cat = categories[right_idx]['snippet']['title']
                right_part = f"{right_num:2d}. {right_cat}"
                print(f"{left_part} {right_part}")
            else:
                print(left_part)

        print("\nNavigation:")
        print(f"Page {page + 1} of {total_pages}")
        print("p. Previous page    n. Next page    q. Quit")
        print("=" * 50)

        selection = input(f"Select category (1-{end_idx-start_idx}) or navigation option: ").lower()

        if selection == 'n' and end_idx < total_categories:
            page += 1
            continue
        elif selection == 'p':
            page = (page - 1) if page > 0 else total_pages - 1
            continue
        elif selection == 'q':
            return DEFAULT_CATEGORY_ID

        try:
            idx = int(selection) - 1
            if 0 <= idx < (end_idx - start_idx):
                selected = categories[start_idx + idx]
                print(f"\nSelected: {selected['snippet']['title']}")
                return selected['id']
        except ValueError:
            continue

        print("\nInvalid selection, please try again")
        time.sleep(1)

def setup_youtube_streams(creds, title, game=None):
    """Set up YouTube live streams."""
    global IS_PORTRAIT
    streams_to_setup = _get_stream_clients(creds)
    chat_urls = []
    broadcast_ids = []
    used_stream_keys = set()  # Track which keys have been used

    # Get all initial setup inputs early
    if not streams_to_setup:
        return []
    _, first_client = streams_to_setup[0]

    # Get category
    selected_category_id = _select_category(first_client, game)

    # Get description
    description = input("Enter stream description (press Enter for none): ").strip()
    if not description:
        description = title  # Use title as default description

    # Get thumbnail
    thumbnail_prompt = "Enter path to thumbnail image (press Enter to skip): "
    thumbnail_fileURL = input(thumbnail_prompt).strip()
    if thumbnail_fileURL and not os.path.exists(thumbnail_fileURL):
        print(f"Warning: Thumbnail file not found at {thumbnail_fileURL}")
        thumbnail_fileURL = None

    # Get made for kids setting
    made_for_kids = input("Is this content made for kids? (y/n): ").lower() == 'y'

    start_time = (datetime.now(timezone.utc) +
                  timedelta(minutes=STREAM_START_DELAY_MINUTES))
    scheduled_start_time = start_time.isoformat().replace('+00:00', 'Z')

    # Get all existing stream keys once using the first client
    if not streams_to_setup:
        return []

    _, first_client = streams_to_setup[0]
    existing_keys = get_existing_stream_keys(first_client)

    # Count how many YouTube streams we need (keys in creds containing 'youtube')
    needed_streams = len([k for k in creds.keys() if 'youtube' in k.lower()])
    existing_key_count = len(existing_keys)

    # Create additional keys if needed
    keys_to_create = max(0, needed_streams - existing_key_count)
    if keys_to_create > 0:
        for i in range(keys_to_create):
            new_key = create_stream_key(first_client, f"Stream Key {existing_key_count + i + 1}")
            if new_key:
                new_key['title'] = f"Stream Key {existing_key_count + i + 1}"
                existing_keys.append(new_key)

    first = True
    for stream_type, yt_client in streams_to_setup:
        try:
            IS_PORTRAIT = stream_type == 'portrait'
            # Filter out keys that have already been used
            unused_keys = [key for key in existing_keys
                         if key['key'] not in used_stream_keys]

            if not unused_keys:
                raise Exception("All stream keys have been assigned to other streams")

            # Let user select stream key
            for i, key in enumerate(unused_keys):
                print(f"{i + 1}. {key['title']}")
            while True:
                try:
                    if first:
                        first = False
                        default_key = next((key for key in existing_keys if 'default' in key.get('title', '').lower()), None)
                        if default_key:
                            print("NOTICE: Using Default key for first stream.\n")
                            selected_key = next((key for key in unused_keys if key['title'] == default_key['title']), default_key)
                            used_stream_keys.add(default_key['key'])
                            break

                    if len(unused_keys) == 1:
                        print("NOTICE: Only one key available, using that key.\n")
                        selected_key = unused_keys[0]
                        break

                    selection = int(input("Select stream key number: ")) - 1
                    if 0 <= selection < len(unused_keys):
                        selected_key = unused_keys[selection]
                        # Verify key hasn't been used
                        if selected_key['key'] in used_stream_keys:
                            print("This stream key has already been used. Please select another.")
                            continue
                        used_stream_keys.add(selected_key['key'])  # Mark key as used
                        print(used_stream_keys)
                        break
                    print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a number.")

            stream_info = {stream_type: selected_key}

            # Use the previously selected category ID
            category_id = selected_category_id

            details = _create_stream_details(
                title, description, category_id, scheduled_start_time, made_for_kids, game
            )

            result = _handle_single_stream(
                yt_client,
                stream_type,
                stream_info,
                details,
                thumbnail_fileURL if thumbnail_fileURL else None
            )
            if result:
                chat_urls.append(result['chat_url'])
                broadcast_ids.append(result['broadcast_id'])

        except Exception as e:
            print(f"Error setting up YouTube stream: {str(e)}")

    print(f"Created {len(chat_urls)} YouTube streams with chat URLs:")
    for i, url in enumerate(chat_urls):
        print(f"Stream {i + 1} chat URL: {url}")

    return chat_urls
