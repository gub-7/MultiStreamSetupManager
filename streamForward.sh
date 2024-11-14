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

# Source constants
. ./constants.py

check_requirements() {
    # Check if ffmpeg is installed
    if ! command -v ffmpeg &> /dev/null; then
        echo "$ERR_FFMPEG"
        exit 1
    fi

    # Check if RTMP server is running
    if ! nc -z "$RTMP_HOST" "$RTMP_PORT" &>/dev/null; then
        echo "$ERR_RTMP"
        exit 1
    fi
}

validate_args() {
    if [ "$#" -ne 3 ]; then
        echo "$ERR_USAGE"
        exit 1
    fi
}

stream_forward() {
    local app_name=$1
    local url=$2
    local key=$3
    local input_url="rtmp://$RTMP_HOST:$RTMP_PORT/$app_name"

    echo "Forwarding stream from app: $app_name"

    ffmpeg -i "$input_url" \
        -c:v "$VIDEO_CODEC" \
        -preset "$VIDEO_PRESET" \
        -crf "$VIDEO_CRF" \
        -b:v "$VIDEO_BITRATE" \
        -c:a "$AUDIO_CODEC" \
        -b:a "$AUDIO_BITRATE" \
        -f "$OUTPUT_FORMAT" \
        -tls_verify 1 \
        "$url$key"
}

main() {
    validate_args "$@"
    check_requirements
    stream_forward "$1" "$2" "$3"
}

main "$@"

