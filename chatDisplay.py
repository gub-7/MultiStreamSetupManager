import sys
import threading
import queue
import time
import os
from datetime import datetime
from colorama import init, Fore, Style, Cursor, AnsiToWin32

import sys

# Force colorama to wrap stdout for better Windows compatibility
init(wrap=True)
# Ensure we're writing to a wrapped stream that handles ANSI codes properly
stdout = AnsiToWin32(sys.stdout).stream

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
}

class ChatDisplay:
    def __init__(self, stream1_process=None, stream2_process=None):
        self.message_queue = queue.Queue()
        self.running = False
        self.chat_thread = None
        self.header_thread = None
        self.input_thread = None
        self.stream1_process = stream1_process
        self.stream2_process = stream2_process
        self.messages_start_line = 9  # Reserve lines for header
        self.message_history = []
        self.max_messages = 100  # Maximum messages to keep in history
        # Get terminal size
        self.terminal_height = os.get_terminal_size().lines
        self.terminal_width = os.get_terminal_size().columns
        self.visible_messages = self.terminal_height - self.messages_start_line - 1

    def _wrap_text(self, text, start_width):
        """Wrap text to fit within terminal width, accounting for starting width."""
        available_width = self.terminal_width - start_width
        words = text.split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_length = len(word)
            if current_width + word_length + 1 <= available_width:
                current_line.append(word)
                current_width += word_length + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_length

        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def format_message(self, platform, username, message):
        """Format a chat message with color and platform prefix, handling multiple lines."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        platform_format = PLATFORM_FORMATS.get(platform.lower(), {
            'color': Fore.WHITE,
            'prefix': f'[{platform.upper()}]'
        })

        # Handle Kick's Author object
        if platform.lower() == 'kick' and hasattr(username, 'username'):
            username = username.username

        # Convert username to string if it isn't already
        username = str(username)

        # Calculate prefix for wrapping
        prefix = f"{timestamp} {platform_format['prefix']} {username}: "
        prefix_length = len(prefix) - len(platform_format['prefix']) - len(username) - 4  # Basic length without ANSI codes

        # Handle newlines in message and wrap long lines
        message_lines = []
        for line in message.split('\n'):
            wrapped_lines = self._wrap_text(line.strip(), prefix_length)
            message_lines.extend(wrapped_lines)

        # Format first line with full prefix
        formatted_lines = []
        first_line = (f"{Fore.CYAN}{timestamp} "
                     f"{platform_format['color']}{platform_format['prefix']} "
                     f"{Fore.BLUE}{username}{Fore.WHITE}: {message_lines[0]}{Style.RESET_ALL}")
        formatted_lines.append(first_line)

        # Format continuation lines with proper indentation and explicit positioning
        if len(message_lines) > 1:
            continuation_prefix = ' ' * prefix_length
            for line in message_lines[1:]:
                formatted_line = f"{continuation_prefix}{line}"
                formatted_lines.append(formatted_line)

        return formatted_lines

    def add_message(self, platform, username, message):
        """Add a message to the queue for display."""
        # Debug information for message receipt
        platform_lower = platform.lower()
        debug_info = f"\033[K[DEBUG {datetime.now().strftime('%H:%M:%S')}] "

        if platform_lower == 'youtube':
            print(f"{debug_info}{Fore.RED}YouTube Message Received:"
                  f"\n\tUsername: {username}"
                  f"\n\tMessage: {message}"
                  f"\n\tRaw data received{Style.RESET_ALL}")
        elif platform_lower == 'kick':
            print(f"{debug_info}{Fore.GREEN}Kick Message Received:"
                  f"\n\tUsername type: {type(username)}"
                  f"\n\tUsername raw: {username}"
                  f"\n\tUsername attrs: {dir(username) if hasattr(username, '__dir__') else 'No attributes'}"
                  f"\n\tMessage type: {type(message)}"
                  f"\n\tMessage: {message}"
                  f"\n\tRaw data received{Style.RESET_ALL}")
        else:
            print(f"{debug_info}{Fore.WHITE}Other Platform ({platform}) Message:"
                  f"\n\tUsername: {username}"
                  f"\n\tMessage: {message}{Style.RESET_ALL}")

        stdout.flush()
        self.message_queue.put((platform, username, message))

        # Additional debug info for queue
        print(f"{debug_info}Queue size: {self.message_queue.qsize()}{Style.RESET_ALL}")
        stdout.flush()

    def display_header(self):
        """Display the chat window header with stream status."""
        with self.header_lock:
            # Build complete header in a buffer
            header_width = 80
            output = []

            # Save cursor and clear entire header area
            output.append("\033[?25l")  # Hide cursor
            output.append("\033[H")  # Move to top

            # Clear all header lines
            for i in range(self.messages_start_line):
                output.append(f"\033[{i+1};0H\033[K")  # Move to line and clear it

            # Return to top
            output.append("\033[H")

            # Build header content with explicit cursor positioning
            output.append("\033[1;0H" + "=" * header_width)
            output.append("\033[2;0H" + f"{Fore.CYAN}Multi-Platform Chat Display{Style.RESET_ALL}".center(header_width))

            # Stream status - only show if processes were passed in
            status_line = ""
            if self.stream1_process is not None or self.stream2_process is not None:
                stream1_status = "🟢 LIVE" if (self.stream1_process and self.stream1_process.poll() is None) else "🔴 OFFLINE"
                stream2_status = "🟢 LIVE" if (self.stream2_process and self.stream2_process.poll() is None) else "🔴 OFFLINE"
                if self.stream1_process is not None and self.stream2_process is not None:
                    status_line = f"Stream 1: {stream1_status}    Stream 2: {stream2_status}"
                elif self.stream1_process is not None:
                    status_line = f"Stream 1: {stream1_status}"
                else:
                    status_line = f"Stream 2: {stream2_status}"
                output.append("\033[3;0H" + status_line.center(header_width))
            else:
                output.append("\033[3;0H" + " " * header_width)  # Empty line if no streams

            output.append("\033[4;0H" + f"{Fore.YELLOW}Press 'q' to quit{Style.RESET_ALL}".center(header_width))
            output.append("\033[5;0H" + "=" * header_width)

            # Platform legend
            legend_line = "Platform Legend: "
            for platform, format_data in PLATFORM_FORMATS.items():
                legend_line += f"{format_data['color']}{format_data['prefix']}{Style.RESET_ALL} "
            output.append("\033[6;0H" + f"{legend_line:<{header_width}}")

            output.append("\033[7;0H" + "=" * header_width)
            output.append("\033[8;0H" + " " * header_width)  # Empty line for spacing

            # Calculate cursor position for messages
            current_pos = self.messages_start_line
            if len(self.message_history) > 0:
                current_pos += len(self.message_history) - 1

            # Restore cursor position
            output.append(f"\033[{current_pos};0H")
            output.append("\033[?25h")  # Show cursor

            # Print everything at once
            print(''.join(output), end='', file=stdout)
            stdout.flush()

    def _update_header(self):
        """Continuously update the header."""
        while self.running:
            self.display_header()
            time.sleep(1)  # Update every second

    def start(self):
        """Start the chat display."""
        self.running = True
        self.header_lock = threading.Lock()

        # Clear entire screen and move to top
        print("\033[2J", end='')  # Clear entire screen
        print(Cursor.POS(0,0), end='')
        stdout.flush()

        # Update terminal size
        self.terminal_height = os.get_terminal_size().lines
        self.visible_messages = self.terminal_height - self.messages_start_line - 1

        # Start header update thread first
        self.header_thread = threading.Thread(target=self._update_header)
        self.header_thread.daemon = True
        self.header_thread.start()

        # Give header thread time to draw initial header
        time.sleep(0.1)

        # Start message processing thread
        self.chat_thread = threading.Thread(target=self._process_messages)
        self.chat_thread.daemon = True
        self.chat_thread.start()

        # Start input handling thread
        self.input_thread = threading.Thread(target=self._input_handler)
        self.input_thread.daemon = True
        self.input_thread.start()

    def _input_handler(self):
        """Handle user input for program control."""
        while self.running:
            try:
                # Read single character without requiring Enter
                if os.name == 'nt':
                    import msvcrt
                    if msvcrt.kbhit():
                        char = msvcrt.getch().decode('utf-8').lower()
                        if char == 'q':
                            self.cleanup_and_exit()
                else:
                    import tty
                    import termios
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(fd)
                        char = sys.stdin.read(1).lower()
                        if char == 'q':
                            self.cleanup_and_exit()
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)
                continue

    def cleanup_and_exit(self):
        """Clean up and exit the program."""
        self.running = False

        # Stop stream processes
        if self.stream1_process and self.stream1_process.poll() is None:
            self.stream1_process.terminate()
            self.stream1_process.wait(timeout=5)
        if self.stream2_process and self.stream2_process.poll() is None:
            self.stream2_process.terminate()
            self.stream2_process.wait(timeout=5)

        # Clear screen and reset cursor
        print("\033[2J", end='')  # Clear screen
        print("\033[H", end='')   # Move cursor to home position
        print("\033[?25h", end='') # Show cursor
        stdout.flush()


        # Exit program
        sys.exit(0)

    def stop(self):
        """Stop the chat display."""
        self.running = False
        if self.chat_thread:
            self.chat_thread.join()
        if self.header_thread:
            self.header_thread.join()
        if self.input_thread:
            self.input_thread.join()

    def _refresh_messages(self):
        """Refresh all visible messages on the screen."""
        # Build complete output buffer first
        output = []

        # Calculate which messages to show
        start_idx = max(0, len(self.message_history) - self.visible_messages)
        visible_messages = self.message_history[start_idx:]

        # Move to start of message area and clear it entirely
        output.append(f"\033[{self.messages_start_line};0H")
        for i in range(self.visible_messages):
            output.append(f"\033[K\033[{self.messages_start_line + i};0H")

        # Always start with a blank line
        output.append(f"\033[{self.messages_start_line};0H\033[K")

        # Add each message to buffer with explicit positioning
        for i, msg in enumerate(visible_messages):
            line_num = self.messages_start_line + i + 1  # Start messages one line below
            output.append(f"\033[{line_num};0H{msg}")

        # Print everything at once and position cursor at bottom
        print(''.join(output), end='', file=stdout)
        if visible_messages:
            print(f"\033[{self.messages_start_line + len(visible_messages)};0H", end='', file=stdout)
        stdout.flush()

    def _process_messages(self):
        """Process and display messages from the queue."""
        while self.running:
            try:
                # Update terminal size
                new_size = os.get_terminal_size()
                if new_size.lines != self.terminal_height or new_size.columns != self.terminal_width:
                    self.terminal_height = new_size.lines
                    self.terminal_width = new_size.columns
                    self.visible_messages = self.terminal_height - self.messages_start_line - 1

                # Process new messages
                platform, username, message = self.message_queue.get(timeout=0.1)

                # Format message and handle multiple lines
                formatted_lines = self.format_message(platform, username, message)

                # Add each line to history, maintaining max size
                for line in formatted_lines:
                    self.message_history.append(line)
                    if len(self.message_history) > self.max_messages:
                        self.message_history.pop(0)

                # Refresh display
                self._refresh_messages()

            except queue.Empty:
                continue
            except Exception as e:
                error_msg = f"{Fore.RED}Error processing message: {str(e)}{Style.RESET_ALL}"
                self.message_history.append(error_msg)
                self._refresh_messages()

def create_chat_display(stream1_process=None, stream2_process=None):
    """Create and return a new ChatDisplay instance."""
    return ChatDisplay(stream1_process, stream2_process)

