import sys
import ffmpeg
import subprocess
from constants import (
    FFMPEG_PRESET, FFMPEG_CRF, VIDEO_BITRATE, AUDIO_BITRATE,
    VIDEO_CODEC, RTMP_LOCAL_PORT, PORTRAIT, AUDIO_CODEC
)

def create_ffmpeg_stream(orientation: str, url: str, key: str) -> None:
    """
    Create and run FFmpeg stream using ffmpeg-python library.

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

        print(f"Starting FFmpeg stream from {input_url} to {output_url}")

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

        # Run the stream (blocking)
        ffmpeg.run(
            stream,
            capture_stdout=True,
            capture_stderr=True
        )

    except ffmpeg.Error as e:
        print(f"FFmpeg error occurred: {e.stderr.decode() if e.stderr else str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

def forward_stream(orientation=PORTRAIT, url="", key="") -> None:
    """Forward stream using FFmpeg with specified parameters."""
    create_ffmpeg_stream(orientation, url, key)

def main():
    """
    Main function to start the stream forwarding.
    Usage: python alt.py [orientation] [url] [key]
    Default orientation is PORTRAIT if not specified
    """
    args = sys.argv[1:]

    if len(args) == 0:
        forward_stream()
    elif len(args) == 3:
        orientation, url, key = args
        forward_stream(orientation=orientation, url=url, key=key)
    else:
        print("Usage: python alt.py [orientation] [url] [key]")
        print("Example: python alt.py PORTRAIT rtmp://example.com streamkey123")
        sys.exit(1)

if __name__ == "__main__":
    main()
