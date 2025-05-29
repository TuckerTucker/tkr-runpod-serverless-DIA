#!/bin/bash
# Script to delete a RunPod serverless endpoint

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the project root directory
cd "$SCRIPT_DIR/.."

# Parse command line arguments
ENDPOINT_ID=""
FORCE=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --endpoint-id)
            ENDPOINT_ID="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            # Unknown option
            echo "Unknown option: $1"
            echo "Usage: $0 [--endpoint-id ENDPOINT_ID] [--force]"
            exit 1
            ;;
    esac
done

# Construct the command
CMD="python3 main.py delete"

if [ -n "$ENDPOINT_ID" ]; then
    CMD="$CMD --endpoint-id $ENDPOINT_ID"
fi

if [ "$FORCE" = true ]; then
    CMD="$CMD --force"
fi

# Execute the command
echo "Executing: $CMD"
$CMD

# Exit with the same status as the Python script
exit $?