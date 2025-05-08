#!/usr/bin/env python3
"""
Example script showing how to use the Dia TTS Inference package
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import the client from the package
from inference import DiaTTSClient

def main():
    """Basic example of generating speech with Dia TTS"""
    
    # Check if API key and endpoint ID are set
    if not os.environ.get('RUNPOD_API_KEY') or not os.environ.get('ENDPOINT_ID'):
        print("ERROR: Please set RUNPOD_API_KEY and ENDPOINT_ID environment variables")
        print("You can also create a .env file in the package root directory")
        return 1
    
    # Sample text to generate
    text = "[S1] Hello, this is a test of the Dia Text-to-Speech system."
    
    # Create client instance
    client = DiaTTSClient()
    
    # Generate speech
    print(f"Generating speech for: '{text}'")
    success, result = client.generate_speech(
        text=text,
        temperature=1.3,  # Adjust for more/less variation
        top_p=0.95,       # Controls randomness
        save_path="output.wav"
    )
    
    # Check result
    if success:
        print("Speech generated successfully!")
        print(f"Output saved to: output.wav")
        return 0
    else:
        print(f"Speech generation failed: {result}")
        return 1

if __name__ == "__main__":
    sys.exit(main())