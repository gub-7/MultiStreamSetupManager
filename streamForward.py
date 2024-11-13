import sys
import subprocess
import shutil
import os

def get_terminal_command():
    """Get the appropriate terminal command for the current system."""
    if sys.platform == "win32":
        return None  # Windows uses CREATE_NEW_CONSOLE flag
    
    # Check for common terminals
    terminals = ['gnome-terminal', 'konsole']
    for term in terminals:
        if shutil.which(term):
            return term
    
    # Fallback to environment variable
    return os.environ.get('TERM', 'xterm')

def forward_stream(orientation="PORTRAIT", url="", key=""):
    if not url.endswith('/'):
        url += '/'
    
    # Build command as a list for better argument handling
    ffmpeg_command = [
        'ffmpeg',
        '-i', f'rtmp://localhost:1935/{orientation}',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '23',
        '-b:v', '4M',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-f', 'flv',
        f'{url}{key}'
    ]
    
    print(' '.join(ffmpeg_command))
    
    if sys.platform == "win32":
        # For Windows, use list format with CREATE_NEW_CONSOLE
        subprocess.Popen(
            ffmpeg_command,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # For Unix-like systems, use terminal command
        terminal = get_terminal_command()
        if terminal == 'gnome-terminal':
            subprocess.Popen([terminal, '--', *ffmpeg_command])
            print("we in here")
        elif terminal == 'konsole':
            subprocess.Popen([terminal, '-e', *ffmpeg_command])
        else:
            # Fallback: try to run directly
            subprocess.Popen(ffmpeg_command)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <\"PORTRAIT\"/\"LANDSCAPE\"> <URL> <KEY>")
        sys.exit(1)

    ORIENTATION = sys.argv[1]
    URL = sys.argv[2]
    KEY = sys.argv[3]

    forward_stream(ORIENTATION, URL, KEY)
