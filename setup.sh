#!/bin/bash

# Enable error handling
set -e

echo "Checking and installing prerequisites..."

# Function to add directory to PATH permanently
add_to_path() {
  DIR="$1"
  if ! grep -q "$DIR" <<< "$PATH"; then
    echo "Adding $DIR to PATH"
    echo "export PATH=\"$DIR:\$PATH\"" >> ~/.bashrc
    source ~/.bashrc
  fi
}

# Detect package manager
detect_package_manager() {
  if command -v apt &>/dev/null; then
    PACKAGE_MANAGER="apt"
  elif command -v pacman &>/dev/null; then
    PACKAGE_MANAGER="pacman"
  elif command -v dnf &>/dev/null; then
    PACKAGE_MANAGER="dnf"
  elif command -v zypper &>/dev/null; then
    PACKAGE_MANAGER="zypper"
  else
    echo "No supported package manager found. Please install dependencies manually."
    exit 1
  fi
}

# Install required packages based on detected package manager
install_packages() {
  detect_package_manager

  case "$PACKAGE_MANAGER" in
    apt)
      sudo apt update && sudo apt install -y python3 python3-pip golang-go ffmpeg nginx
      ;;
    pacman)
      sudo pacman -Sy --noconfirm python python-pip go ffmpeg nginx
      ;;
    dnf)
      sudo dnf install -y python3 python3-pip golang ffmpeg nginx
      ;;
    zypper)
      sudo zypper install -y python3 python3-pip go ffmpeg nginx
      ;;
    *)
      echo "Unsupported package manager: $PACKAGE_MANAGER"
      exit 1
      ;;
  esac
}

# Check for Python installation
if ! command -v python3 &> /dev/null; then
  echo "Python not found. Installing Python..."
  install_packages
  add_to_path "/usr/bin/python3"
fi

# Check for Go installation
if ! command -v go &> /dev/null; then
  echo "Go not found. Installing Go..."
  install_packages
  add_to_path "/usr/local/go/bin"
fi

# Check for FFmpeg installation
if ! command -v ffmpeg &> /dev/null; then
  echo "FFmpeg not found. Installing FFmpeg..."
  install_packages
fi

# Check for NGINX installation
if ! command -v nginx &> /dev/null; then
  echo "NGINX not found. Installing NGINX..."
  install_packages
fi

# Ask about existing NGINX installation
read -p "Do you have an existing NGINX installation that you want to manage yourself? (y/n): " CUSTOM_NGINX

if [[ "$CUSTOM_NGINX" != "y" ]]; then
  # Install NGINX-RTMP from source
  echo "Installing NGINX with RTMP module..."

  # Download and configure NGINX RTMP setup
  echo "Creating NGINX configuration..."

  # Get stream URLs from user
  read -p "Enter Twitch URL (or press Enter to skip): " TWITCH_URL
  read -p "Enter YouTube URL for landscape (or press Enter to skip): " YOUTUBE_URL
  read -p "Enter YouTube URL for portrait (or press Enter to skip): " YOUTUBE_PORTRAIT_URL

  # Create NGINX config
  NGINX_CONF="/etc/nginx/nginx.conf"
  sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak

  sudo tee "$NGINX_CONF" > /dev/null <<EOL
worker_processes  1;
events {
    worker_connections  1024;
}

rtmp {
    server {
        listen 1935;
        chunk_size 4096;

        application landscape {
            live on;
            record off;
EOL

  # Add Twitch push if URL provided
  if [[ -n "$TWITCH_URL" ]]; then
    echo "            push $TWITCH_URL;" | sudo tee -a "$NGINX_CONF" > /dev/null
  fi

  # Add YouTube landscape push if URL provided
  if [[ -n "$YOUTUBE_URL" ]]; then
    echo "            push $YOUTUBE_URL;" | sudo tee -a "$NGINX_CONF" > /dev/null
  fi

  sudo tee -a "$NGINX_CONF" > /dev/null <<EOL
        }

        application portrait {
            live on;
            record off;
EOL

  # Add YouTube portrait push if URL provided
  if [[ -n "$YOUTUBE_PORTRAIT_URL" ]]; then
    echo "            push $YOUTUBE_PORTRAIT_URL;" | sudo tee -a "$NGINX_CONF" > /dev/null
  fi

  sudo tee -a "$NGINX_CONF" > /dev/null <<EOL
        }
    }
}

http {
    server {
        listen      80;
        server_name localhost;
    }
}
EOL

  echo "NGINX configuration complete!"
  sudo systemctl restart nginx
fi

# Install Python requirements (make sure a `requirements.txt` exists in the current directory)
if [[ -f "requirements.txt" ]]; then
  echo "Installing Python requirements..."
  python3 -m pip install -r requirements.txt
else
  echo "No requirements.txt found, skipping Python package installation."
fi

# Create NGINX startup task (use systemd for Linux)
echo "Creating NGINX startup service..."
sudo tee /etc/systemd/system/nginx-rtmp.service > /dev/null <<EOL
[Unit]
Description=NGINX RTMP server
After=network.target

[Service]
ExecStart=/usr/sbin/nginx -c /etc/nginx/nginx.conf
ExecReload=/usr/sbin/nginx -s reload
ExecStop=/usr/sbin/nginx -s quit
PIDFile=/var/run/nginx.pid
Restart=on-failure
User=nginx
Group=nginx

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable nginx-rtmp
sudo systemctl start nginx-rtmp

echo "NGINX-RTMP server is running."
echo "Portrait stream endpoint: rtmp://localhost:1935/portrait"
echo "Landscape stream endpoint: rtmp://localhost:1935/landscape"

# Install Kick bypass (ensure python module is available)
echo "Installing Kick bypass..."
python3 -m kick bypass create
python3 -m kick bypass install

echo "Setup complete!"

