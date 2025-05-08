#!/bin/bash
# Setup script for Dia TTS RunPod deployment virtual environment

# Stop on errors
set -e

# Configuration
VENV_NAME="dia-tts-runpod-env"
PYTHON_VERSION="3.13"  # Updated to use Python 3.13
REQUIREMENTS_FILE="../requirements.txt"
ENV_FILE="../.env"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root directory (one level up from scripts)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${YELLOW}Setting up virtual environment for Dia TTS RunPod deployment...${NC}"

# Check if Python is installed
if ! command -v python$PYTHON_VERSION &> /dev/null; then
    echo -e "${RED}Python $PYTHON_VERSION is required but not found.${NC}"
    echo "Please install Python $PYTHON_VERSION and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
VENV_PATH="$PROJECT_ROOT/$VENV_NAME"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "Creating virtual environment at ${GREEN}$VENV_PATH${NC}..."
    python$PYTHON_VERSION -m venv "$VENV_PATH"
else
    echo -e "Virtual environment already exists at ${GREEN}$VENV_PATH${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements if file exists
if [ -f "$PROJECT_ROOT/$REQUIREMENTS_FILE" ]; then
    echo -e "Installing requirements from ${GREEN}$REQUIREMENTS_FILE${NC}..."
    pip install -r "$PROJECT_ROOT/$REQUIREMENTS_FILE"
else
    echo -e "${YELLOW}Requirements file not found."
fi

# Create activation script
ACTIVATE_SCRIPT="$PROJECT_ROOT/activate.sh"
echo -e "Creating activation script at ${GREEN}$ACTIVATE_SCRIPT${NC}..."
cat > "$ACTIVATE_SCRIPT" << EOF
#!/bin/bash
# Activation script for Dia TTS RunPod deployment

# Project root directory
PROJECT_ROOT="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="\$PROJECT_ROOT/$VENV_NAME"

# Activate virtual environment
source "\$VENV_PATH/bin/activate"

# Set environment variables
export PYTHONPATH="\$PROJECT_ROOT:\$PYTHONPATH"

# Load environment variables from .env file
if [ -f "\$PROJECT_ROOT/.env" ]; then
    set -a
    source "\$PROJECT_ROOT/.env"
    set +a
fi

echo -e "\033[0;32mDia TTS RunPod deployment environment activated\033[0m"
echo "Use 'deactivate' to exit the virtual environment"
EOF
chmod +x "$ACTIVATE_SCRIPT"

# Create update requirements script
UPDATE_REQS_SCRIPT="$PROJECT_ROOT/scripts/update_requirements.sh"
echo -e "Creating requirements update script at ${GREEN}$UPDATE_REQS_SCRIPT${NC}..."
cat > "$UPDATE_REQS_SCRIPT" << EOF
#!/bin/bash
# Script to update frozen requirements for Dia TTS RunPod deployment

# Stop on errors
set -e

# Project root directory
PROJECT_ROOT="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="\$PROJECT_ROOT/$VENV_NAME"
REQUIREMENTS_FILE="\$PROJECT_ROOT/requirements.txt"
FROZEN_REQUIREMENTS_FILE="\$PROJECT_ROOT/requirements.frozen.txt"

# Activate virtual environment
source "\$VENV_PATH/bin/activate"

# Generate frozen requirements
echo "Generating frozen requirements file..."
pip freeze > "\$FROZEN_REQUIREMENTS_FILE"

echo -e "\033[0;32mRequirements updated and frozen to \$FROZEN_REQUIREMENTS_FILE\033[0m"
EOF
chmod +x "$UPDATE_REQS_SCRIPT"

# Add project directory to PYTHONPATH within virtual environment
PTHFILE="$VENV_PATH/lib/python$PYTHON_VERSION/site-packages/project.pth"
echo "$PROJECT_ROOT" > "$PTHFILE"

echo -e "${GREEN}Virtual environment setup complete!${NC}"
echo -e "To activate the environment, run: ${YELLOW}source activate.sh${NC}"
echo -e "Your project environment is ready for Dia TTS RunPod deployment"