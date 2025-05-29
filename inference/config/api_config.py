"""
API configuration for Dia-1.6B RunPod serverless endpoint
"""
import os
from pathlib import Path

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

# First, try the .env in the inference package directory
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))
    
# If keys aren't set, try the root directory .env
if not os.environ.get('RUNPOD_API_KEY') or not os.environ.get('ENDPOINT_ID'):
    root_env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if root_env_path.exists():
        load_dotenv(dotenv_path=str(root_env_path))

# RunPod API key (required for making API calls)
RUNPOD_API_KEY = os.environ.get('RUNPOD_API_KEY', '')

# The endpoint ID for the RunPod serverless endpoint
ENDPOINT_ID = os.environ.get('ENDPOINT_ID', '')

# Base URL for RunPod REST API (for endpoint management)
RUNPOD_API_BASE_URL = 'https://api.runpod.io/v1'

# Base URL for RunPod Serverless API (for inference)
# Note: api.runpod.ai domain is used for inference calls
RUNPOD_SERVERLESS_API_URL = 'https://api.runpod.ai/v2'

# Hugging Face API token (optional, for accessing private models)
HUGGING_FACE_TOKEN = os.environ.get('HUGGING_FACE_TOKEN', '')

def get_endpoint_url(endpoint_id=None):
    """Get the URL for a specific RunPod serverless endpoint for inference
    
    Args:
        endpoint_id (str, optional): The endpoint ID. Defaults to ENDPOINT_ID from environment.
    
    Returns:
        str: The full endpoint URL for serverless inference
    """
    endpoint_id = endpoint_id or ENDPOINT_ID
    if not endpoint_id:
        raise ValueError("Endpoint ID is required but not provided.")
    
    # For serverless endpoints (running inference), use v2 API with .ai domain
    # IMPORTANT: RunPod uses different domains for different operations:
    # - api.runpod.ai for inference operations (used here)
    # - api.runpod.io for management operations (see get_endpoint_management_url)
    return f"{RUNPOD_SERVERLESS_API_URL}/{endpoint_id}"

def get_endpoint_management_url(endpoint_id=None):
    """Get the management URL for a specific RunPod endpoint
    
    Args:
        endpoint_id (str, optional): The endpoint ID. Defaults to ENDPOINT_ID from environment.
    
    Returns:
        str: The management URL for the endpoint
    """
    endpoint_id = endpoint_id or ENDPOINT_ID
    if not endpoint_id:
        raise ValueError("Endpoint ID is required but not provided.")
    
    # For endpoint management (status, update, delete), use v1 API with .io domain
    # IMPORTANT: RunPod uses different domains for different operations:
    # - api.runpod.io for management operations (used here)
    # - api.runpod.ai for inference operations (see get_endpoint_url)
    return f"{RUNPOD_API_BASE_URL}/endpoints/{endpoint_id}"

def validate_api_config():
    """Validate the API configuration
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not RUNPOD_API_KEY:
        return False, "RunPod API key is not set. Set the RUNPOD_API_KEY environment variable."
    
    if not ENDPOINT_ID:
        return False, "Endpoint ID is not set. Set the ENDPOINT_ID environment variable."
    
    return True, "API configuration is valid."