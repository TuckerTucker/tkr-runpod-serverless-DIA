#!/usr/bin/env python3
"""
Example script showing how to use streaming with Dia TTS Inference package
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import the streaming client from the package
from inference import DiaStreamingClient

def main():
    """Example of streaming audio with Dia TTS"""
    
    # Check if API key and endpoint ID are set
    if not os.environ.get('RUNPOD_API_KEY') or not os.environ.get('ENDPOINT_ID'):
        print("ERROR: Please set RUNPOD_API_KEY and ENDPOINT_ID environment variables")
        print("You can also create a .env file in the package root directory")
        return 1
    
    # Sample text to generate - longer text is better for demonstrating streaming
    text = """
    [S1] This is a longer piece of text to demonstrate streaming capabilities.
    [S2] Yes, with streaming you can start hearing the audio before the entire generation is complete.
    [S1] That's extremely useful for longer texts like this one, where you might want to provide
    feedback to the user while generation is still in progress.
    [S2] Exactly! It provides a much better user experience for interactive applications.
    """
    
    # Create streaming client instance
    client = DiaStreamingClient()
    
    # Generate speech with streaming
    print(f"Streaming speech for the following text:")
    print(f"---\n{text}\n---")
    
    success, result = client.stream_speech(
        text=text,
        temperature=1.3,
        top_p=0.95,
        save_path="streamed_output.wav"
    )
    
    # Check result
    if success:
        print("\nStreaming completed successfully!")
        print(f"Complete audio saved to: streamed_output.wav")
        return 0
    else:
        print(f"\nStreaming failed: {result}")
        return 1

if __name__ == "__main__":
    sys.exit(main())