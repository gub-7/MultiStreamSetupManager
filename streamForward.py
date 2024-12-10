import subprocess
from constants import (
    FFMPEG_PRESET, FFMPEG_CRF, VIDEO_BITRATE, AUDIO_BITRATE,
    VIDEO_CODEC, RTMP_LOCAL_PORT, PORTRAIT, AUDIO_CODEC
)

def create_ffmpeg_stream(orientation: str, url: str, key: str) -> subprocess.Popen | None:
    """
    Create FFmpeg stream using direct subprocess command.

    Args:
        orientation: Stream orientation ('PORTRAIT' or 'LANDSCAPE')
        url: RTMP URL
        key: Stream key
    """
    try:
        # Ensure URL ends with /
        if not url.endswith('/'):
            url += '/'

        # Build input/output URLs
        input_url = f"rtmp://localhost:{RTMP_LOCAL_PORT}/{orientation}"
        output_url = f"{url}{key}"

        # Construct FFmpeg command
        cmd = [
            'ffmpeg',
            '-f', 'flv',
            '-i', input_url,
            '-c:v', VIDEO_CODEC,
            '-preset', FFMPEG_PRESET,
            '-crf', str(FFMPEG_CRF),
            '-b:v', VIDEO_BITRATE,
            '-c:a', AUDIO_CODEC,
            '-b:a', AUDIO_BITRATE,
            '-f', 'flv',
            '-tls_verify', '1',
            output_url
        ]

        # Create and return process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        return process

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def forward_stream(orientation=PORTRAIT, url="", key="") -> subprocess.Popen | None:
    """Forward stream using FFmpeg with specified parameters."""
    return create_ffmpeg_stream(orientation, url, key)
