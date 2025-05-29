#!/bin/bash
# Script to create a RunPod template for Dia-1.6B TTS with network volume and secrets
# Uses the REST API approach that worked in the tkr-runpod-serverless-llm project

# Stop on errors
set -e

# Project root directory (one level up from scripts)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse command line arguments
TEMPLATE_NAME="Dia-1.6B-TTS"
CONTAINER_IMAGE="tuckertucker/dia-1.6b-tts-runpod:latest"
DISK_SIZE=20
VOLUME_PATH="/data"
HF_TOKEN=""
VOLUME_ID="$NETWORK_VOLUME_ID" # Default from .env if available

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --name)
            TEMPLATE_NAME="$2"
            shift
            shift
            ;;
        --image)
            CONTAINER_IMAGE="$2"
            shift
            shift
            ;;
        --disk-size)
            DISK_SIZE="$2"
            shift
            shift
            ;;
        --volume-id)
            VOLUME_ID="$2"
            shift
            shift
            ;;
        --volume-path)
            VOLUME_PATH="$2"
            shift
            shift
            ;;
        --hf-token)
            HF_TOKEN="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/create_template.sh [--name NAME] [--image IMAGE] [--disk-size SIZE] [--volume-id ID] [--volume-path PATH] [--hf-token TOKEN]"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}Creating RunPod template for Dia-1.6B TTS...${NC}"
echo -e "Template Name:    ${GREEN}$TEMPLATE_NAME${NC}"
echo -e "Container Image:  ${GREEN}$CONTAINER_IMAGE${NC}"
echo -e "Container Disk:   ${GREEN}$DISK_SIZE GB${NC}"

# Check if we have the necessary API key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo -e "${RED}Error: RUNPOD_API_KEY is not set in your .env file.${NC}"
    exit 1
fi

# Check for HF token
if [ -z "$HF_TOKEN" ]; then
    # Try to get from environment
    HF_TOKEN="$HUGGINGFACE_TOKEN"
    if [ -z "$HF_TOKEN" ]; then
        echo -e "${YELLOW}Warning: No Hugging Face token provided.${NC}"
        echo -e "This is required for downloading the model."
        echo "Please provide a token with --hf-token or set HUGGINGFACE_TOKEN in your .env file."
        read -p "Do you want to continue without a token? (y/n): " CONTINUE
        if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
            echo "Operation cancelled."
            exit 1
        fi
    fi
fi

# Check for Docker credentials
DOCKER_USERNAME=${DOCKER_USERNAME:-$DOCKERHUB_USERNAME}
DOCKER_PASSWORD=${DOCKER_PASSWORD:-$DOCKERHUB_PASSWORD}

if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
    echo -e "Docker Credentials: ${GREEN}Available${NC}"
    USE_DOCKER_CREDENTIALS=true
else
    echo -e "Docker Credentials: ${YELLOW}Not configured${NC}"
    USE_DOCKER_CREDENTIALS=false
fi

# Check if jq is installed (needed to create JSON payloads)
if ! command -v jq &> /dev/null; then
    echo -e "${RED}jq is required but not installed. Please install jq and try again.${NC}"
    echo "On macOS: brew install jq"
    echo "On Ubuntu/Debian: apt-get install jq"
    exit 1
fi

# Set up network volume settings if volume ID is provided
if [ -n "$VOLUME_ID" ]; then
    echo -e "Network Volume:   ${GREEN}$VOLUME_ID${NC}"
    echo -e "Volume Mount:     ${GREEN}$VOLUME_PATH${NC}"
else
    echo -e "Network Volume:   ${YELLOW}None${NC}"
    # Set to empty string to avoid "null" in the JSON
    VOLUME_PATH=""
fi

# Create environment variables as a simple object of key-value pairs
ENV_VARS=$(jq -n '{
    "MODEL_ID": "nari-labs/Dia-1.6B",
    "COMPUTE_DTYPE": "float16",
    "DEFAULT_TEMPERATURE": "1.3",
    "DEFAULT_TOP_P": "0.95",
    "DEFAULT_SEED": "42"
}')

