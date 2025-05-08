#!/bin/bash
# Script to update frozen requirements for Dia TTS RunPod deployment

# Stop on errors
set -e

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/dia-tts-runpod-env"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
FROZEN_REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.frozen.txt"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Generate frozen requirements
echo "Generating frozen requirements file..."
pip freeze > "$FROZEN_REQUIREMENTS_FILE"

echo -e "\033[0;32mRequirements updated and frozen to $FROZEN_REQUIREMENTS_FILE\033[0m"
