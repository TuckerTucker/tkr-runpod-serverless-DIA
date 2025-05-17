#!/usr/bin/env python3
"""
Client for sending inference requests to the Dia-1.6B RunPod serverless endpoint
"""
import os
import sys
import requests
import json
import time
import base64
import argparse
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.api_config import RUNPOD_API_KEY, ENDPOINT_ID

class DiaTTSClient:
    """Client for interacting with Dia-1.6B TTS RunPod endpoint"""
    
    def __init__(self, endpoint_id=None, api_key=None):
        """
        Initialize the Dia TTS client
        
        Args:
            endpoint_id (str, optional): RunPod endpoint ID. Defaults to env var ENDPOINT_ID.
            api_key (str, optional): RunPod API key. Defaults to env var RUNPOD_API_KEY.
        """
        self.endpoint_id = endpoint_id or ENDPOINT_ID
        self.api_key = api_key or RUNPOD_API_KEY
        
        if not self.endpoint_id:
            raise ValueError("Endpoint ID is required. Provide it as argument or set ENDPOINT_ID env var.")
        
        if not self.api_key:
            raise ValueError("API key is required. Provide it as argument or set RUNPOD_API_KEY env var.")
        
        # Note: For serverless inference, we still use v2 API with runpod.ai domain
        # The v1 API is for managing endpoints, but v2 is for running inference
        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_speech(self, text, temperature=1.3, top_p=0.95, seed=None, audio_prompt=None, 
                         save_path=None, polling_interval=2, timeout=300, force_refresh=False):
        """
        Generate speech from text using Dia-1.6B model
        
        Args:
            text (str): Text to convert to speech
            temperature (float, optional): Sampling temperature. Defaults to 1.3.
            top_p (float, optional): Top-p sampling value. Defaults to 0.95.
            seed (int, optional): Random seed for reproducible outputs. Defaults to None.
            audio_prompt (str, optional): Path to reference audio file for voice cloning. Defaults to None.
            save_path (str, optional): Path to save the audio file. Defaults to "output.wav".
            polling_interval (int, optional): Seconds between status checks. Defaults to 2.
            timeout (int, optional): Maximum time to wait for result in seconds. Defaults to 300.
            force_refresh (bool, optional): Force the model to be refreshed from Hugging Face. Defaults to False.
        
        Returns:
            tuple: (success, result) where result is either the audio data or error message
        """
        # Prepare payload
        payload = {
            "input": {
                "text": text,
                "temperature": temperature,
                "top_p": top_p
            }
        }
        
        # Add optional parameters if provided
        if seed is not None:
            payload["input"]["seed"] = seed
            
        # Add force refresh flag if set
        if force_refresh:
            payload["input"]["force_refresh"] = True
        
        # Handle audio prompt for voice cloning
        if audio_prompt:
            try:
                with open(audio_prompt, "rb") as f:
                    audio_bytes = f.read()
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                payload["input"]["audio_prompt"] = audio_b64
            except Exception as e:
                return False, f"Error reading audio prompt file: {str(e)}"
        
        # Submit the job
        try:
            response = requests.post(f"{self.base_url}/run", headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            job_id = result.get("id")
            
            if not job_id:
                return False, f"Failed to submit job: {result}"
            
            print(f"Job submitted with ID: {job_id}")
            
            # Poll for result
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    return False, f"Job timed out after {timeout} seconds"
                
                status_response = requests.get(f"{self.base_url}/status/{job_id}", headers=self.headers)
                status_data = status_response.json()
                
                status = status_data.get("status")
                
                if status == "COMPLETED":
                    output = status_data.get("output", {})
                    if "error" in output:
                        return False, f"Job failed: {output['error']}"
                    
                    audio_b64 = output.get("audio")
                    if not audio_b64:
                        return False, "No audio data in response"
                    
                    # Decode audio data
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    # Save to file if path is provided
                    if save_path:
                        with open(save_path, "wb") as f:
                            f.write(audio_bytes)
                        print(f"Audio saved to {save_path}")
                    
                    return True, audio_bytes
                
                elif status in ["FAILED", "CANCELLED"]:
                    error = status_data.get("error", "Unknown error")
                    return False, f"Job {status.lower()}: {error}"
                
                # Wait before polling again
                time.sleep(polling_interval)
                
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Generate speech using Dia-1.6B on RunPod serverless")
    parser.add_argument("text", type=str, help="Text to convert to speech")
    parser.add_argument("--output", "-o", type=str, default="output.wav", help="Output audio file path")
    parser.add_argument("--temperature", "-t", type=float, default=1.3, help="Sampling temperature")
    parser.add_argument("--top-p", "-p", type=float, default=0.95, help="Top-p sampling value")
    parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducible outputs")
    parser.add_argument("--audio-prompt", "-a", type=str, help="Path to reference audio for voice cloning")
    parser.add_argument("--endpoint-id", "-e", type=str, help="RunPod endpoint ID (overrides config)")
    parser.add_argument("--api-key", "-k", type=str, help="RunPod API key (overrides config)")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum time to wait in seconds")
    
    args = parser.parse_args()
    
    try:
        client = DiaTTSClient(endpoint_id=args.endpoint_id, api_key=args.api_key)
        
        print(f"Generating speech for text: '{args.text}'")
        if args.audio_prompt:
            print(f"Using voice reference from: {args.audio_prompt}")
        
        success, result = client.generate_speech(
            text=args.text,
            temperature=args.temperature,
            top_p=args.top_p,
            seed=args.seed,
            audio_prompt=args.audio_prompt,
            save_path=args.output,
            timeout=args.timeout
        )
        
        if success:
            print(f"Speech generation completed successfully")
            return 0
        else:
            print(f"Speech generation failed: {result}")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())