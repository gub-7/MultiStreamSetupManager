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

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 4:
        print("Usage: python streamForward.py <orientation> <url> <key>")
        print("Example: python streamForward.py landscape rtmps://example.com/app/ streamkey123")
        sys.exit(1)

    orientation = sys.argv[1].lower()
    url = sys.argv[2]
    key = sys.argv[3]

    # Validate orientation
    if orientation not in ['portrait', 'landscape']:
        print("Error: orientation must be either 'portrait' or 'landscape'")
        sys.exit(1)

    print(f"Starting stream forwarding...")
    print(f"Orientation: {orientation}")
    print(f"URL: {url}")
    print(f"Key: {key}")

    process = forward_stream(orientation, url, key)

    if process:
        try:
            # Monitor the process and print any output
            while True:
                # Read and print stderr (FFmpeg outputs to stderr by default)
                error = process.stderr.readline()
                if error:
                    print(error.strip())

                # Check if process has ended
                if process.poll() is not None:
                    break

        except KeyboardInterrupt:
            print("\nInterrupted by user. Stopping stream...")
            process.terminate()
            process.wait()
            print("Stream stopped.")
    else:
        print("Failed to start stream forwarding.")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
