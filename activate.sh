#!/bin/bash
# Activation script for Dia TTS RunPod deployment

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/dia-tts-runpod-env"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

echo -e "\033[0;32mDia TTS RunPod deployment environment activated\033[0m"
echo "Use 'deactivate' to exit the virtual environment"
