import asyncio
import logging
import websockets
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs
import pytchat
from aiohttp import ClientWebSocketResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Standardized chat message format"""
    platform: str
    username: str
    message: str
    timestamp: datetime
    message_id: str
    user_id: Optional[str] = None
    is_moderator: bool = False
    is_subscriber: bool = False
    badges: List[str] = None

    def __post_init__(self):
        self.badges = self.badges or []
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))

class ChatManager:
    """Manages WebSocket connections for real-time chat listening"""

    def __init__(self):
        """Initialize ChatManager"""
        self.listeners: List[Callable[[ChatMessage], None]] = []
        self.running = False
        self.websockets: Dict[str, ClientWebSocketResponse] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.platform_handlers = {
            'youtube.com': self._handle_youtube_connection,
            'twitch.tv': self._handle_twitch_connection,
        }

        # Platform-specific WebSocket URLs
        self.ws_urls = {
            'twitch.tv': 'wss://irc-ws.chat.twitch.tv:443',

        }

        # Platform-specific headers
        self.youtube_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Origin': 'https://www.youtube.com',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

    def add_listener(self, callback: Callable[[ChatMessage], None]) -> None:
        """Add a message listener callback"""
        self.listeners.append(callback)
        logger.info("Added new chat message listener")

    def remove_listener(self, callback: Callable[[ChatMessage], None]) -> None:
        """Remove a message listener callback"""
        if callback in self.listeners:
            self.listeners.remove(callback)
            logger.info("Removed chat message listener")

    def _determine_platform(self, url: str) -> Optional[str]:
        """Determine chat platform from URL"""
        domain = urlparse(url).netloc.lower()

        for platform_domain in self.platform_handlers.keys():
            if platform_domain in domain:
                return platform_domain

        return None

    async def _broadcast_message(self, message: ChatMessage) -> None:
        """Send message to all registered listeners"""
        for listener in self.listeners:
            try:
                listener(message)
            except Exception as e:
                logger.error(f"Error in message listener: {str(e)}")

    async def _handle_twitch_chat(self, url: str, response_data: Any) -> List[ChatMessage]:
        """Parse Twitch chat response"""
        messages = []
        try:
            # Extract chat data from Twitch response
            chat_data = response_data.get('messages', [])

            for item in chat_data:
                message = ChatMessage(
                    platform='twitch',
                    username=item.get('user', {}).get('display_name', 'Unknown'),
                    message=item.get('message', ''),
                    timestamp=datetime.fromtimestamp(item.get('timestamp', 0)),
                    message_id=item.get('id', ''),
                    user_id=item.get('user', {}).get('id', ''),
                    is_moderator=item.get('user', {}).get('is_moderator', False),
                    is_subscriber=item.get('user', {}).get('is_subscriber', False),
                    badges=item.get('user', {}).get('badges', [])
                )
                messages.append(message)

        except Exception as e:
            logger.error(f"Error parsing Twitch chat: {str(e)}")

        return messages

    async def _handle_kick_chat(self, url: str, response_data: Any) -> List[ChatMessage]:
        """Parse Kick chat response"""
        messages = []
        try:
            # Extract chat data from Kick response
            chat_data = response_data.get('messages', [])

            for item in chat_data:
                message = ChatMessage(
                    platform='kick',
                    username=item.get('sender', {}).get('username', 'Unknown'),
                    message=item.get('content', ''),
                    timestamp=datetime.fromtimestamp(item.get('created_at', 0)),
                    message_id=str(item.get('id', '')),
                    user_id=str(item.get('sender', {}).get('id', '')),
                    badges=[]
                )
                messages.append(message)

        except Exception as e:
            logger.error(f"Error parsing Kick chat: {str(e)}")

        return messages

    async def _handle_twitch_connection(self, url: str) -> None:
        """Handle Twitch WebSocket connection"""
        channel = parse_qs(urlparse(url).query).get('channel', [''])[0]
        if not channel:
            logger.error("No channel specified in Twitch URL")
            return

        try:
            async with websockets.connect(self.ws_urls['twitch.tv']) as websocket:
                self.websockets[url] = websocket

                # Twitch IRC authentication
                await websocket.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
                await websocket.send("PASS SCHMOOPIIE")
                await websocket.send("NICK justinfan123")
                await websocket.send(f'JOIN #{channel}')

                while self.running:
                    try:
                        message = await websocket.recv()
                        if message.startswith('PING'):
                            await websocket.send('PONG :tmi.twitch.tv')
                            continue

                        # Parse IRC message
                        if 'PRIVMSG' in message:
                            chat_message = self._parse_twitch_message(message)
                            if chat_message:
                                await self._broadcast_message(chat_message)

                    except websockets.ConnectionClosed:
                        logger.error("Twitch WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error processing Twitch message: {str(e)}")

        except Exception as e:
            logger.error(f"Error in Twitch connection: {str(e)}")
        finally:
            if url in self.websockets:
                del self.websockets[url]

    async def _handle_youtube_connection(self, chat_url: str) -> None:
        """Handle YouTube chat using pytchat"""
        try:
            # Extract video ID from URL
            video_id = parse_qs(urlparse(chat_url).query).get('v', [''])[0]
            if not video_id:
                logger.error("No video ID found in YouTube URL")
                return

            # Create pytchat instance
            chat = pytchat.create(video_id=video_id)
            logging.getLogger("httpx").setLevel(logging.WARNING)

            while self.running and chat.is_alive():
                try:
                    # Get new messages
                    for chat_item in chat.get().sync_items():
                        # Create standardized chat message
                        chat_message = ChatMessage(
                            platform='youtube',
                            username=chat_item.author.name,
                            message=chat_item.message,
                            timestamp=datetime.fromtimestamp(chat_item.timestamp/1000),  # Convert from ms to seconds
                            message_id=chat_item.id,
                            user_id=chat_item.author.channelId,
                            is_moderator=chat_item.author.isChatModerator,
                            is_subscriber=chat_item.author.isChatSponsor,
                            badges=[]  # Could be populated from badgeUrl if needed
                        )

                        # Broadcast the message
                        await self._broadcast_message(chat_message)

                except Exception as e:
                    logger.error(f"Error processing YouTube chat message: {str(e)}")

                # Small delay between polling
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in YouTube chat connection: {str(e)}")
        finally:
            if 'chat' in locals():
                chat.terminate()

    def _parse_twitch_message(self, irc_message: str) -> Optional[ChatMessage]:
        """Parse Twitch IRC message into ChatMessage"""
        try:
            # Basic IRC message parsing
            tags_prefix = ''
            if irc_message.startswith('@'):
                tags_prefix, irc_message = irc_message[1:].split(' ', 1)

            tags = dict(tag.split('=') for tag in tags_prefix.split(';')) if tags_prefix else {}

            parts = irc_message.split(' ', 3)
            if len(parts) < 4:
                return None

            username = parts[0].split('!')[0][1:]
            message_text = parts[3][1:] if len(parts) > 3 else ''

            return ChatMessage(
                platform='twitch',
                username=tags.get('display-name', username),
                message=message_text,
                timestamp=datetime.now(),
                message_id=tags.get('id', ''),
                user_id=tags.get('user-id'),
                is_moderator='moderator' in tags.get('badges', ''),
                is_subscriber='subscriber' in tags.get('badges', ''),
                badges=tags.get('badges', '').split(',') if tags.get('badges') else []
            )
        except Exception as e:
            logger.error(f"Error parsing Twitch message: {str(e)}")
            return None

    def _get_platform_headers(self, platform: str) -> Dict[str, str]:
        """Get platform-specific headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        if platform == 'youtube.com':
            headers.update({
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            })
        elif platform == 'twitch.tv':
            headers.update({
                'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
                'Accept': 'application/vnd.twitchtv.v5+json',
            })

        return headers

    async def start(self, url: str) -> None:
        """Start WebSocket connection for chat URL"""
        if url in self.active_tasks:
            logger.warning(f"Chat connection already active for URL: {url}")
            return

        platform = self._determine_platform(url)
        if not platform:
            logger.error(f"Unsupported platform URL: {url}")
            return

        handler = self.platform_handlers.get(platform)
        if not handler:
            logger.error(f"No handler found for platform: {platform}")
            return

        self.running = True
        logger.info(f"Starting chat connection for URL: {url}")

        # Create and store the connection task
        self.active_tasks[url] = asyncio.create_task(handler(url))

    async def stop(self) -> None:
        """Stop all chat connections"""
        self.running = False

        # Close all WebSocket connections
        for url, websocket in self.websockets.items():
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket for {url}: {str(e)}")

        # Cancel all active tasks
        for url, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.active_tasks.clear()
        self.websockets.clear()

        logger.info("Stopped all chat connections")

# Example usage
async def main():
    chat_manager = ChatManager()

    def handle_message(msg: ChatMessage):
        print(f"[{msg.platform}] {msg.username}: {msg.message}")

    chat_manager.add_listener(handle_message)

    # Connect to Twitch chat
    await chat_manager.start("https://twitch.tv/chat?channel=channel_name")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await chat_manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
