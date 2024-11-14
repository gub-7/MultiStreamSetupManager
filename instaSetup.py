import webbrowser
import getpass

import streamForward
from constants import (
    INSTAGRAM_LOGIN_URL,
    LOGIN_PROMPT,
    RTMP_URL_PROMPT,
    PRIVATE_KEY_PROMPT,
    PORTRAIT_MODE
)


def get_stream_credentials():
    """Get RTMP URL and private key from user input."""
    rtmp_url = input(RTMP_URL_PROMPT)
    private_key = getpass.getpass(PRIVATE_KEY_PROMPT)
    return rtmp_url, private_key


def open_instagram():
    """Open Instagram and set up streaming credentials."""
    # Open the Instagram RTMP settings page
    webbrowser.open(INSTAGRAM_LOGIN_URL)

    # Wait for user to log in and provide the RTMP URL and key
    print(LOGIN_PROMPT)
    rtmp_url, private_key = get_stream_credentials()

    # Log the received credentials
    print(f"RTMP URL: {rtmp_url}")
    print(f"Private Key: {private_key}")

    streamForward.forward_stream(PORTRAIT_MODE, rtmp_url, private_key)


if __name__ == "__main__":
    open_instagram()

