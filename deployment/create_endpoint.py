#!/usr/bin/env python3
"""
Script to create a RunPod serverless endpoint for Dia-1.6B using REST API
"""
import os
import sys
import requests
import json
import argparse
import logging
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.api_config import RUNPOD_API_KEY
from config.system_config import GPU_TYPES, MIN_WORKERS, MAX_WORKERS, IDLE_TIMEOUT, FLASH_BOOT

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for RunPod REST API
API_BASE_URL = "https://rest.runpod.io/v1"

def rest_request(method, endpoint, headers, json_data=None, params=None):
    """
    Make a REST API request to RunPod.
    
    Args:
        method: HTTP method (GET, POST, PUT, etc.)
        endpoint: API endpoint
        headers: HTTP headers
        json_data: JSON data for POST/PUT requests
        params: URL parameters
        
    Returns:
        dict: API response or error
    """
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        logger.info(f"Making {method} request to {url}")
        if json_data:
            logger.info(f"Request data: {json.dumps(json_data, indent=2)}")
            
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            params=params
        )
        
        logger.info(f"Response status: {response.status_code}")
        
        # Try to parse response as JSON
        try:
            response_data = response.json()
            logger.info(f"Response data: {json.dumps(response_data, indent=2)}")
        except:
            logger.error(f"Response content: {response.content}")
            return {"error": f"Failed to parse response as JSON: {response.content}"}
        
        # Check for errors
        if response.status_code >= 400:
            error_msg = "Unknown error"
            if isinstance(response_data, dict):
                error_msg = response_data.get("error", "Unknown error")
                if "message" in response_data:
                    error_msg = response_data.get("message", error_msg)
                if "errors" in response_data:
                    error_details = response_data.get("errors", [])
                    error_msg = f"{error_msg}: {error_details}"
            elif isinstance(response_data, list) and len(response_data) > 0:
                error_msg = response_data[0].get("error", "Unknown error")
                if "message" in response_data[0]:
                    error_msg = response_data[0].get("message", error_msg)
            
            logger.error(f"Request failed with error: {error_msg}")
            return {"error": error_msg}
        
        # If response is a list, convert it to a dictionary with a 'data' field
        if isinstance(response_data, list):
            # Extract ID from the first item if available
            id_val = None
            if response_data and isinstance(response_data[0], dict) and "id" in response_data[0]:
                id_val = response_data[0]["id"]
            return {"data": response_data, "id": id_val}
        
        return response_data
        
    except Exception as e:
        logger.error(f"REST request failed: {e}")
        return {"error": str(e)}

