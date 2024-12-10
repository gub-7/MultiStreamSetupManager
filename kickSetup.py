import asyncio
import streamForward
from kick import Client, Credentials
from constants import RTMPS_PREFIX, APP_PATH, STREAM_MODE
import logging
import subprocess


async def create_credentials(creds):
    """Create Kick credentials object from credentials dictionary."""
    return Credentials(
        username=creds['username'],
        password=creds['password'],
        one_time_password=creds.get('one_time_password')
    )

async def setup_kick_stream(creds, title, game=None):
    """Set up async Kick stream with given credentials and metadata."""
    logging.getLogger('kick').setLevel(logging.ERROR)
    client = Client()
    credentials = await create_credentials(creds)

    # Try to login first
    try:
        print('Attempting login...')
        response = await client.login(credentials)
        print('Login successful')
    except Exception as e:
        print(f'Login failed: {str(e)}')
        print('Running bypass script...')

        # Start the bypass process and wait a moment for it to initialize
        bypass_process = subprocess.Popen(
            ["go", "run", "bypass.go"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        await asyncio.sleep(10)  # Give bypass script time to start

        # Try login again
        try:
            response = await client.login(credentials)
            print('Login successful after bypass')
        except Exception as e:
            print(f'Login failed even with bypass: {str(e)}')
            if bypass_process:
                bypass_process.terminate()
            raise
    # Note: The API wrapper documentation doesn't show how to set
    # stream title/category. You may need to extend this once that
    # functionality is documented
    # Get category search query
    search_query = game if game else input("Please enter a Kick category: ")

    while True:
        try:
            category_data = await client.search_categories(search_query)
            if not category_data.hits:
                search_query = input("No categories found. Enter another category: ")
                continue

            # Display up to 5 categories
            max_display = min(len(category_data.hits), 5)
            for i, hit in enumerate(category_data.hits[:max_display], 1):
                doc = hit.document
                print(f"{i}. {doc.name}")

            try:
                selection = input(f"Select a category (1-{max_display}): ")
                selection_idx = int(selection) - 1

                if 0 <= selection_idx < max_display:
                    selected_cat = category_data.hits[selection_idx].document
                    break
                else:
                    print(f"Please enter a number between 1 and {max_display}")
            except ValueError:
                print("Please enter a valid number")

        except Exception as e:
            print(f"Search error: {e}")
            search_query = input("Enter another category: ")

    await client.set_stream_info(
        title,
        "English",
        int(selected_cat.id),
        selected_cat.name,
        selected_cat.is_mature
    )
    streamInfo = await client.fetch_stream_url_and_key()
    url = streamInfo.stream_url
    key = streamInfo.stream_key
    process = streamForward.forward_stream(STREAM_MODE, f"rtmps://{url}/app/", key)
    return client, process
