#!/usr/bin/env python3
"""
Example script showing how to use voice cloning with Dia TTS Inference package
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import the client from the package
from inference import DiaTTSClient

def main():
    """Example of voice cloning with Dia TTS"""
    
    # Check if API key and endpoint ID are set
    if not os.environ.get('RUNPOD_API_KEY') or not os.environ.get('ENDPOINT_ID'):
        print("ERROR: Please set RUNPOD_API_KEY and ENDPOINT_ID environment variables")
        print("You can also create a .env file in the package root directory")
        return 1
    
    # Check for audio prompt file
    audio_prompt_path = os.path.join(Path(__file__).resolve().parent, "reference.wav")
    if not os.path.exists(audio_prompt_path):
        print(f"ERROR: Reference audio file not found at {audio_prompt_path}")
        print("Please provide a 5-10 second reference audio file named 'reference.wav'")
        print("in the same directory as this script.")
        return 1
    
    # Sample text to generate
    text = "[S1] This is my cloned voice. I'm demonstrating voice cloning capabilities."
    
    # Create client instance
    client = DiaTTSClient()
    
    # Generate speech with voice cloning
    print(f"Generating speech using voice from {audio_prompt_path}")
    print(f"Text: '{text}'")
    
    success, result = client.generate_speech(
        text=text,
        audio_prompt=audio_prompt_path,
        temperature=1.0,  # Lower temperature for more consistent results with cloning
        save_path="cloned_voice.wav"
    )
    
    # Check result
    if success:
        print("Voice cloning successful!")
        print(f"Output saved to: cloned_voice.wav")
        return 0
    else:
        print(f"Voice cloning failed: {result}")
        return 1

if __name__ == "__main__":
    sys.exit(main())