def create_endpoint(name, template_id, gpu_ids=None, min_workers=0, max_workers=3, 
                    idle_timeout=300, flash_boot=True, container_disk_size=20,
                    network_volume_id=None):
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
        network_volume_id (str): Network volume ID to attach (default: None)
    
    Returns:
        dict: Endpoint information or None if creation failed
    """
    try:
        # Convert our GPU types to the RunPod API's expected format
        gpu_type_mapping = {
            'NVIDIA A4000': 'NVIDIA RTX A4000',
            'NVIDIA RTX 4000': 'NVIDIA RTX 4000 Ada Generation', 
            'NVIDIA RTX 3090': 'NVIDIA GeForce RTX 3090',
            'NVIDIA A5000': 'NVIDIA RTX A5000',
            'NVIDIA RTX 4090': 'NVIDIA GeForce RTX 4090'
        }
        
        if gpu_ids is None:
            # Use GPU mappings instead of direct GPU_TYPES
            gpu_ids = []
            for gpu_id in GPU_TYPES:
                if gpu_id in gpu_type_mapping:
                    gpu_ids.append(gpu_type_mapping[gpu_id])
                else:
                    # If we don't have a mapping, include it anyway (in case it's already in the correct format)
                    gpu_ids.append(gpu_id)
        
        # Make sure we have at least one valid GPU type
        if not gpu_ids:
            gpu_ids = ['NVIDIA RTX A4000', 'NVIDIA GeForce RTX 3090', 'NVIDIA RTX A5000']
            
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare the endpoint data with minimum required fields
        endpoint_data = {
            "name": name,
            "templateId": template_id,
            "gpuTypeIds": gpu_ids,
            "computeType": "GPU",
            "workersMin": min_workers,
            "workersMax": max_workers
        }
        
        # Add optional fields
        if idle_timeout is not None:
            endpoint_data["idleTimeout"] = idle_timeout
            
        if flash_boot is not None:
            endpoint_data["flashboot"] = flash_boot
        
        # Add network volume if provided
        if network_volume_id:
            endpoint_data["networkVolumeId"] = network_volume_id
            
        # Make the REST API request
        result = rest_request("POST", "endpoints", headers, endpoint_data)
        
        # Check for errors
        if result and "error" in result:
            logger.error(f"Error creating endpoint: {result['error']}")
            return None
            
        # Extract endpoint ID and info
        endpoint_id = result.get("id")
        if not endpoint_id and "data" in result:
            # It might be in a data array
            data = result.get("data")
            if isinstance(data, list) and len(data) > 0:
                endpoint_id = data[0].get("id")
                
        if not endpoint_id:
            logger.error("No endpoint ID found in response")
            return None
            
        # Construct a response object similar to the GraphQL one
        endpoint_info = {
            "id": endpoint_id,
            "name": name,
            "templateId": template_id,
            "gpuIds": gpu_ids,
            "minWorkers": min_workers,
            "maxWorkers": max_workers,
            "idleTimeout": idle_timeout,
            "flashBoot": flash_boot,
            "networkVolumeId": network_volume_id if network_volume_id else None,
            "workersRunning": 0,  # Default initial values
            "workersWaiting": 0,
            "requestsHandled": 0,
            "requestsErrors": 0,
            "averageResponseTime": 0
        }
        
        # Update with actual values from result if available
        for key in result:
            # Convert camelCase to snake_case and back to our format
            if key in ["id", "name", "templateId"]:
                endpoint_info[key] = result[key]
            elif key == "workersMin":
                endpoint_info["minWorkers"] = result[key]
            elif key == "workersMax":
                endpoint_info["maxWorkers"] = result[key]
            elif key == "idleTimeout":
                endpoint_info["idleTimeout"] = result[key]
            elif key == "flashboot":
                endpoint_info["flashBoot"] = result[key]
            elif key == "networkVolumeId":
                endpoint_info["networkVolumeId"] = result[key]
                
        return endpoint_info
        
    except Exception as e:
        logger.error(f"Error creating endpoint: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create a RunPod serverless endpoint for Dia-1.6B")
    parser.add_argument("--name", type=str, default="Dia-1.6B-Endpoint", help="Name of the endpoint")
    parser.add_argument("--template-id", type=str, required=True, help="Template ID to use")
    parser.add_argument("--min-workers", type=int, default=MIN_WORKERS, help="Minimum active workers")
    parser.add_argument("--max-workers", type=int, default=MAX_WORKERS, help="Maximum active workers")
    parser.add_argument("--idle-timeout", type=int, default=IDLE_TIMEOUT, help="Worker idle timeout in seconds")
    parser.add_argument("--container-disk", type=int, default=20, help="Container disk size in GB")
    parser.add_argument("--no-flash-boot", action="store_false", dest="flash_boot", help="Disable flash boot")
    parser.add_argument("--network-volume-id", type=str, help="Network volume ID to attach")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.set_defaults(flash_boot=FLASH_BOOT)
    
    args = parser.parse_args()
    
    # Set up verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print parameters when verbose
    if args.verbose:
        print("Deployment parameters:")
        print(f"  Name: {args.name}")
        print(f"  Template ID: {args.template_id}")
        print(f"  Min Workers: {args.min_workers}")
        print(f"  Max Workers: {args.max_workers}")
        print(f"  Flash Boot: {args.flash_boot}")
        print(f"  Network Volume ID: {args.network_volume_id}")
    
    # Get network volume ID from environment if not provided
    network_volume_id = args.network_volume_id
    if not network_volume_id:
        network_volume_id = os.environ.get("NETWORK_VOLUME_ID")
        if network_volume_id and args.verbose:
            print(f"  Using network volume ID from environment: {network_volume_id}")
    
    # Create the endpoint
    try:
        endpoint = create_endpoint(
            name=args.name,
            template_id=args.template_id,
            min_workers=args.min_workers,
            max_workers=args.max_workers,
            idle_timeout=args.idle_timeout,
            flash_boot=args.flash_boot,
            container_disk_size=args.container_disk,
            network_volume_id=network_volume_id
        )
        
        if endpoint:
            print(f"Endpoint created successfully!")
            print(f"Endpoint ID: {endpoint['id']}")
            print(f"Endpoint Name: {endpoint['name']}")
            print(f"Min Workers: {endpoint['minWorkers']}")
            print(f"Max Workers: {endpoint['maxWorkers']}")
            print(f"Idle Timeout: {endpoint['idleTimeout']} seconds")
            print(f"Flash Boot: {'Enabled' if endpoint['flashBoot'] else 'Disabled'}")
            print(f"GPU Types: {', '.join(endpoint['gpuIds'])}")
            if endpoint.get('networkVolumeId'):
                print(f"Network Volume: {endpoint['networkVolumeId']}")
            print("\nUse this Endpoint ID in your client applications.")
            
            # Save endpoint ID to .env file
            env_path = Path(__file__).resolve().parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                # Replace or add ENDPOINT_ID
                if 'ENDPOINT_ID=' in env_content:
                    env_content = '\n'.join([
                        line if not line.startswith('ENDPOINT_ID=') else f'ENDPOINT_ID={endpoint["id"]}'
                        for line in env_content.splitlines()
                    ])
                else:
                    env_content += f'\nENDPOINT_ID={endpoint["id"]}\n'
                
                with open(env_path, 'w') as f:
                    f.write(env_content)
                
                print(f"Endpoint ID saved to .env file.")
            
            return 0
        else:
            print("Error: Failed to create endpoint. Response contained no endpoint data.")
            return 1
    except Exception as e:
        print(f"Error creating endpoint: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Unhandled error in main: {e}")
        sys.exit(1)