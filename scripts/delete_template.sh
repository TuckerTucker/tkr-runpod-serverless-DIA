#!/bin/bash
# Script to delete a RunPod serverless template

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the project root directory
cd "$SCRIPT_DIR/.."

# Parse command line arguments
TEMPLATE_ID=""
FORCE=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --template-id)
            TEMPLATE_ID="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            # Unknown option
            echo "Unknown option: $1"
            echo "Usage: $0 [--template-id TEMPLATE_ID] [--force]"
            exit 1
            ;;
    esac
done

# Construct the command
CMD="python3 deployment/delete_template.py"

if [ -n "$TEMPLATE_ID" ]; then
    CMD="$CMD --template-id $TEMPLATE_ID"
elif [ -n "$TEMPLATE_ID_FROM_ENV" ]; then
    CMD="$CMD --template-id $TEMPLATE_ID_FROM_ENV"
fi

if [ "$FORCE" = true ]; then
    CMD="$CMD --force"
fi

# Execute the command
echo "Executing: $CMD"
$CMD

# Exit with the same status as the Python script
exit $?