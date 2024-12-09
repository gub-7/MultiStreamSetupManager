import sys
import ffmpeg
import subprocess
from constants import (
    FFMPEG_PRESET, FFMPEG_CRF, VIDEO_BITRATE, AUDIO_BITRATE,
    VIDEO_CODEC, RTMP_LOCAL_PORT, PORTRAIT, AUDIO_CODEC
)

def create_ffmpeg_stream(orientation: str, url: str, key: str) -> subprocess.Popen | None:
    """
    Create FFmpeg stream using ffmpeg-python library.

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
        input_url = f"rtmp://localhost:{RTMP_LOCAL_PORT}/live/{orientation}"
        output_url = f"{url}{key}"

        # Create stream with input options
        stream = ffmpeg.input(
            input_url,
            f='flv'  # Input format
        )

        # Add output options
        stream = ffmpeg.output(
            stream,
            output_url,
            vcodec=VIDEO_CODEC,
            acodec=AUDIO_CODEC,
            preset=FFMPEG_PRESET,
            crf=FFMPEG_CRF,
            video_bitrate=VIDEO_BITRATE,
            audio_bitrate=AUDIO_BITRATE,
            format='flv',
            tls_verify=1
        )

        # Run the stream (non-blocking)
        process = ffmpeg.run_async(
            stream,
            quiet=True,
            overwrite_output=True
        )

        # Keep the process reference
        return process

    except ffmpeg.Error as e:
        print(f"FFmpeg error occurred: {e.stderr.decode() if e.stderr else str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

def forward_stream(orientation=PORTRAIT, url="", key="") -> subprocess.Popen | None:
    """Forward stream using FFmpeg with specified parameters."""
    return create_ffmpeg_stream(orientation, url, key)
