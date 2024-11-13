import webbrowser
import subprocess
import time
import getpass

import streamForward

def open_instagram():
    # Open the Instagram RTMP settings page
    instagram_url = "https://www.instagram.com/accounts/login/"
    webbrowser.open(instagram_url)

    # Wait for user to log in and provide the RTMP URL and key
    print("Log into Instagram and copy your RTMP stream URL and private key.")
    rtmp_url = input("Paste your RTMP stream URL here: ")
    private_key = getpass.getpass("Paste your private key here: ")

    # Here you can validate or process the rtmp_url and private_key if needed
    print(f"RTMP URL: {rtmp_url}")
    print(f"Private Key: {private_key}")

    streamForward.forward_stream("portrait", rtmp_url, private_key)
if __name__ == "__main__":
    open_instagram()

