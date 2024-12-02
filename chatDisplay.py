import sys
import threading
import queue
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init()

# Platform-specific colors and prefixes
PLATFORM_FORMATS = {
    'twitch': {
        'color': Fore.MAGENTA,
        'prefix': '[TWITCH]'
    },
    'youtube': {
        'color': Fore.RED,
        'prefix': '[YT]'
    },
    'kick': {
        'color': Fore.GREEN,
        'prefix': '[KICK]'
    },
    'instagram': {
        'color': Fore.YELLOW,
        'prefix': '[IG]'
    }
}

class ChatDisplay:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.running = False
        self.chat_thread = None

    def format_message(self, platform, username, message):
        """Format a chat message with color and platform prefix."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        platform_format = PLATFORM_FORMATS.get(platform.lower(), {
            'color': Fore.WHITE,
            'prefix': f'[{platform.upper()}]'
        })

        return (f"{Fore.CYAN}{timestamp} "
                f"{platform_format['color']}{platform_format['prefix']} "
                f"{Fore.BLUE}{username}{Fore.WHITE}: {message}{Style.RESET_ALL}")

    def add_message(self, platform, username, message):
        """Add a message to the queue for display."""
        self.message_queue.put((platform, username, message))

    def display_header(self):
        """Display the chat window header."""
        print("\n" * 2)
        print("=" * 80)
        print(f"{Fore.CYAN}Multi-Platform Chat Display{Style.RESET_ALL}".center(80))
        print("=" * 80)

        # Display platform legend
        print("\nPlatform Legend:")
        for platform, format_data in PLATFORM_FORMATS.items():
            print(f"{format_data['color']}{format_data['prefix']}{Style.RESET_ALL}", end=" ")
        print("\n" + "=" * 80 + "\n")

    def start(self):
        """Start the chat display."""
        self.running = True
        self.display_header()
        self.chat_thread = threading.Thread(target=self._process_messages)
        self.chat_thread.daemon = True
        self.chat_thread.start()

    def stop(self):
        """Stop the chat display."""
        self.running = False
        if self.chat_thread:
            self.chat_thread.join()

    def _process_messages(self):
        """Process and display messages from the queue."""
        while self.running:
            try:
                platform, username, message = self.message_queue.get(timeout=0.1)
                formatted_message = self.format_message(platform, username, message)
                print(formatted_message)
                sys.stdout.flush()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"{Fore.RED}Error processing message: {str(e)}{Style.RESET_ALL}")

def create_chat_display():
    """Create and return a new ChatDisplay instance."""
    return ChatDisplay()

