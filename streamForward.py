import sys
import subprocess
import shutil
import os
import shlex
from constants import (
    FFMPEG_PRESET, FFMPEG_CRF, VIDEO_BITRATE, AUDIO_CODEC, AUDIO_BITRATE,
    VIDEO_CODEC, RTMP_LOCAL_PORT, PORTRAIT
)

def get_terminal_command():
    """Get the appropriate terminal command for the current platform."""
    if sys.platform == "win32":
        # Try Windows Terminal first, fall back to cmd.exe
        if shutil.which("wt"):
            return ["wt"]
        return ["cmd", "/c", "start"]

    # For Unix-like systems (Linux and macOS)
    terminals = [
        # Linux terminals
        "konsole", "gnome-terminal", "xterm", "terminator", "xfce4-terminal",
        # macOS terminals
        "Terminal.app", "iTerm.app"
    ]

    for terminal in terminals:
        if terminal.endswith('.app'):  # macOS
            if os.path.exists(f"/Applications/{terminal}"):
                return ["open", "-a", terminal]
        else:  # Linux
            if shutil.which(terminal):
                terminal_args = {
                    "konsole": [terminal, "-e"],
                    "gnome-terminal": [terminal, "--"],
                    "xterm": [terminal, "-e"],
                    "terminator": [terminal, "-e"],
                    "xfce4-terminal": [terminal, "-e"]
                }
                return terminal_args.get(terminal, [terminal, "-e"])

    # Fallback to xterm if nothing else is found on Unix
    if sys.platform != "win32" and shutil.which("xterm"):
        return ["xterm", "-e"]

    raise RuntimeError("No suitable terminal found")

def build_ffmpeg_command(orientation, url, key):
    """Build the FFmpeg command string."""
    if not url.endswith('/'):
        url += '/'

    full_url = shlex.quote(f"{url}{key}")

    command = (
        f"ffmpeg -i rtmp://localhost:{RTMP_LOCAL_PORT}/{orientation} "
        f"-c:v {VIDEO_CODEC} "
        f"-preset {FFMPEG_PRESET} "
        f"-crf {FFMPEG_CRF} "
        f"-b:v {VIDEO_BITRATE} "
        f"-c:a {AUDIO_CODEC} "
        f"-b:a {AUDIO_BITRATE} "
        f"-f flv "
        f"-tls_verify 1 "
        f"{full_url}"
    )

    if sys.platform != "win32":
        command += "; exec bash"  # Keep terminal open on Unix-like systems

    return command

def execute_command(orientation, url, key):
    """Execute FFmpeg command using the appropriate terminal."""
    try:
        terminal_cmd = get_terminal_command()
        ffmpeg_cmd = build_ffmpeg_command(orientation, url, key)

        if sys.platform == "win32":
            if terminal_cmd[0] == "wt":
                subprocess.Popen([*terminal_cmd, "powershell", "-Command", ffmpeg_cmd])
            else:
                subprocess.Popen([*terminal_cmd, "cmd", "/k", ffmpeg_cmd])
        else:
            subprocess.Popen([*terminal_cmd, "bash", "-c", ffmpeg_cmd])

    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

def forward_stream(orientation=PORTRAIT, url="", key=""):
    """Forward stream using FFmpeg with specified parameters."""
    execute_command(orientation, url, key)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} "
            "<\"PORTRAIT\"/\"LANDSCAPE\"> <URL> <KEY>"
        )
        sys.exit(1)

    forward_stream(sys.argv[1], sys.argv[2], sys.argv[3])
