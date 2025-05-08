"""
System-level configuration for GPU and resource requirements
"""
import os
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=str(env_path))

# Supported GPU types in order of preference
GPU_TYPES = os.environ.get('GPU_TYPES', 'NVIDIA A4000,NVIDIA RTX 4000,NVIDIA RTX 3090').split(',')

# Worker configuration
MIN_WORKERS = int(os.environ.get('MIN_WORKERS', '0'))
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '3'))
IDLE_TIMEOUT = int(os.environ.get('IDLE_TIMEOUT', '300'))
FLASH_BOOT = os.environ.get('FLASH_BOOT', 'true').lower() == 'true'

# Container configuration
CONTAINER_DISK_SIZE = int(os.environ.get('CONTAINER_DISK_SIZE', '20'))  # in GB
EXECUTION_TIMEOUT = int(os.environ.get('EXECUTION_TIMEOUT', '600'))    # in seconds

# System requirements
MIN_VRAM_GB = 10  # Minimum VRAM required for Dia-1.6B in float16 mode
RECOMMENDED_VRAM_GB = 16  # Recommended VRAM for optimal performance

# Performance metrics
TOKENS_PER_SECOND = {
    'NVIDIA A4000': 40,
    'NVIDIA RTX 4000': 40,
    'NVIDIA RTX 3090': 55,
    'NVIDIA A5000': 55,
    'NVIDIA RTX 4090': 75
}

AUDIO_TOKENS_PER_SECOND = 86  # Approximately 86 tokens = 1 second of audio

def get_gpu_info(gpu_type):
    """Get information about a GPU type
    
    Args:
        gpu_type (str): GPU type (e.g., 'NVIDIA A4000')
    
    Returns:
        dict: GPU information including VRAM and performance metrics
    """
    gpu_info = {
        'NVIDIA A4000': {
            'vram_gb': 16,
            'tokens_per_second': 40,
            'suitable': True,
            'cost_per_hour': 0.576
        },
        'NVIDIA RTX 4000': {
            'vram_gb': 16,
            'tokens_per_second': 40,
            'suitable': True,
            'cost_per_hour': 0.576
        },
        'NVIDIA RTX 3090': {
            'vram_gb': 24,
            'tokens_per_second': 55,
            'suitable': True,
            'cost_per_hour': 0.684
        },
        'NVIDIA A5000': {
            'vram_gb': 24,
            'tokens_per_second': 55,
            'suitable': True,
            'cost_per_hour': 0.684
        },
        'NVIDIA RTX 4090': {
            'vram_gb': 24,
            'tokens_per_second': 75,
            'suitable': True,
            'cost_per_hour': 1.116
        },
        'NVIDIA T4': {
            'vram_gb': 16,
            'tokens_per_second': 25,
            'suitable': True,
            'cost_per_hour': 0.36
        },
        'NVIDIA L4': {
            'vram_gb': 24,
            'tokens_per_second': 45,
            'suitable': True,
            'cost_per_hour': 0.60
        }
    }
    
    return gpu_info.get(gpu_type, {
        'vram_gb': 0,
        'tokens_per_second': 0,
        'suitable': False,
        'cost_per_hour': 0
    })

def estimate_processing_time(text_length, gpu_type='NVIDIA A4000'):
    """Estimate processing time for a given text length
    
    Args:
        text_length (int): Length of text in characters
        gpu_type (str, optional): GPU type. Defaults to 'NVIDIA A4000'.
    
    Returns:
        float: Estimated processing time in seconds
    """
    # Rough estimate: average of 4 characters per token for input text
    input_tokens = text_length / 4
    
    # Get tokens per second for this GPU type
    tokens_per_second = get_gpu_info(gpu_type)['tokens_per_second']
    
    # Estimate processing time
    processing_time = input_tokens / tokens_per_second
    
    return processing_time

def estimate_audio_length(text_length):
    """Estimate audio length for a given text length
    
    Args:
        text_length (int): Length of text in characters
    
    Returns:
        float: Estimated audio length in seconds
    """
    # Rough estimate: average of 4 characters per token for input text
    # and 86 tokens per second of audio
    input_tokens = text_length / 4
    audio_length = input_tokens / AUDIO_TOKENS_PER_SECOND
    
    return audio_length