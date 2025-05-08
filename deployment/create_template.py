#!/usr/bin/env python3
"""
Script to create a RunPod template for Dia-1.6B with network volume and secrets
"""
import os
import sys
import requests
import json
import argparse
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.api_config import RUNPOD_API_KEY, RUNPOD_GRAPHQL_URL

def create_template(name, container_image, container_disk_size=20, 
                   env_vars=None, secrets=None, ports=None, 
                   volume_mount_path=None, volume_id=None):
    """
    Create a RunPod template with proper configuration for Dia-1.6B

    Args:
        name (str): Template name
        container_image (str): Docker image URL
        container_disk_size (int): Disk size in GB
        env_vars (dict): Environment variables to set in the container
        secrets (dict): Secrets to set in the container
        ports (list): List of ports to expose
        volume_mount_path (str): Path to mount volume in container
        volume_id (str): Network volume ID to mount

    Returns:
        dict: Response from RunPod API
    """
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    # GraphQL query for creating template
    query = """
    mutation createTemplate(
        $containerDiskSize: Int!,
        $dockerArgs: String,
        $env: [KeyValue]!,
        $imageName: String!,
        $name: String!,
        $ports: String,
        $readme: String,
        $volumeInGb: Int,
        $volumeMountPath: String
    ) {
        createTemplate(
            input: {
                containerDiskSize: $containerDiskSize,
                dockerArgs: $dockerArgs,
                env: $env,
                imageName: $imageName,
                name: $name,
                ports: $ports,
                readme: $readme,
                volumeInGb: $volumeInGb,
                volumeMountPath: $volumeMountPath
            }
        ) {
            id
            name
            imageName
            env {
                key
                value
            }
            volumeInGb
            volumeMountPath
            containerDiskSize
        }
    }
    """

    # Combined environment variables and secrets
    env_list = []
    
    # Add environment variables
    if env_vars:
        for key, value in env_vars.items():
            env_list.append({"key": key, "value": value})
    
    # Add secrets as special environment variables
    if secrets:
        for key, value in secrets.items():
            env_list.append({"key": key, "value": value, "isSecret": True})

    # Create readme content with template information
    readme = f"""# Dia-1.6B TTS Model Template

This template runs the nari-labs/Dia-1.6B text-to-speech model on RunPod serverless.

## Features

- Natural dialogue generation with multiple speakers
- Voice cloning capability with audio prompt
- Fast inference with CUDA support

## Required Environment Variables

None required. All configuration is built into the container.

## Secrets

- HUGGING_FACE_TOKEN: Your Hugging Face token for downloading the model

## Network Volume

{'Network volume is configured at ' + volume_mount_path if volume_id else 'No network volume configured'}

## Example Usage

```python
import requests
import base64

ENDPOINT_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run"
API_KEY = "YOUR_RUNPOD_API_KEY"

payload = {{
    "input": {{
        "text": "[S1] Hello, this is a test of the Dia TTS model.",
        "temperature": 1.3,
        "top_p": 0.95,
        "seed": 42
    }}
}}

headers = {{
    "Authorization": f"Bearer {{API_KEY}}",
    "Content-Type": "application/json"
}}

response = requests.post(ENDPOINT_URL, headers=headers, json=payload)
result = response.json()
print(result)

# Get audio data
if "output" in result and "audio" in result["output"]:
    audio_b64 = result["output"]["audio"]
    audio_bytes = base64.b64decode(audio_b64)
    
    with open("output.wav", "wb") as f:
        f.write(audio_bytes)
    print("Audio saved to output.wav")
```
"""

    # Convert ports list to JSON string
    ports_json = json.dumps(ports) if ports else None

    # Variables for GraphQL query
    variables = {
        "name": name,
        "imageName": container_image,
        "containerDiskSize": container_disk_size,
        "env": env_list,
        "ports": ports_json,
        "readme": readme,
        "volumeMountPath": volume_mount_path
    }

    payload = {
        "query": query,
        "variables": variables
    }

    try:
        response = requests.post(RUNPOD_GRAPHQL_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            print(f"Error creating template: {result['errors']}")
            return None
        
        return result["data"]["createTemplate"]
    
    except requests.exceptions.RequestException as e:
        print(f"Error creating template: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create a RunPod template for Dia-1.6B")
    parser.add_argument("--name", type=str, default="Dia-1.6B-TTS", help="Template name")
    parser.add_argument("--image", type=str, default="tuckertucker/dia-1.6b-tts-runpod:latest", 
                        help="Docker image name")
    parser.add_argument("--disk-size", type=int, default=20, help="Container disk size in GB")
    parser.add_argument("--volume-id", type=str, help="Network volume ID to mount")
    parser.add_argument("--volume-path", type=str, default="/data", 
                        help="Path to mount volume in container")
    parser.add_argument("--hf-token", type=str, help="Hugging Face token")
    
    args = parser.parse_args()
    
    # Environment variables for the container
    env_vars = {
        "MODEL_ID": "nari-labs/Dia-1.6B",
        "COMPUTE_DTYPE": "float16",
        "DEFAULT_TEMPERATURE": "1.3",
        "DEFAULT_TOP_P": "0.95",
        "DEFAULT_SEED": "42"
    }
    
    # Secrets to set
    secrets = {}
    if args.hf_token:
        secrets["HUGGING_FACE_TOKEN"] = args.hf_token
    else:
        # Try to get from environment
        hf_token = os.environ.get("HUGGINGFACE_TOKEN")
        if hf_token:
            secrets["HUGGING_FACE_TOKEN"] = hf_token
        else:
            print("Warning: No Hugging Face token provided. Model downloads may fail.")
            print("Please provide a token with --hf-token or set HUGGINGFACE_TOKEN environment variable.")
    
    # Get volume ID from args or environment
    volume_id = args.volume_id or os.environ.get("NETWORK_VOLUME_ID")
    volume_mount_path = args.volume_path if volume_id else None
    
    if volume_id:
        print(f"Using network volume: {volume_id}")
        print(f"Volume will be mounted at: {volume_mount_path}")
    else:
        print("No network volume specified. Template will not use network storage.")
    
    # Ports to expose
    ports = [
        {"published": "8000", "target": "8000", "protocol": "tcp"},
        {"published": "443", "target": "8000", "protocol": "tcp"}
    ]
    
    # Create the template
    template = create_template(
        name=args.name,
        container_image=args.image,
        container_disk_size=args.disk_size,
        env_vars=env_vars,
        secrets=secrets,
        ports=ports,
        volume_mount_path=volume_mount_path,
        volume_id=volume_id
    )
    
    if template:
        print(f"Template created successfully!")
        print(f"Template ID: {template['id']}")
        print(f"Template Name: {template['name']}")
        print(f"Container Image: {template['imageName']}")
        print(f"Container Disk Size: {template['containerDiskSize']} GB")
        
        if template.get('volumeMountPath'):
            print(f"Volume Mount Path: {template['volumeMountPath']}")
            print(f"Volume Size: {template['volumeInGb']} GB")
        
        # Print environment variables (excluding secrets)
        print("\nEnvironment Variables:")
        for env in template.get('env', []):
            if 'isSecret' not in env or not env['isSecret']:
                print(f"  {env['key']}={env['value']}")
        
        print("\nSecrets:")
        print("  HUGGING_FACE_TOKEN=********")
        
        print("\nUse this Template ID when deploying your serverless endpoint.")
        print(f"Template ID: {template['id']}")
    else:
        print("Failed to create template. Check your API key and parameters.")

if __name__ == "__main__":
    main()