# Add HF token if provided
if [ -n "$HF_TOKEN" ]; then
    ENV_VARS=$(echo "$ENV_VARS" | jq --arg token "$HF_TOKEN" '. + {"HUGGING_FACE_TOKEN": $token}')
    echo -e "Hugging Face Token: ${GREEN}Configured as secret${NC}"
else
    echo -e "Hugging Face Token: ${YELLOW}Not configured${NC}"
fi

# Create README content
README="# Dia-1.6B TTS Model Template

This template runs the nari-labs/Dia-1.6B text-to-speech model on RunPod serverless.

## Features

- Natural dialogue generation with multiple speakers
- Voice cloning capability with audio prompt
- Fast inference with CUDA support

## Required Environment Variables

None required. All configuration is built into the container.

## Secrets

- HUGGING_FACE_TOKEN: Your Hugging Face token for downloading the model

## Network Volume

$([ -n "$VOLUME_ID" ] && echo "Network volume is configured at $VOLUME_PATH" || echo "No network volume configured")

## Example Usage

\`\`\`python
import requests
import base64

ENDPOINT_URL = \"https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run\"
API_KEY = \"YOUR_RUNPOD_API_KEY\"

payload = {
    \"input\": {
        \"text\": \"[S1] Hello, this is a test of the Dia TTS model.\",
        \"temperature\": 1.3,
        \"top_p\": 0.95,
        \"seed\": 42
    }
}

headers = {
    \"Authorization\": f\"Bearer {API_KEY}\",
    \"Content-Type\": \"application/json\"
}

response = requests.post(ENDPOINT_URL, headers=headers, json=payload)
result = response.json()
print(result)

# Get audio data
if \"output\" in result and \"audio\" in result[\"output\"]:
    audio_b64 = result[\"output\"][\"audio\"]
    audio_bytes = base64.b64decode(audio_b64)
    
    with open(\"output.wav\", \"wb\") as f:
        f.write(audio_bytes)
    print(\"Audio saved to output.wav\")
\`\`\`"

# Create basic template payload
PAYLOAD=$(jq -n \
    --arg name "$TEMPLATE_NAME" \
    --arg imageName "$CONTAINER_IMAGE" \
    --arg containerDiskInGb "$DISK_SIZE" \
    --argjson env "$ENV_VARS" \
    --arg volumeMountPath "$VOLUME_PATH" \
    --arg readme "$README" \
    '{
        name: $name,
        imageName: $imageName,
        containerDiskInGb: $containerDiskInGb | tonumber,
        env: $env,
        isServerless: true,
        readme: $readme
    }')

# Add volume mount path if provided
if [ -n "$VOLUME_PATH" ]; then
    PAYLOAD=$(echo "$PAYLOAD" | jq --arg path "$VOLUME_PATH" '. + {volumeMountPath: $path}')
fi

# Add Docker credentials if available
if [ "$USE_DOCKER_CREDENTIALS" = true ]; then
    CONTAINER_REGISTRY_AUTH=$(jq -n \
        --arg username "$DOCKER_USERNAME" \
        --arg password "$DOCKER_PASSWORD" \
        '{
            "dockerHub": {
                "username": $username,
                "password": $password
            }
        }')
    
    PAYLOAD=$(echo "$PAYLOAD" | jq --argjson auth "$CONTAINER_REGISTRY_AUTH" '. + {containerRegistryAuth: $auth}')
    echo -e "Docker Hub credentials will be included in the template."
fi

# Execute the REST API call
echo -e "\n${YELLOW}Creating template...${NC}"
echo "API Payload: $PAYLOAD"  # For debugging
response=$(curl -s -X POST "https://rest.runpod.io/v1/templates" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $RUNPOD_API_KEY" \
    -d "$PAYLOAD")

# Print the full response for debugging
echo "API Response: $response"

# Check for errors - handle various error response formats
if [[ "$response" == *"error"* ]] || [[ "$response" == *"unmarshal"* ]] || [[ "$response" == *"message"* ]]; then
    echo -e "${RED}Error creating template:${NC}"

    # Direct output of response for debugging
    echo "Error details: $response"
    
    # Try to extract a more specific error message if possible
    if echo "$response" | jq -e '.[0].error' &>/dev/null; then
        # Array of errors format
        error_msg=$(echo "$response" | jq -r '.[0].error')
        problems=$(echo "$response" | jq -r '.[0].problems[]' 2>/dev/null || echo "No specific problems listed")
        echo "Error message: $error_msg"
        echo "Problems: $problems"
    elif echo "$response" | jq -e '.error' &>/dev/null; then
        # Simple error object format
        error_msg=$(echo "$response" | jq -r '.error')
        echo "Error message: $error_msg"
    elif echo "$response" | jq -e '.message' &>/dev/null; then
        # Message format
        error_msg=$(echo "$response" | jq -r '.message')
        echo "Error message: $error_msg"
    fi
    
    # If this is an authentication issue, provide more guidance
    if [[ "$response" == *"authentication"* ]] || [[ "$response" == *"Unauthorized"* ]] || [[ "$response" == *"401"* ]]; then
        echo -e "\n${YELLOW}Authentication Error:${NC}"
        echo "Please check your RUNPOD_API_KEY in the .env file."
        echo "You can get your API key from: https://www.runpod.io/console/user/settings"
    fi
    
    # If this is a format issue, provide some guidance
    if [[ "$response" == *"unmarshal"* ]] || [[ "$response" == *"json"* ]]; then
        echo -e "\n${YELLOW}API Format Error:${NC}"
        echo "The RunPod API may have changed its expected format."
        echo "Consider using the manual approach instead:"
        echo "1. Log into RunPod dashboard at https://www.runpod.io/console/serverless"
        echo "2. Navigate to Templates and create a template manually"
    fi
    
    exit 1
fi

# Extract template ID 
TEMPLATE_ID=$(echo "$response" | jq -r '.id')

if [ -z "$TEMPLATE_ID" ] || [ "$TEMPLATE_ID" = "null" ]; then
    echo -e "${RED}Failed to create template. No template ID returned.${NC}"
    echo "Response: $response"
    exit 1
fi

echo -e "\n${GREEN}Template created successfully!${NC}"
echo -e "Template ID: ${GREEN}$TEMPLATE_ID${NC}"

# Save template ID to .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Create a temporary file for the updated content
    TEMP_ENV_FILE=$(mktemp)
    
    # Flag to track if we've found and updated the TEMPLATE_ID line
    TEMPLATE_ID_UPDATED=false
    
    # Process the .env file line by line
    while IFS= read -r line || [ -n "$line" ]; do
        if [[ "$line" =~ ^TEMPLATE_ID=.* ]]; then
            # Replace the existing TEMPLATE_ID line
            echo "TEMPLATE_ID=$TEMPLATE_ID" >> "$TEMP_ENV_FILE"
            TEMPLATE_ID_UPDATED=true
        else
            # Keep the line as is
            echo "$line" >> "$TEMP_ENV_FILE"
        fi
    done < "$PROJECT_ROOT/.env"
    
    # If TEMPLATE_ID wasn't found, add it to the end
    if [ "$TEMPLATE_ID_UPDATED" = false ]; then
        # Make sure there's a newline at the end
        if [ -s "$TEMP_ENV_FILE" ] && [ "$(tail -c 1 "$TEMP_ENV_FILE" | wc -l)" -eq 0 ]; then
            echo "" >> "$TEMP_ENV_FILE"
        fi
        echo "TEMPLATE_ID=$TEMPLATE_ID" >> "$TEMP_ENV_FILE"
    fi
    
    # Replace the original .env file with our updated version
    mv "$TEMP_ENV_FILE" "$PROJECT_ROOT/.env"
    
    echo -e "Template ID saved to .env file."
fi

echo -e "\n${YELLOW}Next step:${NC} Deploy an endpoint using this template:"
echo -e "${GREEN}./scripts/deploy.sh --template-id $TEMPLATE_ID${NC}"

exit 0