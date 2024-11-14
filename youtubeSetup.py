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
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode=REGION_CODE
    )
    return request.execute()

def _create_category_mapping(response):
    """Create a mapping of category names to IDs."""
    return {
        item['snippet']['title'].lower(): item['id']
        for item in response.get('items', [])
    }

def get_category_id(youtube, category_name):
    """Get category ID from category name with fuzzy matching."""
    try:
        response = _fetch_categories(youtube)
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
            print(f"Matched category '{category_name}' to '{matched_name}'"
                  f" (ID: {category_id})")
            return category_id
            
        print(f"No matching category found for '{category_name}', "
              f"defaulting to Gaming")
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
        print(f"Failed to create stream key: {e}")
        return None

def _process_stream_item(item):
    """Process a single stream item from YouTube API response."""
    return {
        'key': item['cdn']['ingestionInfo']['streamName'],
        'id': item['id']
    }

def _handle_portrait_stream(youtube, stream_info):
    """Create portrait stream if it doesn't exist."""
    if 'portrait' not in stream_info:
        print("Portrait stream key not found. Creating new one...")
        portrait_stream = create_stream_key(youtube, "Portrait Stream")
        if portrait_stream:
            stream_info['portrait'] = portrait_stream
            print("Created new portrait stream key successfully")

def get_existing_stream_keys(youtube):
    """Retrieve existing stream keys from YouTube."""
    try:
        request = youtube.liveStreams().list(
            part="snippet,cdn,id",
            mine=True
        )
        response = request.execute()
        
        stream_info = {}
        for item in response.get('items', []):
            stream_data = _process_stream_item(item)
            key_type = 'portrait' if IS_PORTRAIT else 'default'
            stream_info[key_type] = stream_data
        
        _handle_portrait_stream(youtube, stream_info)
        
        print(f"Retrieved stream information: {stream_info}")
        return stream_info
    except Exception as e:
        print(f"Failed to retrieve existing stream keys: {e}")
        return {}

# Upload a thumbnail to a YouTube live stream
def upload_thumbnail(youtube, video_id, thumbnail_fileURL):
    """Upload a thumbnail to a YouTube live stream."""
    try:
        if not os.path.exists(thumbnail_fileURL):
            raise FileNotFoundError(
                f"Thumbnail file not found at {thumbnail_fileURL}"
            )

        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumbnail_fileURL
        )
        request.execute()
        print(f"Thumbnail uploaded successfully for video ID: {video_id}")
    except Exception as e:
        print(f"Failed to upload thumbnail: {e}")

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
    if 'youtube' in creds:
        streams.append(('default', _build_youtube_client(creds, 'youtube')))
    if 'youtubep' in creds:
        streams.append(('portrait', _build_youtube_client(creds, 'youtubep')))
    return streams

def _create_stream_details(title, description, category_id, start_time, game=None):
    """Create stream details dictionary."""
    details = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
            "scheduledStartTime": start_time
        },
        "status": {
            "privacyStatus": PRIVACY_STATUS
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
    
    print(f"Created broadcast with ID: {broadcast_id}")
    
    bind_request = yt_client.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=info['id']
    )
    bind_request.execute()
    
    if thumbnail_fileURL:
        upload_thumbnail(yt_client, broadcast_id, thumbnail_fileURL)
    
    return YOUTUBE_CHAT_URL.format(broadcast_id)

def setup_youtube_streams(creds, title, description, category, game, 
                         thumbnail_fileURL=None):
    """Set up YouTube live streams."""
    global IS_PORTRAIT
    streams_to_setup = _get_stream_clients(creds)
    urls = []
    
    start_time = (datetime.now(timezone.utc) + 
                  timedelta(minutes=STREAM_START_DELAY_MINUTES))
    scheduled_start_time = start_time.isoformat().replace('+00:00', 'Z')
    
    for stream_type, yt_client in streams_to_setup:
        try:
            IS_PORTRAIT = stream_type == 'portrait'
            stream_info = get_existing_stream_keys(yt_client)
            
            if not stream_info:
                raise Exception(
                    f"No stream information found for {stream_type}. "
                    "Please create stream keys manually in YouTube Studio."
                )
            
            category_id = (DEFAULT_CATEGORY_ID if game 
                          else get_category_id(yt_client, category))
            
            details = _create_stream_details(
                title, description, category_id, scheduled_start_time, game
            )
            
            url = _handle_single_stream(
                yt_client, stream_type, stream_info, details, thumbnail_fileURL
            )
            if url:
                urls.append(url)
                
        except Exception as e:
            print(f"Failed to set up YouTube stream for {stream_type}: {e}")
    
    return urls

# Example usage (integrate with main.py):
if __name__ == "__main__":
    # You need to set up the YouTube API client (youtube) before calling this function
    
    title = "My Stream Title"
    description = "My Stream Description"
    category = "20"  # Example category ID for gaming
    game = "My Game"
    thumbnail_fileURL = "path/to/thumbnail.jpg"
    
    # Example of how to call the function with separate youtube and youtubep clients
    # youtube_client = googleapiclient.discovery.build("youtube", "v3", credentials=your_credentials)
    # youtubep_client = googleapiclient.discovery.build("youtube", "v3", credentials=your_credentials)
    # setup_youtube_streams(youtube=youtube_client, youtubep=youtubep_client, title=title, description=description, category=category, game=game, thumbnail_fileURL=thumbnail_fileURL)
