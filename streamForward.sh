##!/bin/bash
#
## Check if two arguments are passed
#if [ "$#" -ne 3 ]; then
#  echo "Usage: $0 <\"PORTRAIT\"/\"LANDSCAPE\"> <URL> <KEY>"
#  exit 1
#fi
#
#ORIENTATION=$1
#URL=$2
#KEY=$3
#
#echo "$ORIENTATION"
#
#ffmpeg -i rtmp://localhost:1935/"$ORIENTATION" -c:v libx264 -preset veryfast -crf 23 -b:v 2M -c:a aac -b:a 128k -f flv "$URL$KEY"

#!/bin/bash

# Check if three arguments are passed
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <APP_NAME> <URL> <KEY>"
  exit 1
fi

APP_NAME=$1
URL=$2
KEY=$3

echo "Forwarding stream from app: $APP_NAME"

# Ensure ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed"
    exit 1
fi

# Check if the input stream is available
if ! nc -z localhost 1935 &>/dev/null; then
    echo "Error: RTMP server not running on port 1935"
    exit 1
fi

# Forward the stream with RTMPS
ffmpeg -i rtmp://localhost:1935/"$APP_NAME" \
  -c:v libx264 -preset veryfast -crf 23 -b:v 2M \
  -c:a aac -b:a 128k \
  -f flv \
  -tls_verify 1 \
  -ca_file /etc/ssl/certs/ca-certificates.crt \
  "$URL$KEY"

