#!/bin/bash
# Activation script for Dia TTS RunPod deployment

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/dia-tts-runpod-env"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\033[0;33mVirtual environment not found. Creating one now...\033[0m"
    
    # Determine Python path
    PYTHON_PATH=$(which python3)
    echo "Using Python at: $PYTHON_PATH"
    
    # Create virtual environment with system packages
    $PYTHON_PATH -m venv "$VENV_PATH" --system-site-packages
    
    if [ $? -ne 0 ]; then
        echo -e "\033[0;31mFailed to create virtual environment. Trying without system packages...\033[0m"
        $PYTHON_PATH -m venv "$VENV_PATH"
        
        if [ $? -ne 0 ]; then
            echo -e "\033[0;31mFailed to create virtual environment. Please check your Python installation.\033[0m"
            return 1
        fi
    fi
    
    echo -e "\033[0;32mVirtual environment created successfully.\033[0m"
fi

# Activate virtual environment - use absolute paths to be sure
ACTIVATE_PATH="$VENV_PATH/bin/activate"
if [ -f "$ACTIVATE_PATH" ]; then
    source "$ACTIVATE_PATH"
else
    echo -e "\033[0;31mActivation script not found at $ACTIVATE_PATH\033[0m"
    return 1
fi

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Check Python path after activation
PYTHON_CMD="$VENV_PATH/bin/python3"
PIP_CMD="$VENV_PATH/bin/pip3"

if [ ! -x "$PYTHON_CMD" ]; then
    echo -e "\033[0;31mCannot find executable Python at $PYTHON_CMD\033[0m"
    return 1
fi

if [ ! -x "$PIP_CMD" ]; then
    echo -e "\033[0;31mCannot find executable pip at $PIP_CMD\033[0m"
    return 1
fi

echo "Using Python: $PYTHON_CMD ($(PATH=$VENV_PATH/bin:$PATH $PYTHON_CMD --version 2>&1))"
echo "Using Pip: $PIP_CMD ($(PATH=$VENV_PATH/bin:$PATH $PIP_CMD --version 2>&1))"

# Install requirements if needed
if [ ! -f "$VENV_PATH/.requirements_installed" ]; then
    echo -e "\033[0;33mInstalling requirements...\033[0m"
    
    # Upgrade pip using absolute path
    $PIP_CMD install --upgrade pip
    
    # Install requirements
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        $PIP_CMD install -r "$PROJECT_ROOT/requirements.txt"
        
        if [ $? -eq 0 ]; then
            echo -e "\033[0;32mRequirements installed successfully.\033[0m"
            touch "$VENV_PATH/.requirements_installed"
        else
            echo -e "\033[0;31mFailed to install requirements.\033[0m"
        fi
    else
        echo -e "\033[0;31mrequirements.txt not found.\033[0m"
    fi
fi

# Set PATH to include virtual environment bin directory
export PATH="$VENV_PATH/bin:$PATH"

echo -e "\033[0;32mDia TTS RunPod deployment environment activated\033[0m"
echo "Virtual environment path: $VENV_PATH"
echo "Python executable: $(which python3)"
echo "Pip executable: $(which pip3)"
echo "Use 'deactivate' to exit the virtual environment"
