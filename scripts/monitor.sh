#!/bin/bash
# Simple monitoring script for RunPod serverless endpoint

# Ensure we're in the project root directory
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_ROOT"

# Load environment if exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    source .env
fi

# Check for required environment variables
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY is not set. Please set it in your .env file."
    exit 1
fi

if [ -z "$ENDPOINT_ID" ]; then
    echo "Error: ENDPOINT_ID is not set. Please set it in your .env file."
    exit 1
fi

# Parse command line arguments
INTERVAL=60  # Default monitoring interval in seconds
ENDPOINT_ID_ARG=""
COUNT=""      # Number of times to check (default: infinite)

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --endpoint-id)
            ENDPOINT_ID_ARG="$2"
            shift
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift
            shift
            ;;
        --count)
            COUNT="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Use command line endpoint ID if provided
if [ -n "$ENDPOINT_ID_ARG" ]; then
    ENDPOINT_ID="$ENDPOINT_ID_ARG"
fi

echo "======================================"
echo "  Dia-1.6B RunPod Serverless Monitor"
echo "======================================"
echo "Endpoint ID:    $ENDPOINT_ID"
echo "Interval:       $INTERVAL seconds"
if [ -n "$COUNT" ]; then
    echo "Count:          $COUNT"
else
    echo "Count:          Infinite (Ctrl+C to stop)"
fi
echo "======================================"

# Activate virtual environment if it exists
if [ -d "dia-tts-runpod-env" ]; then
    echo "Activating virtual environment..."
    source dia-tts-runpod-env/bin/activate
fi

# Function to check status
check_status() {
    python main.py status --endpoint-id "$ENDPOINT_ID"
}

# Monitor the endpoint
counter=0
while true; do
    # Check if we've reached the count limit
    if [ -n "$COUNT" ]; then
        counter=$((counter + 1))
        if [ $counter -gt "$COUNT" ]; then
            echo "Reached check count limit ($COUNT). Exiting."
            break
        fi
        echo "Check $counter of $COUNT:"
    fi

    # Check status
    check_status
    
    # Sleep if this isn't the last check
    if [ -z "$COUNT" ] || [ $counter -lt "$COUNT" ]; then
        echo "Next check in $INTERVAL seconds..."
        sleep "$INTERVAL"
        echo
    fi
done

exit 0