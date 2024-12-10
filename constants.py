# YouTube API Scopes
YOUTUBE_API_SCOPE = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# Region Settings
REGION_CODE = "US"

# Category IDs
DEFAULT_CATEGORY_ID = "20"  # Gaming
ENTERTAINMENT_CATEGORY_ID = "24"

# Stream Configuration
FRAME_RATE = "variable"
INGESTION_TYPE = "rtmp"
RESOLUTION = "variable"

# Privacy Settings
PRIVACY_STATUS = "public"

# Stream Settings
ENABLE_AUTO_START = True
ENABLE_AUTO_STOP = True
ENABLE_DVR = True
ENABLE_CONTENT_ENCRYPTION = True
ENABLE_EMBED = True
RECORD_FROM_START = True
START_WITH_SLATE = False

# Timing
STREAM_START_DELAY_MINUTES = 5

# URL Templates
YOUTUBE_CHAT_URL = "https://www.youtube.com/live_chat?is_popout=1&v={}"

# Category Matching
CATEGORY_MATCH_CUTOFF = 0.6
CATEGORY_MATCH_COUNT = 1
# OAuth URLs
YOUTUBE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo"

# Server Configuration
YOUTUBE_SERVER_HOST = "localhost"
YOUTUBE_SERVER_PORT = 8080
YOUTUBE_REDIRECT_URI = f"http://{YOUTUBE_SERVER_HOST}:{YOUTUBE_SERVER_PORT}/callback"

# YouTube API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Account Types
YOUTUBE_ACCOUNT_TYPE = "youtube"
YOUTUBE_PORTRAIT_ACCOUNT_TYPE = "youtubep"

# Credential Files
YOUTUBE_CREDS_FILE = "youtubeCreds.json"
YOUTUBE_PORTRAIT_CREDS_FILE = "youtubepCreds.json"
# OAuth URLs and Settings for YouTube
YOUTUBE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_REDIRECT_URI = 'http://localhost:3000/callback'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# File paths and names
YOUTUBE_CREDS_FILE = 'youtubeCreds.json'
YOUTUBE_PORTRAIT_CREDS_FILE = 'youtubepCreds.json'

# API endpoints
TOKEN_INFO_URL = 'https://www.googleapis.com/oauth2/v1/tokeninfo'

# Server settings for YouTube
YOUTUBE_SERVER_HOST = 'localhost'
YOUTUBE_SERVER_PORT = 3000
# API Base URL
TWITCH_API_BASE_URL = "https://api.twitch.tv/helix"

# API Endpoints
USERS_ENDPOINT = "/users"
SEARCH_CATEGORIES_ENDPOINT = "/search/categories"
CHANNELS_ENDPOINT = "/channels"

# Headers
AUTH_HEADER = "Authorization"
CLIENT_ID_HEADER = "Client-Id"
CONTENT_TYPE_HEADER = "Content-Type"
JSON_CONTENT_TYPE = "application/json"

# URL Templates
CHAT_URL_TEMPLATE = "https://www.twitch.tv/popout/{username}/chat?popout="
# Twitch API endpoints
TWITCH_AUTH_URL = "https://id.twitch.tv/oauth2/authorize"
TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"

# Server settings for Twitch
TWITCH_REDIRECT_URI = 'http://localhost:3000/callback'
TWITCH_SERVER_HOST = 'localhost'
TWITCH_SERVER_PORT = 3000

# OAuth scopes
OAUTH_SCOPES = [
    'user:read:email',
    'channel:manage:broadcast'
]

# File names
CREDS_FILENAME = 'twitchCreds.json'
#!/bin/bash

# Network settings
RTMP_HOST="localhost"
RTMP_PORT=1935

# Stream settings
VIDEO_CODEC="libx264"
VIDEO_PRESET="veryfast"
VIDEO_CRF=23
VIDEO_BITRATE="2M"
AUDIO_CODEC="aac"
AUDIO_BITRATE="128k"
OUTPUT_FORMAT="flv"

# Error messages
ERR_USAGE="Usage: $0 <APP_NAME> <URL> <KEY>"
ERR_FFMPEG="Error: ffmpeg is not installed"
ERR_RTMP="Error: RTMP server not running on port 1935"
# Terminal commands
GNOME_TERMINAL = 'gnome-terminal'
KONSOLE_TERMINAL = 'konsole'
DEFAULT_TERM = 'xterm'
TERMINAL_LIST = [GNOME_TERMINAL, KONSOLE_TERMINAL]

# FFmpeg settings
FFMPEG_PRESET = 'veryfast'
FFMPEG_CRF = '23'
VIDEO_BITRATE = '4M'
AUDIO_CODEC = 'aac'
AUDIO_BITRATE = '128k'
VIDEO_CODEC = 'libx264'
RTMP_LOCAL_PORT = '1935'

# Stream orientations
PORTRAIT = "PORTRAIT"
LANDSCAPE = "LANDSCAPE"
# Kick streaming constants
RTMPS_PREFIX = 'rtmps://'
APP_PATH = '/app/'
STREAM_MODE = 'landscape'

# User prompts
RTMP_URL_PROMPT = "Paste your RTMP stream URL here: "
PRIVATE_KEY_PROMPT = "Paste your private key here: "

# Stream orientation
PORTRAIT_MODE = "portrait"
# File paths
DEFAULT_CREDS_PATH = "./"
TWITCH_APP_DATA_FILE = "twitchappdata"
YOUTUBE_APP_DATA_FILE = "youtubeappdata"

# Platform names
PLATFORM_YOUTUBE = "youtube"
PLATFORM_TWITCH = "twitch"
PLATFORM_KICK = "kick"
PLATFORM_YOUTUBE_PORTRAIT = "youtubep"

# Platform mapping
PLATFORM_MAP = {
    1: PLATFORM_YOUTUBE,
    2: PLATFORM_TWITCH,
    3: PLATFORM_KICK,
    4: PLATFORM_YOUTUBE_PORTRAIT,
}

# Default platform selection
DEFAULT_PLATFORM_SELECTION = "1, 2"

# Menu text
PLATFORM_SELECTION_MENU = """
    Select streaming platforms.
    1. Youtube
    2. Twitch
    3. Kick
    4. Youtube (portrait)

    Ex: <1, 3, 4>(1, 3, and 4)
        <2-4>(2, 3, and 4)
        <1, 5>(1 and 5)
    """

# File name templates
CREDS_FILE_TEMPLATE = "{}Creds.json"
