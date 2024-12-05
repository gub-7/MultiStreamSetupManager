from instagrapi import Client
import streamForward
from constants import (
    PORTRAIT_MODE
)

def setup_instagram_stream(creds, title):
    client = Client()
    client.login(username=creds["username"], password=creds["password"])

    response = client.media_schedule_livestream(title, auto_start=True)

    # Wait for user to log in and provide the RTMP URL and key

    url = response['upload_url'][:response['upload_url'].find('/rtmp/') + 6]
    stream_key = response['upload_url'][response['upload_url'].find('/rtmp/') + 6:]

    streamForward.forward_stream(PORTRAIT_MODE, url, stream_key)
    client.username=response['broadcast_id']
    return client
