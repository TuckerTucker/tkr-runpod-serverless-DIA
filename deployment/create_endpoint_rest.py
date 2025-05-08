#!/usr/bin/env python3
"""
Script to create a RunPod serverless endpoint for Dia-1.6B using REST API
"""
import os
import sys
import requests
import json
import argparse
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.api_config import RUNPOD_API_KEY
from config.system_config import GPU_TYPES, MIN_WORKERS, MAX_WORKERS, IDLE_TIMEOUT, FLASH_BOOT

API_URL = "https://api.runpod.io/v1/endpoints"

def create_endpoint(name, template_id, gpu_ids=None, min_workers=0, max_workers=3, 
                    idle_timeout=300, flash_boot=True, container_disk_size=20):
    """
    Create a RunPod serverless endpoint using the REST API
    
    Args:
        name (str): Name of the endpoint
        template_id (str): Template ID to use
        gpu_ids (list): List of GPU types to use (default: None)
        min_workers (int): Minimum active workers (default: 0)
        max_workers (int): Maximum active workers (default: 3)
        idle_timeout (int): Worker idle timeout in seconds (default: 300)
        flash_boot (bool): Enable flash boot for faster starts (default: True)
        container_disk_size (int): Container disk size in GB (default: 20)
    
    Returns:
        dict: Response from RunPod API
    """
    if gpu_ids is None:
        gpu_ids = GPU_TYPES
        
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "templateId": template_id,
        "gpuTypeIds": gpu_ids,
        "workersMin": min_workers,
        "workersMax": max_workers,
        "idleTimeout": idle_timeout,
        "flashboot": flash_boot,
        "containerDiskSizeGB": container_disk_size
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # REST API v1 has different response format
        if isinstance(result, dict) and "error" in result:
            print(f"Error creating endpoint: {result.get('error', 'Unknown error')}")
            return None
        
        # If result is a list, extract the first item (should be our endpoint)
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        
        # Otherwise, assume the result is our endpoint data
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error creating endpoint: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create a RunPod serverless endpoint for Dia-1.6B (REST API)")
    parser.add_argument("--name", type=str, default="Dia-1.6B-Endpoint", help="Name of the endpoint")
    parser.add_argument("--template-id", type=str, required=True, help="Template ID to use")
    parser.add_argument("--min-workers", type=int, default=MIN_WORKERS, help="Minimum active workers")
    parser.add_argument("--max-workers", type=int, default=MAX_WORKERS, help="Maximum active workers")
    parser.add_argument("--idle-timeout", type=int, default=IDLE_TIMEOUT, help="Worker idle timeout in seconds")
    parser.add_argument("--container-disk", type=int, default=20, help="Container disk size in GB")
    parser.add_argument("--no-flash-boot", action="store_false", dest="flash_boot", help="Disable flash boot")
    parser.set_defaults(flash_boot=FLASH_BOOT)
    
    args = parser.parse_args()
    
    # Create the endpoint
    endpoint = create_endpoint(
        name=args.name,
        template_id=args.template_id,
        min_workers=args.min_workers,
        max_workers=args.max_workers,
        idle_timeout=args.idle_timeout,
        flash_boot=args.flash_boot,
        container_disk_size=args.container_disk
    )
    
    if endpoint:
        print(f"Endpoint created successfully!")
        print(f"Endpoint ID: {endpoint.get('id')}")
        print(f"Endpoint Name: {endpoint.get('name')}")
        print(f"Template ID: {endpoint.get('templateId')}")
        print(f"Min Workers: {endpoint.get('workersMin', endpoint.get('minActiveWorkers', 0))}")
        print(f"Max Workers: {endpoint.get('workersMax', endpoint.get('maxActiveWorkers', 0))}")
        print(f"Idle Timeout: {endpoint.get('idleTimeout')} seconds")
        print(f"Flash Boot: {'Enabled' if endpoint.get('flashboot', endpoint.get('flashBoot', False)) else 'Disabled'}")
        
        # GPU IDs may be in different fields depending on API version
        gpu_ids = endpoint.get('gpuTypeIds', endpoint.get('gpuIds', []))
        if isinstance(gpu_ids, list):
            print(f"GPU Types: {', '.join(gpu_ids)}")
        else:
            print(f"GPU Types: {gpu_ids}")
        print("\nUse this Endpoint ID in your client applications.")
    else:
        print("Failed to create endpoint. Check your API key and parameters.")

if __name__ == "__main__":
    main()