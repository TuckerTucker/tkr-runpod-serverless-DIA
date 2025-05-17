#!/bin/bash
# One-command deployment script for Dia-1.6B RunPod serverless endpoint

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

# Parse command line arguments
TEMPLATE_ID="${TEMPLATE_ID:-}"  # Use TEMPLATE_ID from .env if it exists
ENDPOINT_NAME="Dia-1.6B-Endpoint"
MIN_WORKERS=0
MAX_WORKERS=3
FLASH_BOOT=true
NETWORK_VOLUME_OPTION=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --template-id)
            TEMPLATE_ID="$2"
            shift
            shift
            ;;
        --name)
            ENDPOINT_NAME="$2"
            shift
            shift
            ;;
        --min-workers)
            MIN_WORKERS="$2"
            shift
            shift
            ;;
        --max-workers)
            MAX_WORKERS="$2"
            shift
            shift
            ;;
        --no-flash-boot)
            FLASH_BOOT=false
            shift
            ;;
        --network-volume-id)
            NETWORK_VOLUME_OPTION="--network-volume-id $2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check for required template ID
if [ -z "$TEMPLATE_ID" ]; then
    echo "Error: Template ID is required. Use --template-id to specify it."
    echo "Usage: ./scripts/deploy.sh --template-id <template-id> [--name <name>] [--min-workers <num>] [--max-workers <num>] [--no-flash-boot] [--network-volume-id <id>]"
    exit 1
fi

# Use network volume from .env if not specified and available
if [ -z "$NETWORK_VOLUME_OPTION" ] && [ -n "$NETWORK_VOLUME_ID" ]; then
    NETWORK_VOLUME_OPTION="--network-volume-id $NETWORK_VOLUME_ID"
fi

echo "======================================"
echo "  Dia-1.6B RunPod Serverless Deploy"
echo "======================================"
echo "Template ID:   $TEMPLATE_ID"
echo "Endpoint Name: $ENDPOINT_NAME"
echo "Min Workers:   $MIN_WORKERS"
echo "Max Workers:   $MAX_WORKERS"
echo "Flash Boot:    $FLASH_BOOT"
if [ -n "$NETWORK_VOLUME_OPTION" ]; then
    echo "Network Volume: ${NETWORK_VOLUME_OPTION#--network-volume-id }"
fi
echo "======================================"

# Activate virtual environment if it exists
if [ -d "dia-tts-runpod-env" ]; then
    echo "Activating virtual environment..."
    source dia-tts-runpod-env/bin/activate
fi

# Deploy the endpoint
echo "Deploying endpoint..."

# Build command parts
DEPLOY_CMD="python deployment/create_endpoint.py"
DEPLOY_CMD="$DEPLOY_CMD --template-id \"$TEMPLATE_ID\""
DEPLOY_CMD="$DEPLOY_CMD --name \"$ENDPOINT_NAME\""
DEPLOY_CMD="$DEPLOY_CMD --min-workers $MIN_WORKERS"
DEPLOY_CMD="$DEPLOY_CMD --max-workers $MAX_WORKERS"

# Add flash boot option only if it's false
if [ "$FLASH_BOOT" = "false" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --no-flash-boot"
fi

# Add network volume if provided
if [ -n "$NETWORK_VOLUME_OPTION" ]; then
    NETWORK_VOL_ID=${NETWORK_VOLUME_OPTION#--network-volume-id }
    DEPLOY_CMD="$DEPLOY_CMD --network-volume-id \"$NETWORK_VOL_ID\""
fi

# Print final command for debugging
echo "Running command: $DEPLOY_CMD"

# Execute the command
eval $DEPLOY_CMD
RESULT=$?

# Check if deployment was successful
if [ $RESULT -ne 0 ]; then
    echo "Deployment failed with error code: $RESULT"
    exit 1
fi

# Double check by looking for the endpoint ID
if [ ! -f .env ] || ! grep -q "ENDPOINT_ID=" .env; then
    echo "Warning: Deployment may have failed. No ENDPOINT_ID found in .env file."
    echo "Please check in the RunPod dashboard if your endpoint was created."
    exit 1
fi

echo "Deployment successful!"

# Update .env file with new endpoint ID
ENDPOINT_ID=$(python -c "import os, sys; sys.path.insert(0, '$PROJECT_ROOT'); from config.api_config import ENDPOINT_ID; print(ENDPOINT_ID)")

if [ -n "$ENDPOINT_ID" ]; then
    echo "Endpoint ID is now set to: $ENDPOINT_ID"
    
    # Check endpoint status
    echo "Checking endpoint status..."
    python main.py status
    
    echo "Deployment complete!"
    echo "You can now use the endpoint for speech generation."
    echo "Example: python main.py generate \"[S1] Hello, this is a test of the Dia TTS model.\" --output test.wav"
fi

exit 0