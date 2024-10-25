import webbrowser
import subprocess
import time

def open_instagram():
    # Open the Instagram RTMP settings page
    instagram_url = "https://www.instagram.com/accounts/login/"
    webbrowser.open(instagram_url)

    # Wait for user to log in and provide the RTMP URL and key
    print("Please log into Instagram and copy your RTMP stream URL and private key.")
    rtmp_url = input("Paste your RTMP stream URL here: ")
    private_key = input("Paste your private key here: ")

    # Here you can validate or process the rtmp_url and private_key if needed
    print(f"RTMP URL: {rtmp_url}")
    print(f"Private Key: {private_key}")

    # Call the local bash script with necessary arguments
    stream_forward_script = './streamForward'
    args = [rtmp_url, private_key]  # Pass the RTMP URL and private key as arguments
    try:
        subprocess.run([stream_forward_script] + args, check=True)
        print("Stream forwarding script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the stream forwarding script: {e}")

if __name__ == "__main__":
    open_instagram()

