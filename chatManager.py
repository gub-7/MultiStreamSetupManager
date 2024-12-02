import asyncio
import aiohttp
import logging
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlparse
import json
import re

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
    """Manages chat polling and message distribution for streaming platforms"""

    def __init__(self, poll_interval: float = 1.0):
        """
        Initialize ChatManager

        Args:
            poll_interval: Time between polls in seconds
        """
        self.poll_interval = poll_interval
        self.listeners: List[Callable[[ChatMessage], None]] = []
        self.running = False
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.last_message_id: Dict[str, str] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.platform_handlers = {
            'youtube.com': self._handle_youtube_chat,
            'twitch.tv': self._handle_twitch_chat,
            'kick.com': self._handle_kick_chat
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

    async def _handle_youtube_chat(self, url: str, response_data: Any) -> List[ChatMessage]:
        """Parse YouTube chat response"""
        messages = []
        try:
            # Extract chat data from YouTube response
            chat_data = response_data.get('items', [])

            for item in chat_data:
                snippet = item.get('snippet', {})
                if not snippet:
                    continue

                message = ChatMessage(
                    platform='youtube',
                    username=snippet.get('authorDisplayName', 'Unknown'),
                    message=snippet.get('displayMessage', ''),
                    timestamp=snippet.get('publishedAt', datetime.now()),
                    message_id=item.get('id', ''),
                    user_id=snippet.get('authorChannelId', ''),
                    is_moderator=snippet.get('isModerator', False),
                    badges=[]
                )
                messages.append(message)

        except Exception as e:
            logger.error(f"Error parsing YouTube chat: {str(e)}")

        return messages

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

    async def poll_chat(self, url: str) -> None:
        """Poll chat URL for new messages"""
        platform = self._determine_platform(url)
        if not platform:
            logger.error(f"Unsupported platform URL: {url}")
            return

        handler = self.platform_handlers.get(platform)
        if not handler:
            logger.error(f"No handler found for platform: {platform}")
            return

        try:
            self.sessions[url] = aiohttp.ClientSession()
            session = self.sessions[url]

            while self.running:
                try:
                    # Add any necessary headers or query parameters
                    params = {}
                    if self.last_message_id.get(url):
                        params['after'] = self.last_message_id[url]

                    headers = self._get_platform_headers(platform)

                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status != 200:
                            logger.error(f"Failed to fetch chat, status: {response.status}")
                            await asyncio.sleep(self.poll_interval)
                            continue

                        data = await response.json()
                        messages = await handler(url, data)

                        # Update last message ID if we got messages
                        if messages:
                            self.last_message_id[url] = messages[-1].message_id

                        # Broadcast messages to listeners
                        for message in messages:
                            await self._broadcast_message(message)

                except aiohttp.ClientError as e:
                    logger.error(f"Network error polling chat: {str(e)}")
                    await asyncio.sleep(self.poll_interval * 2)  # Back off on error
                except Exception as e:
                    logger.error(f"Error polling chat: {str(e)}")
                    await asyncio.sleep(self.poll_interval)

                await asyncio.sleep(self.poll_interval)

        except Exception as e:
            logger.error(f"Session error: {str(e)}")
        finally:
            if url in self.sessions:
                await self.sessions[url].close()
                del self.sessions[url]

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
        """Start polling chat URL"""
        if url in self.active_tasks:
            logger.warning(f"Chat polling already active for URL: {url}")
            return

        self.running = True
        logger.info(f"Starting chat polling for URL: {url}")

        # Create and store the polling task
        self.active_tasks[url] = asyncio.create_task(self.poll_chat(url))

    async def stop(self) -> None:
        """Stop polling chat"""
        self.running = False

        # Cancel all active polling tasks
        for url, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close all active sessions
        for url, session in self.sessions.items():
            if not session.closed:
                await session.close()

        self.active_tasks.clear()
        self.sessions.clear()
        self.last_message_id.clear()

        logger.info("Stopped chat polling")

# Example usage
async def main():
    # Create chat manager with 2-second poll interval
    chat_manager = ChatManager(poll_interval=2.0)

    # Add message listener
    def print_message(message: ChatMessage):
        print(f"[{message.platform}] {message.username}: {message.message}")

    chat_manager.add_listener(print_message)

    # Start polling chat URL
    chat_url = "https://www.youtube.com/live_chat?v=STREAM_ID"
    try:
        await chat_manager.start(chat_url)
    except KeyboardInterrupt:
        await chat_manager.stop()

if __name__ == "__main__":
    asyncio.run(main())

