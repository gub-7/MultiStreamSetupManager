import webbrowser
import subprocess
import sys
import os

def open_kik_chat():
    # Replace 'your_kik_username' with the actual Kik username you want to chat with
    kik_username = input("Enter your Kik username to open chat: ")
    kik_url = f"https://kik.me/{kik_username}"

    # Open the Kik chat in the default web browser
    webbrowser.open(kik_url)

    # Wait for user input to continue after they've logged in and opened the chat
    input("Press Enter after you have logged into Kik and opened the chat...")

    # Call the local bash script with necessary arguments
    stream_forward_script = './streamForward'
    args = ['arg1', 'arg2']  # Replace these with actual arguments if needed
    try:
        subprocess.run([stream_forward_script] + args, check=True)
        print("Stream forwarding script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the stream forwarding script: {e}")

if __name__ == "__main__":
    open_kik_chat()

