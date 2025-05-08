#!/bin/bash
# Script to build the Docker image for Dia TTS serverless endpoint

# Stop on errors
set -e

# Make sure we're in the correct directory
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# Configuration
IMAGE_NAME="tuckertucker/dia-1.6b-tts-runpod"
TAG="latest"
FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f "../.env" ]; then
    source "../.env"
fi

echo -e "${YELLOW}Building Docker image for Dia-1.6B TTS RunPod serverless endpoint...${NC}"
echo -e "Image name: ${GREEN}$FULL_IMAGE_NAME${NC}"
echo -e "NOTE: The Hugging Face token will be provided via RunPod secrets"
echo -e "      and not baked into the Docker image for security reasons."
echo -e "Working directory: ${GREEN}$SCRIPT_DIR${NC}"

# Check for Dockerfile
if [ ! -f "$SCRIPT_DIR/Dockerfile" ]; then
    echo -e "${RED}Dockerfile not found in $SCRIPT_DIR${NC}"
    echo -e "Current directory contains: $(ls -la)"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed or not in PATH. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker daemon is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}Not logged in to Docker Hub. Attempting to log in...${NC}"
    echo "Please enter your Docker Hub credentials:"
    docker login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to log in to Docker Hub. Please try again.${NC}"
        exit 1
    fi
fi

# Build the Docker image with platform specification (for RunPod which uses amd64)
echo -e "\n${YELLOW}Building Docker image...${NC}"
docker build --platform linux/amd64 -t "$FULL_IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to build Docker image.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Docker image built successfully!${NC}"

# Ask if we should push the image
read -p "Do you want to push the image to Docker Hub? (y/n): " PUSH_IMAGE

if [ "$PUSH_IMAGE" = "y" ] || [ "$PUSH_IMAGE" = "Y" ]; then
    echo -e "\n${YELLOW}Pushing image to Docker Hub...${NC}"
    docker push "$FULL_IMAGE_NAME"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to push Docker image.${NC}"
        exit 1
    fi
    
    echo -e "\n${GREEN}Docker image pushed successfully!${NC}"
    echo -e "Image is now available at: ${GREEN}$FULL_IMAGE_NAME${NC}"
    
    # Print instructions for RunPod template
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "1. Go to RunPod dashboard → Serverless → Templates"
    echo "2. Click 'New Template'"
    echo "3. Set the following values:"
    echo "   - Name: Dia-1.6B TTS"
    echo "   - Container Image: $FULL_IMAGE_NAME"
    echo "   - Container Disk: 20 GB"
    echo "4. Add the following secret:"
    echo "   Key: HUGGING_FACE_TOKEN"
    echo "   Value: Your Hugging Face token (available in your .env file)"
    echo "5. Save the template"
    echo "6. Note the template ID for deployment"
    echo -e "\nThen run: ${GREEN}./scripts/deploy.sh --template-id YOUR_TEMPLATE_ID${NC}"
else
    echo -e "\n${YELLOW}Skipping push to Docker Hub.${NC}"
    echo "You can push the image later with:"
    echo "docker push $FULL_IMAGE_NAME"
fi

exit 0