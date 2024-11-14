import asyncio
import streamForward
from kick import Client, Credentials
from constants import RTMPS_PREFIX, APP_PATH, STREAM_MODE


async def create_credentials(creds):
    """Create Kick credentials object from credentials dictionary."""
    return Credentials(
        username=creds['username'],
        password=creds['password'],
        one_time_password=creds.get('one_time_password')
    )


async def build_stream_url(ingest_data):
    """Build the complete streaming URL from ingest data."""
    return (
        f"{RTMPS_PREFIX}"
        f"{ingest_data['rtmp_publish_path']}"
        f"{APP_PATH}"
    )


async def setup_kick_stream_async(creds, title, category):
    """Set up async Kick stream with given credentials and metadata."""
    client = Client()
    credentials = await create_credentials(creds)
    
    await client.login(credentials)
    # Note: The API wrapper documentation doesn't show how to set 
    # stream title/category. You may need to extend this once that 
    # functionality is documented
    ingest_data = await client.fetch_stream_url_and_key()
    url = await build_stream_url(ingest_data)
    key = ingest_data['rtmp_stream_token']
    await client.close() 
    streamForward.forward_stream(STREAM_MODE, url, key) 
    return client


def setup_kick_stream(creds, title, category):
    """Synchronous wrapper for setting up Kick stream."""
    asyncio.run(setup_kick_stream_async(creds, title, category))

