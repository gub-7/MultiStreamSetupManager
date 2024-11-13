import webbrowser
import subprocess
import sys
import os
import pyperclip

import streamForward

def setup_kick_stream(creds, title, category): 
    print(f"Title: {title}")
    print(f"Category: {category}")
    
    pyperclip.copy(title)
    
    kick_stream_url = "https://kick.com/dashboard/stream"
    webbrowser.open(kick_stream_url)
    
    input("Press Enter after you have updated your stream info...")
    streamForward.forward_stream("landscape", creds["stream_url"], 
                                 creds["stream_key"])

def open_kick_chat(username):
    kick_chat_url = f"https://kick.com/{username}/chatroom"
    webbrowser.open(kick_chat_url)


