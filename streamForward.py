import sys
import subprocess
import shutil
import os
from constants import (
    GNOME_TERMINAL, KONSOLE_TERMINAL, DEFAULT_TERM, TERMINAL_LIST,
    FFMPEG_PRESET, FFMPEG_CRF, VIDEO_BITRATE, AUDIO_CODEC, AUDIO_BITRATE,
    VIDEO_CODEC, RTMP_LOCAL_PORT, PORTRAIT
)

def get_terminal_command():
    """Get the appropriate terminal command for the current system."""
    if sys.platform == "win32":
        return None  # Windows uses CREATE_NEW_CONSOLE flag
    
    for term in TERMINAL_LIST:
        if shutil.which(term):
            return term
    
    return os.environ.get('TERM', DEFAULT_TERM)

def build_ffmpeg_command(orientation, url, key):
    """Build the FFmpeg command with the given parameters."""
    if not url.endswith('/'):
        url += '/'
        
    rtmp_url = f'rtmp://localhost:{RTMP_LOCAL_PORT}/{orientation}'
    
    return [
        'ffmpeg',
        '-i', rtmp_url,
        '-c:v', VIDEO_CODEC,
        '-preset', FFMPEG_PRESET,
        '-crf', FFMPEG_CRF,
        '-b:v', VIDEO_BITRATE,
        '-c:a', AUDIO_CODEC,
        '-b:a', AUDIO_BITRATE,
        '-f', 'flv',
        '-tls_verify', '1',
        f'{url}{key}'
    ]

def execute_windows_command(ffmpeg_command):
    """Execute FFmpeg command on Windows."""
    subprocess.Popen(
        ffmpeg_command,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

def execute_unix_command(ffmpeg_command, terminal):
    """Execute FFmpeg command on Unix-like systems."""
    if terminal == GNOME_TERMINAL:
        subprocess.Popen([terminal, '--', *ffmpeg_command])
    elif terminal == KONSOLE_TERMINAL:
        subprocess.Popen([terminal, '-e', *ffmpeg_command])
    else:
        subprocess.Popen(ffmpeg_command)

def forward_stream(orientation=PORTRAIT, url="", key=""):
    """Forward stream using FFmpeg with specified parameters."""
    ffmpeg_command = build_ffmpeg_command(orientation, url, key)
    
    if sys.platform == "win32":
        execute_windows_command(ffmpeg_command)
    else:
        execute_unix_command(ffmpeg_command, get_terminal_command())

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} "
            "<\"PORTRAIT\"/\"LANDSCAPE\"> <URL> <KEY>"
        )
        sys.exit(1)

    forward_stream(sys.argv[1], sys.argv[2], sys.argv[3])
