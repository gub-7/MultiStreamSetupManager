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

async def setup_kick_stream_async(creds, title, category):
    """Set up async Kick stream with given credentials and metadata."""
    client = Client()
    credentials = await create_credentials(creds)

    await client.login(credentials)
    print(category)
    # Note: The API wrapper documentation doesn't show how to set
    # stream title/category. You may need to extend this once that
    # functionality is documented
    ingest_data = await client.fetch_stream_url_and_key()
    print(ingest_data.stream_url)
    print(ingest_data.stream_key)
    category_data = await client.search_categories(category)
    print(category_data)

    print(category_data.hits[0])
    doc = category_data.hits[0].document

    info = await client.set_stream_info(title, "English", int(doc.id), doc.name, doc.is_mature)
    print(info)
    streamInfo = await client.fetch_stream_url_and_key()
    url = streamInfo.stream_url
    key = streamInfo.stream_key
    await client.close()
    print(url)
    streamForward.forward_stream(STREAM_MODE, f"rtmps://{url}/app/", key)
    return client


def setup_kick_stream(creds, title, category):
    """Synchronous wrapper for setting up Kick stream."""
    asyncio.run(setup_kick_stream_async(creds, title, category))

