import asyncio
import logging
from typing import (
    Optional,
    List,
    Callable,
    Dict,
    Any
)
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs
import pytchat
from aiohttp import ClientWebSocketResponse
from kick import Client
import websockets

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

        # Platform handlers mapping
        self.platform_handlers = {
            'youtube.com': self._handle_youtube_connection,
            'twitch.tv': self._handle_twitch_connection,
            'kick.com': self._handle_kick_connection,
            'instagram.com': self._handle_instagram_connection,
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

    def remove_listener(self, callback: Callable[[ChatMessage], None]) -> None:
        """Remove a message listener callback"""
        if callback in self.listeners:
            self.listeners.remove(callback)

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
                logger.debug(e)

    def _create_twitch_message(self, item: dict) -> ChatMessage:
        """Create ChatMessage from Twitch chat data"""
        user_data = item.get('user', {})
        return ChatMessage(
            platform='twitch',
            username=user_data.get('display_name', 'Unknown'),
            message=item.get('message', ''),
            timestamp=datetime.fromtimestamp(item.get('timestamp', 0)),
            message_id=item.get('id', ''),
            user_id=user_data.get('id', ''),
            is_moderator=user_data.get('is_moderator', False),
            is_subscriber=user_data.get('is_subscriber', False),
            badges=user_data.get('badges', [])
        )

    def _create_instagram_message(self, item: dict) -> ChatMessage:
        """Create ChatMessage from Instagram comment data"""
        return ChatMessage(
            platform='instagram',
            username=item.get('user', {}).get('username', 'Unknown'),
            message=item.get('text', ''),
            timestamp=datetime.fromtimestamp(item['created_at']),
            message_id=str(item['pk']),
            user_id=str(item.get('user', {}).get('pk', '')),
            is_moderator=False,
            is_subscriber=False,
            badges=[]
        )

    async def _process_instagram_messages(
        self,
        messages: dict,
        seen_ids: set,
        last_ts: int
    ) -> int:
        """Process Instagram messages and return updated timestamp"""
        if not messages or 'comments' not in messages:
            return last_ts

        for item in messages['comments']:
            if item['pk'] in seen_ids:
                continue

            seen_ids.add(item['pk'])
            last_ts = max(last_ts, item['created_at'])

            msg = self._create_instagram_message(item)
            await self._broadcast_message(msg)

        return last_ts

    async def _handle_instagram_connection(self, client) -> None:
        """Handle Instagram live chat using authenticated client"""
        last_ts = 0
        poll_interval = 3  # Standardized polling interval
        seen_message_ids = set()

        try:
            broadcast_id = client.username
            if not broadcast_id:
                return

            while self.running:
                try:
                    messages = await asyncio.to_thread(
                        client.media_fetch_live_chat,
                        broadcast_id,
                        last_comment_ts=last_ts
                    )

                    last_ts = await self._process_instagram_messages(
                        messages,
                        seen_message_ids,
                        last_ts
                    )

                    if len(seen_message_ids) > 1000:
                        seen_message_ids.clear()

                except Exception as e:
                    logger.error(f"Error polling Instagram chat: {str(e)}")

                await asyncio.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Error in Instagram chat connection: {str(e)}")

    def _create_kick_message(self, item) -> ChatMessage:
        """Create a ChatMessage from a Kick message item"""
        return ChatMessage(
            platform='kick',
            username=item.author,
            message=item.content,
            timestamp=item.created_at,
            message_id=str(item.id),
            user_id=str(item.author),
            badges=[]
        )

    async def _process_kick_messages(
        self,
        messages: list,
        seen_ids: set,
        is_first_batch: bool = False
    ) -> None:
        """Process new Kick messages"""
        now = datetime.now()
        cutoff_time = now.timestamp() - 120  # 2 minutes ago

        for item in reversed(messages):
            if item.id in seen_ids:
                continue

            # Skip old messages in first batch
            if is_first_batch and item.created_at.timestamp() < cutoff_time:
                seen_ids.add(item.id)
                continue

            seen_ids.add(item.id)
            msg = self._create_kick_message(item)
            await self._broadcast_message(msg)

    async def _handle_kick_connection(self, client) -> None:
        """Handle Kick chat using authenticated client"""
        seen_ids = set()
        poll_interval = 15  # Standardized polling interval
        first_batch = True

        try:
            user = await client.fetch_user(client.user.username)
            if not user or not user.channel_id:
                logger.error("Could not fetch Kick channel information")
                return

            while self.running:
                try:
                    msgs = await client.get_messages(user.channel_id)
                    await self._process_kick_messages(msgs, seen_ids, first_batch)
                    first_batch = False

                    if len(seen_ids) > 1000:
                        seen_ids.clear()

                except Exception as e:
                    logger.error(f"Error polling Kick chat: {str(e)}")

                await asyncio.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Error in Kick chat connection: {str(e)}")

    async def _handle_twitch_connection(self, url: str) -> None:
        """Handle Twitch WebSocket connection"""
        channel = url.split('popout/')[1].split('/chat')[0]
        try:
            async with websockets.connect(self.ws_urls['twitch.tv']) as websocket:
                self.websockets[url] = websocket

                # Twitch IRC authentication
                logger.info("Sending Twitch IRC capabilities request")
                await websocket.send("CAP REQ :twitch.tv/tags twitch.tv/commands")
                logger.info("Sending anonymous auth")
                await websocket.send("PASS SCHMOOPIIE")
                await websocket.send("NICK justinfan123")
                logger.info(f"Joining channel #{channel}")
                await websocket.send(f'JOIN #{channel}')

                while self.running:
                    try:
                        message = await websocket.recv()
                        logger.debug(f"Raw Twitch message received: {message}")

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
                    logger.error(f"Error processing YouTube message: {str(e)}")

                # Standardized polling interval
                await asyncio.sleep(15)

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
                badges=tags.get('badges', '').split(',')
            )
        except Exception as e:
            logger.error(f"Error parsing Twitch message: {str(e)}")
            return None

    def _get_platform_headers(self, platform: str) -> Dict[str, str]:
        """Get platform-specific headers"""
        user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
        headers = {'User-Agent': user_agent}

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

    async def start(self, source) -> None:
        """Start chat connection for URL or client

        Args:
            source: Either a URL string for YouTube/Twitch, or a client object for Kick/Instagram
        """
        # Handle client-based platforms (Kick and Instagram)
        if hasattr(source, 'get_messages'):  # Kick client
            if 'kick_client' in self.active_tasks:
                logger.warning("Kick chat connection already active")
                return

            self.running = True
            logger.info("Starting Kick chat connection")
            self.active_tasks['kick_client'] = asyncio.create_task(
                self._handle_kick_connection(source))
            return

        elif hasattr(source, 'media_fetch_live_chat'):  # Instagram client
            if 'instagram_client' in self.active_tasks:
                logger.warning("Instagram chat connection already active")
                return

            self.running = True
            logger.info("Starting Instagram chat connection")
            self.active_tasks['instagram_client'] = asyncio.create_task(
                self._handle_instagram_connection(source))
            return

        # Handle URL-based platforms
        url = str(source)
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
