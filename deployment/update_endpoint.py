#!/usr/bin/env python3
"""
Script to update a RunPod serverless endpoint
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
from config.system_config import GPU_TYPES, MIN_WORKERS, MAX_WORKERS, IDLE_TIMEOUT

API_URL = "https://api.runpod.io/graphql"

def update_endpoint(endpoint_id, min_workers=None, max_workers=None, idle_timeout=None, gpu_ids=None):
    """
    Update a RunPod serverless endpoint
    
    Args:
        endpoint_id (str): ID of the endpoint to update
        min_workers (int, optional): New minimum active workers
        max_workers (int, optional): New maximum active workers
        idle_timeout (int, optional): New worker idle timeout in seconds
        gpu_ids (list, optional): New list of GPU types to use
    
    Returns:
        dict: Updated endpoint information
    """
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare variables
    variables = {
        "input": {
            "id": endpoint_id
        }
    }
    
    # Add optional parameters if provided
    if min_workers is not None:
        variables["input"]["minWorkers"] = min_workers
    
    if max_workers is not None:
        variables["input"]["maxWorkers"] = max_workers
    
    if idle_timeout is not None:
        variables["input"]["idleTimeout"] = idle_timeout
    
    if gpu_ids is not None:
        variables["input"]["gpuIds"] = gpu_ids
    
    # GraphQL query for updating endpoint
    query = """
    mutation updateServerlessEndpoint($input: UpdateServerlessEndpointInput!) {
        updateServerlessEndpoint(input: $input) {
            id
            name
            templateId
            gpuIds
            minWorkers
            maxWorkers
            idleTimeout
            flashBoot
            workersRunning
            workersWaiting
            requestsHandled
            requestsErrors
            averageResponseTime
        }
    }
    """
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            print(f"Error updating endpoint: {result['errors']}")
            return None
        
        return result["data"]["updateServerlessEndpoint"]
    
    except requests.exceptions.RequestException as e:
        print(f"Error updating endpoint: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Update a RunPod serverless endpoint")
    parser.add_argument("endpoint_id", type=str, help="ID of the endpoint to update")
    parser.add_argument("--min-workers", type=int, help="New minimum active workers")
    parser.add_argument("--max-workers", type=int, help="New maximum active workers")
    parser.add_argument("--idle-timeout", type=int, help="New worker idle timeout in seconds")
    parser.add_argument("--gpu-ids", type=str, nargs="+", help="New list of GPU types to use (space-separated)")
    
    args = parser.parse_args()
    
    # Make sure at least one parameter is provided
    if not any([args.min_workers is not None, args.max_workers is not None, 
                args.idle_timeout is not None, args.gpu_ids is not None]):
        print("Error: At least one parameter to update must be provided.")
        parser.print_help()
        return
    
    # Update the endpoint
    endpoint = update_endpoint(
        endpoint_id=args.endpoint_id,
        min_workers=args.min_workers,
        max_workers=args.max_workers,
        idle_timeout=args.idle_timeout,
        gpu_ids=args.gpu_ids
    )
    
    if endpoint:
        print(f"Endpoint {args.endpoint_id} updated successfully!")
        print(f"Endpoint Name: {endpoint['name']}")
        print(f"Min Workers: {endpoint['minWorkers']}")
        print(f"Max Workers: {endpoint['maxWorkers']}")
        print(f"Idle Timeout: {endpoint['idleTimeout']} seconds")
        print(f"Flash Boot: {'Enabled' if endpoint['flashBoot'] else 'Disabled'}")
        print(f"GPU Types: {', '.join(endpoint['gpuIds'])}")
        print(f"Workers Running: {endpoint['workersRunning']}")
        print(f"Workers Waiting: {endpoint['workersWaiting']}")
        print(f"Requests Handled: {endpoint['requestsHandled']}")
        print(f"Requests Errors: {endpoint['requestsErrors']}")
        print(f"Average Response Time: {endpoint['averageResponseTime']} ms")
    else:
        print(f"Failed to update endpoint {args.endpoint_id}. Check your API key and parameters.")

if __name__ == "__main__":
    main()