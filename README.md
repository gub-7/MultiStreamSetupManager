# Streaming Software

This software allows you to stream to multiple platforms simultaneously using FFmpeg and a local NGINX server.

## Prerequisites

### FFmpeg

1. Install FFmpeg:
   - Windows: Download from [FFmpeg official website](https://ffmpeg.org/download.html)
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg`

2. Verify installation:
   ```
   ffmpeg -version
   ```

### NGINX Server

1. Install NGINX:
   - Windows: Download from [NGINX official website](http://nginx.org/en/download.html)
   - macOS: `brew install nginx`
   - Linux: `sudo apt-get install nginx`

2. Configure NGINX:
   - Open the NGINX configuration file (usually located at `/etc/nginx/nginx.conf` or `C:\nginx\conf\nginx.conf`)
   - Add the following server blocks:

   ```nginx
   server {
       listen 1935;
       application landscape {
           live on;
       }
   }

   server {
       listen 1935;
       application portrait {
           live on;
       }
   }
   ```

3. Start NGINX:
   - Windows: Run `nginx.exe`
   - macOS/Linux: `sudo nginx`

## Python Requirements

Install the following Python packages:

```
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install twitchAPI
pip install pyperclip
pip install webbrowser
pip install python-ffmpeg
```

## Usage

1. Run the script:
   ```
   python main.py
   ```

2. Select one or more streaming platforms when prompted.

3. Follow the instructions in the terminal to set up your streams.

## Troubleshooting

### Stream Key/URL Issues

If you're having trouble with stream keys or URLs, make sure to wrap them in quotes when pasting into the terminal. For example:

```
Enter your stream key: "your_stream_key_here"
```

### FFmpeg Preset Option Error

If FFmpeg doesn't recognize the "preset" option (or another option), try reinstalling FFmpeg:

1. Uninstall the current FFmpeg installation.
2. Download and install the latest version from the official website.

If the issue persists, you may need to build FFmpeg from source with libx264 support:

1. Clone the FFmpeg repository:
   ```
   git clone https://git.ffmpeg.org/ffmpeg.git
   ```

2. Navigate to the FFmpeg directory:
   ```
   cd ffmpeg
   ```

3. Configure the build with libx264 support:
   ```
   ./configure --enable-libx264
   ```

4. Build and install:
   ```
   make
   sudo make install
   ```

## Coming Soon

TikTok streaming support will be added as a platform in a future update.
