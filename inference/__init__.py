"""
Dia TTS Inference Package - Client for generating speech using RunPod serverless endpoints
"""

# Import main clients for easy access
from .client.inference import DiaTTSClient
from .client.streaming import DiaStreamingClient

# Version information
__version__ = "1.0.0"

# Make key modules and classes available at the package level
__all__ = ['DiaTTSClient', 'DiaStreamingClient']