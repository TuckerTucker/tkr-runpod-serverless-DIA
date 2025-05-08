#!/usr/bin/env python3
"""
Client for streaming responses from the Dia-1.6B RunPod serverless endpoint
"""
import os
import sys
import requests
import json
import time
import base64
import argparse
import threading
import queue
# import pyaudio  # Commented out to avoid dependency for basic testing
import numpy as np
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.api_config import RUNPOD_API_KEY, ENDPOINT_ID

class DiaStreamingClient:
    """Client for streaming audio from Dia-1.6B TTS RunPod endpoint"""
    
    def __init__(self, endpoint_id=None, api_key=None):
        """
        Initialize the Dia TTS streaming client
        
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
        
        # Setup audio playback
        self.sample_rate = 44100
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.pyaudio = None
        self.stream = None
    
    def _audio_player_thread(self):
        """Thread function to play audio from the queue"""
        try:
            # Commented out for basic testing without PyAudio
            print("Audio playback disabled - PyAudio not available")
            # self.pyaudio = pyaudio.PyAudio()
            # self.stream = self.pyaudio.open(
            #     format=pyaudio.paFloat32,
            #     channels=1,
            #     rate=self.sample_rate,
            #     output=True
            # )
            
            while not self.stop_event.is_set() or not self.audio_queue.empty():
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                    # Commented out for basic testing without PyAudio
                    # self.stream.write(audio_chunk.tobytes())
                    print("Audio chunk received (playback disabled)")
                    self.audio_queue.task_done()
                except queue.Empty:
                    continue
                
        except Exception as e:
            print(f"Audio player error: {e}")
        finally:
            # Commented out for basic testing without PyAudio
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'pyaudio') and self.pyaudio:
                self.pyaudio.terminate()
    
    def stream_speech(self, text, temperature=1.3, top_p=0.95, seed=None, audio_prompt=None, 
                      save_path=None, polling_interval=0.5, timeout=300):
        """
        Generate and stream speech from text using Dia-1.6B model
        
        Args:
            text (str): Text to convert to speech
            temperature (float, optional): Sampling temperature. Defaults to 1.3.
            top_p (float, optional): Top-p sampling value. Defaults to 0.95.
            seed (int, optional): Random seed for reproducible outputs. Defaults to None.
            audio_prompt (str, optional): Path to reference audio file for voice cloning. Defaults to None.
            save_path (str, optional): Path to save the complete audio file. Defaults to None.
            polling_interval (float, optional): Seconds between status checks. Defaults to 0.5.
            timeout (int, optional): Maximum time to wait for result in seconds. Defaults to 300.
        
        Returns:
            tuple: (success, result) where result is either the audio data or error message
        """
        # Start with a clean state
        self.audio_queue = queue.Queue()
        self.stop_event.clear()
        
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
            print("Submitting speech generation job...")
            response = requests.post(f"{self.base_url}/run", headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            job_id = result.get("id")
            
            if not job_id:
                return False, f"Failed to submit job: {result}"
            
            print(f"Job submitted with ID: {job_id}")
            
            # Start audio player thread
            print("Starting audio streaming...")
            audio_thread = threading.Thread(target=self._audio_player_thread)
            audio_thread.daemon = True
            audio_thread.start()
            
            # Poll for result
            start_time = time.time()
            complete_audio = None
            
            while True:
                if time.time() - start_time > timeout:
                    self.stop_event.set()
                    return False, f"Job timed out after {timeout} seconds"
                
                status_response = requests.get(f"{self.base_url}/status/{job_id}", headers=self.headers)
                status_data = status_response.json()
                
                status = status_data.get("status")
                
                if status == "COMPLETED":
                    output = status_data.get("output", {})
                    if "error" in output:
                        self.stop_event.set()
                        return False, f"Job failed: {output['error']}"
                    
                    audio_b64 = output.get("audio")
                    if not audio_b64:
                        self.stop_event.set()
                        return False, "No audio data in response"
                    
                    # Decode audio data
                    audio_bytes = base64.b64decode(audio_b64)
                    complete_audio = audio_bytes
                    
                    # Convert to numpy array and queue for playback
                    # Since we have the complete audio, we can load it into the queue
                    # This is a simplification; real streaming would handle chunks differently
                    try:
                        import soundfile as sf
                        import io
                        data, _ = sf.read(io.BytesIO(audio_bytes))
                        data = data.astype(np.float32)
                        
                        # Break into smaller chunks for smoother playback
                        chunk_size = 4096
                        for i in range(0, len(data), chunk_size):
                            chunk = data[i:i + chunk_size]
                            self.audio_queue.put(chunk)
                    
                    except Exception as e:
                        print(f"Error processing audio data: {e}")
                    
                    break
                
                elif status in ["FAILED", "CANCELLED"]:
                    self.stop_event.set()
                    error = status_data.get("error", "Unknown error")
                    return False, f"Job {status.lower()}: {error}"
                
                # Wait before polling again
                time.sleep(polling_interval)
            
            # Wait for audio playback to complete
            print("Audio generation complete, waiting for playback to finish...")
            self.audio_queue.join()
            self.stop_event.set()
            audio_thread.join()
            
            # Save to file if path is provided
            if save_path and complete_audio:
                with open(save_path, "wb") as f:
                    f.write(complete_audio)
                print(f"Audio saved to {save_path}")
            
            return True, complete_audio
                
        except requests.exceptions.RequestException as e:
            self.stop_event.set()
            return False, f"Request error: {str(e)}"
        except Exception as e:
            self.stop_event.set()
            return False, f"Unexpected error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Stream speech using Dia-1.6B on RunPod serverless")
    parser.add_argument("text", type=str, help="Text to convert to speech")
    parser.add_argument("--output", "-o", type=str, help="Output audio file path (optional)")
    parser.add_argument("--temperature", "-t", type=float, default=1.3, help="Sampling temperature")
    parser.add_argument("--top-p", "-p", type=float, default=0.95, help="Top-p sampling value")
    parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducible outputs")
    parser.add_argument("--audio-prompt", "-a", type=str, help="Path to reference audio for voice cloning")
    parser.add_argument("--endpoint-id", "-e", type=str, help="RunPod endpoint ID (overrides config)")
    parser.add_argument("--api-key", "-k", type=str, help="RunPod API key (overrides config)")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum time to wait in seconds")
    
    args = parser.parse_args()
    
    try:
        client = DiaStreamingClient(endpoint_id=args.endpoint_id, api_key=args.api_key)
        
        print(f"Generating speech for text: '{args.text}'")
        if args.audio_prompt:
            print(f"Using voice reference from: {args.audio_prompt}")
        
        success, result = client.stream_speech(
            text=args.text,
            temperature=args.temperature,
            top_p=args.top_p,
            seed=args.seed,
            audio_prompt=args.audio_prompt,
            save_path=args.output,
            timeout=args.timeout
        )
        
        if success:
            print(f"Speech streaming completed successfully")
            return 0
        else:
            print(f"Speech streaming failed: {result}")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())