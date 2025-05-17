#!/usr/bin/env python3
"""
Dia TTS inference-only CLI interface for RunPod serverless deployment
"""
import os
import sys
import argparse
from pathlib import Path

# Import our modules
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.api_config import validate_api_config
from client.inference import DiaTTSClient
from client.streaming import DiaStreamingClient

def show_banner():
    """Show Dia TTS RunPod banner"""
    banner = r"""
    ██████╗ ██╗ █████╗     ████████╗████████╗███████╗
    ██╔══██╗██║██╔══██╗    ╚══██╔══╝╚══██╔══╝██╔════╝
    ██║  ██║██║███████║       ██║      ██║   ███████╗
    ██║  ██║██║██╔══██║       ██║      ██║   ╚════██║
    ██████╔╝██║██║  ██║       ██║      ██║   ███████║
    ╚═════╝ ╚═╝╚═╝  ╚═╝       ╚═╝      ╚═╝   ╚══════╝
                                                      
     RunPod Serverless TTS - nari-labs/Dia-1.6B
    """
    print(banner)

def admin_refresh_model(args):
    """Send a command to refresh the model without generating speech"""
    import requests
    from config.api_config import RUNPOD_API_KEY, ENDPOINT_ID, get_endpoint_url
    
    endpoint_id = args.endpoint_id or ENDPOINT_ID
    api_key = args.api_key or RUNPOD_API_KEY
    
    if not endpoint_id:
        print("Error: No endpoint ID provided")
        return 1
    
    base_url = get_endpoint_url(endpoint_id)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare admin command payload
    payload = {
        "input": {
            "command": "refresh_model"
        }
    }
    
    try:
        print(f"Sending model refresh command to endpoint {endpoint_id}...")
        response = requests.post(f"{base_url}/run", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        job_id = result.get("id")
        
        if not job_id:
            print(f"Failed to submit refresh command: {result}")
            return 1
        
        print(f"Command submitted with job ID: {job_id}")
        print("Waiting for command to complete...")
        
        # Poll for result
        polling_interval = 2
        timeout = 60
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                print(f"Command timed out after {timeout} seconds")
                return 1
            
            status_response = requests.get(f"{base_url}/status/{job_id}", headers=headers)
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "COMPLETED":
                output = status_data.get("output", {})
                if output.get("status") == "success":
                    print(f"Model refresh successful: {output.get('message', 'Model refreshed')}")
                    return 0
                else:
                    print(f"Model refresh failed: {output}")
                    return 1
            
            elif status in ["FAILED", "CANCELLED"]:
                error = status_data.get("error", "Unknown error")
                print(f"Command {status.lower()}: {error}")
                return 1
            
            time.sleep(polling_interval)
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return 1

def main():
    """Main entry point for the CLI"""
    show_banner()
    
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Dia-1.6B RunPod Serverless Inference CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add global arguments
    parser.add_argument("--endpoint-id", type=str, help="RunPod endpoint ID (overrides env var)")
    parser.add_argument("--api-key", type=str, help="RunPod API key (overrides env var)")
    
    # Add inference arguments directly to main parser
    parser.add_argument("text", nargs="?", type=str, help="Text to convert to speech")
    parser.add_argument("--output", "-o", type=str, default="output.wav", help="Output audio file path")
    parser.add_argument("--temperature", "-t", type=float, help="Sampling temperature")
    parser.add_argument("--top-p", "-p", type=float, help="Top-p sampling value")
    parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducible outputs")
    parser.add_argument("--audio-prompt", "-a", type=str, help="Path to reference audio for voice cloning")
    parser.add_argument("--stream", action="store_true", help="Stream audio output")
    parser.add_argument("--status", action="store_true", help="Check endpoint status instead of generating speech")
    parser.add_argument("--refresh-model", action="store_true", help="Force the model to refresh from Hugging Face")
    parser.add_argument("--admin-refresh", action="store_true", help="Admin command to refresh the model without generating speech")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate API configuration
    is_valid, message = validate_api_config()
    if not is_valid:
        print(f"Error: {message}")
        print("Make sure RUNPOD_API_KEY and ENDPOINT_ID are set in your environment.")
        return 1
    
    # Check endpoint status if requested
    if args.status:
        return check_status(args)
    
    # Admin refresh command takes precedence
    if args.admin_refresh:
        return admin_refresh_model(args)
    
    # If no text is specified and not checking status or doing admin refresh, show help
    if not args.text:
        parser.print_help()
        return 0
    
    # Generate speech
    return generate_speech(args)

def check_status(args):
    """Check status of serverless endpoint using REST API"""
    import requests
    from config.api_config import RUNPOD_API_KEY, ENDPOINT_ID, RUNPOD_API_BASE_URL
    
    endpoint_id = args.endpoint_id or ENDPOINT_ID
    api_key = args.api_key or RUNPOD_API_KEY
    
    if not endpoint_id:
        print("Error: No endpoint ID provided")
        return 1
    
    print(f"Checking status of endpoint {endpoint_id}...")
    
    # REST API endpoint for serverless status
    rest_url = f"https://api.runpod.io/v1/endpoints/{endpoint_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get endpoint details
        response = requests.get(rest_url, headers=headers)
        response.raise_for_status()
        endpoint_data = response.json()
        
        # Get endpoint metrics
        metrics_url = f"https://api.runpod.io/v1/endpoints/{endpoint_id}/metrics"
        metrics_response = requests.get(metrics_url, headers=headers)
        metrics_response.raise_for_status()
        metrics_data = metrics_response.json()
        
        # Combine data from both endpoints
        status = {}
        
        # Basic endpoint details
        if isinstance(endpoint_data, dict):
            status["id"] = endpoint_data.get("id", endpoint_id)
            status["name"] = endpoint_data.get("name", "Unknown")
            status["templateId"] = endpoint_data.get("templateId", "Unknown")
            status["gpuIds"] = endpoint_data.get("gpuTypeIds", [])
            status["minWorkers"] = endpoint_data.get("workersMin", 0)
            status["maxWorkers"] = endpoint_data.get("workersMax", 0)
            status["idleTimeout"] = endpoint_data.get("idleTimeout", 0)
            status["flashBoot"] = endpoint_data.get("flashboot", False)
        elif isinstance(endpoint_data, list) and len(endpoint_data) > 0:
            # Extract from list if API returns data in a different format
            endpoint_info = endpoint_data[0]
            status["id"] = endpoint_info.get("id", endpoint_id)
            status["name"] = endpoint_info.get("name", "Unknown")
            status["templateId"] = endpoint_info.get("templateId", "Unknown")
            status["gpuIds"] = endpoint_info.get("gpuTypeIds", [])
            status["minWorkers"] = endpoint_info.get("workersMin", 0)
            status["maxWorkers"] = endpoint_info.get("workersMax", 0)
            status["idleTimeout"] = endpoint_info.get("idleTimeout", 0)
            status["flashBoot"] = endpoint_info.get("flashboot", False)
        
        # Performance metrics
        if isinstance(metrics_data, dict):
            status["workersRunning"] = metrics_data.get("workersRunning", 0)
            status["workersWaiting"] = metrics_data.get("workersWaiting", 0)
            status["requestsHandled"] = metrics_data.get("requestsHandled", 0)
            status["requestsErrors"] = metrics_data.get("requestsErrors", 0)
            status["averageResponseTime"] = metrics_data.get("averageResponseTime", 0)
            status["lastRequestTimestamp"] = metrics_data.get("lastRequestTimestamp", "N/A")
        elif isinstance(metrics_data, list) and len(metrics_data) > 0:
            # Extract from list if API returns data in a different format
            metrics_info = metrics_data[0]
            status["workersRunning"] = metrics_info.get("workersRunning", 0)
            status["workersWaiting"] = metrics_info.get("workersWaiting", 0)
            status["requestsHandled"] = metrics_info.get("requestsHandled", 0)
            status["requestsErrors"] = metrics_info.get("requestsErrors", 0)
            status["averageResponseTime"] = metrics_info.get("averageResponseTime", 0)
            status["lastRequestTimestamp"] = metrics_info.get("lastRequestTimestamp", "N/A")
        
        # Print status information
        print("\nEndpoint Status:")
        print(f"Name:                   {status.get('name', 'Unknown')}")
        print(f"Template ID:            {status.get('templateId', 'Unknown')}")
        
        gpu_ids = status.get('gpuIds', [])
        if isinstance(gpu_ids, list):
            print(f"GPU Types:              {', '.join(gpu_ids)}")
        else:
            print(f"GPU Types:              {gpu_ids}")
            
        print(f"Min Workers:            {status.get('minWorkers', 0)}")
        print(f"Max Workers:            {status.get('maxWorkers', 0)}")
        print(f"Idle Timeout:           {status.get('idleTimeout', 0)} seconds")
        print(f"Flash Boot:             {status.get('flashBoot', False)}")
        print(f"\nCurrent Status:")
        print(f"Workers Running:        {status.get('workersRunning', 0)}")
        print(f"Workers Waiting:        {status.get('workersWaiting', 0)}")
        print(f"Requests Handled:       {status.get('requestsHandled', 0)}")
        print(f"Requests Errors:        {status.get('requestsErrors', 0)}")
        print(f"Average Response Time:  {status.get('averageResponseTime', 0)} ms")
        print(f"Last Request Time:      {status.get('lastRequestTimestamp', 'N/A')}")
        
        return 0
        
    except requests.exceptions.RequestException as e:
        print(f"Error checking status: {e}")
        return 1

def generate_speech(args):
    """Generate speech from text"""
    # Use streaming client if requested, otherwise use regular client
    if args.stream:
        client_class = DiaStreamingClient
    else:
        client_class = DiaTTSClient
    
    try:
        client = client_class(endpoint_id=args.endpoint_id, api_key=args.api_key)
        
        print(f"Generating speech for text: '{args.text}'")
        if args.audio_prompt:
            print(f"Using voice reference from: {args.audio_prompt}")
        if args.refresh_model:
            print("Model will be refreshed from Hugging Face")
        
        # Prepare parameters
        params = {
            'text': args.text,
            'save_path': args.output,
        }
        
        # Add optional parameters if provided
        if args.temperature is not None:
            params['temperature'] = args.temperature
        
        if args.top_p is not None:
            params['top_p'] = args.top_p
        
        if args.seed is not None:
            params['seed'] = args.seed
        
        if args.audio_prompt:
            params['audio_prompt'] = args.audio_prompt
        
        if args.refresh_model:
            params['force_refresh'] = True
        
        # Generate speech
        if args.stream:
            success, result = client.stream_speech(**params)
        else:
            success, result = client.generate_speech(**params)
        
        if success:
            print(f"Speech generation completed successfully")
            print(f"Output saved to: {args.output}")
            return 0
        else:
            print(f"Speech generation failed: {result}")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())