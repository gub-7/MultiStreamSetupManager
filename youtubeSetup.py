import os
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from datetime import datetime, timezone, timedelta
import webbrowser

# Scopes for YouTube API access
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def get_existing_stream_keys(youtube):
    try:
        request = youtube.liveStreams().list(
            part="snippet,cdn,id",
            mine=True
        )
        response = request.execute()
        
        stream_info = {}
        for item in response.get('items', []):
            stream_title = item['snippet']['title']
            stream_key = item['cdn']['ingestionInfo']['streamName']
            stream_id = item['id']
            if 'default' in stream_title.lower():
                stream_info['default'] = {'key': stream_key, 'id': stream_id}
            elif 'portrait' in stream_title.lower():
                stream_info['portrait'] = {'key': stream_key, 'id': stream_id}
        
        print(f"Retrieved stream information: {stream_info}")
        return stream_info
    except Exception as e:
        print(f"Failed to retrieve existing stream keys: {e}")
        return {}

# Upload a thumbnail to a YouTube live stream
def upload_thumbnail(youtube, video_id, thumbnail_fileURL):
    try:
        # Ensure thumbnail file exists
        if not os.path.exists(thumbnail_fileURL):
            raise FileNotFoundError(f"Thumbnail file not found at {thumbnail_fileURL}")

        # Call the YouTube API to upload the thumbnail
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumbnail_fileURL
        )
        response = request.execute()
        print(f"Thumbnail uploaded successfully for video ID: {video_id}")
    except Exception as e:
        print(f"Failed to upload thumbnail: {e}")

# Function to set up YouTube live streams
def setup_youtube_streams(creds, title, description, category, game, thumbnail_fileURL=None):
    streams_to_setup = []
    if creds['youtube']:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=Credentials.from_authorized_user_info(creds['youtube']))
        streams_to_setup.append(('default', youtube))
    if creds['youtubep']:
        youtubep = googleapiclient.discovery.build("youtube", "v3", credentials=Credentials.from_authorized_user_info(creds['youtubep']))
        streams_to_setup.append(('portrait', youtubep))
    should_open_chat_in = input("Open chat(s) after stream setup? y/n (Enter for y): ").lower()
    should_open_chat = True if (should_open_chat_in == "" or should_open_chat_in == "y") else False
    for stream_type, yt_client in streams_to_setup:
        try:
            # Get existing stream information
            stream_info = get_existing_stream_keys(yt_client)
            if not stream_info:
                raise Exception(f"No existing stream information found for {stream_type}. Please create stream keys manually in YouTube Studio.")
            
            # Calculate start time as current time + 5 minutes
            start_time = datetime.now(timezone.utc) + timedelta(minutes=5)
            scheduled_start_time_utc = start_time.isoformat().replace('+00:00', 'Z')
            
            info = stream_info.get(stream_type)
            if not info:
                print(f"No stream information found for {stream_type}. Skipping.")
                continue

            # Set up stream details
            stream_details = {
                "snippet": {
                    "title": title, 
                    "description": description,
                    "categoryId": category,
                    "scheduledStartTime": scheduled_start_time_utc
                },
                "status": {
                    "privacyStatus": "public"
                },
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True,
                    "enableDvr": True,
                    "enableContentEncryption": True,
                    "enableEmbed": True,
                    "recordFromStart": True,
                    "startWithSlate": False
                }
            }

            if category == "20" and game:  # 20 is the category ID for Gaming
                stream_details["snippet"]["gameTitle"] = game

            # Call the YouTube API to create the live broadcast
            broadcast_request = yt_client.liveBroadcasts().insert(
                part="snippet,status,contentDetails",
                body=stream_details
            )
            broadcast_response = broadcast_request.execute()
            broadcast_id = broadcast_response["id"]

            print(f"Created broadcast with ID: {broadcast_id}")

            # Bind the broadcast to the existing stream
            try:
                bind_request = yt_client.liveBroadcasts().bind(
                    part="id,contentDetails",
                    id=broadcast_id,
                    streamId=info['id']
                )
                bind_response = bind_request.execute()
                print(f"Bind response for {stream_type}:")

                print(f"Created YouTube broadcast for {stream_type} with broadcast ID: {broadcast_id}")

                # Automatically upload thumbnail if fileURL is provided
                if thumbnail_fileURL:
                    upload_thumbnail(yt_client, broadcast_id, thumbnail_fileURL)
                if should_open_chat:
                    # Get the chat URL and open it in a web browser
                    chat_url = f"https://www.youtube.com/live_chat?is_popout=1&v={broadcast_id}"
                    webbrowser.open(chat_url)
                    print(f"Opened chat URL for {stream_type}: {chat_url}")


            except Exception as bind_error:
                print(f"Failed to bind broadcast {broadcast_id} to stream {info['id']} for {stream_type}: {bind_error}")

        except Exception as e:
            print(f"Failed to set up YouTube stream for {stream_type}: {e}")

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
