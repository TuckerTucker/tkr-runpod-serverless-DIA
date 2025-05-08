#!/usr/bin/env python3
"""
Script to delete a RunPod serverless template using REST API
"""
import os
import sys
import requests
import json
import argparse
from pathlib import Path

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.api_config import RUNPOD_API_KEY, RUNPOD_API_BASE_URL

def delete_template(template_id, api_key=None):
    """
    Delete a RunPod serverless template
    
    Args:
        template_id (str): ID of the template to delete
        api_key (str, optional): RunPod API key. Defaults to env var RUNPOD_API_KEY.
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    api_key = api_key or RUNPOD_API_KEY
    
    if not api_key:
        print("Error: No API key provided")
        return False
    
    if not template_id:
        print("Error: No template ID provided")
        return False
    
    # REST API endpoint for deleting a template
    url = f"{RUNPOD_API_BASE_URL}/templates/{template_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Deleting template {template_id}...")
        response = requests.delete(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 204:
            return True
        
        try:
            result = response.json()
            if "error" in result:
                print(f"Error deleting template: {result['error']}")
            else:
                print(f"Unexpected response: {result}")
        except:
            print(f"Error: Received status code {response.status_code}")
            
        return False
    
    except requests.exceptions.RequestException as e:
        print(f"Error deleting template: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Delete a RunPod serverless template")
    parser.add_argument("--template-id", type=str, help="Template ID to delete")
    parser.add_argument("--api-key", type=str, help="RunPod API key (overrides env var)")
    parser.add_argument("--force", action="store_true", help="Force deletion without confirmation")
    
    args = parser.parse_args()
    
    # Try to get the template ID from the environment if not provided
    template_id = args.template_id
    if not template_id:
        template_id = os.environ.get("TEMPLATE_ID")
        if not template_id:
            print("Error: No template ID provided")
            print("Please specify using --template-id or set TEMPLATE_ID in your .env file")
            return 1
    
    # Confirm deletion if not forced
    if not args.force:
        confirm = input(f"Are you sure you want to delete template {template_id}? This action cannot be undone. (y/n): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return 0
    
    # Delete the template
    success = delete_template(template_id, args.api_key)
    
    if success:
        print(f"Template {template_id} deleted successfully!")
        
        # Update .env file to remove TEMPLATE_ID if it matches
        env_path = Path(__file__).resolve().parent.parent / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            env_lines = env_content.splitlines()
            new_lines = []
            
            for line in env_lines:
                if line.startswith('TEMPLATE_ID=') and template_id in line:
                    # Skip this line to remove it
                    continue
                new_lines.append(line)
            
            with open(env_path, 'w') as f:
                f.write('\n'.join(new_lines))
                # Ensure there's a trailing newline
                if new_lines and not new_lines[-1].endswith('\n'):
                    f.write('\n')
            
            print(f"Template ID removed from .env file.")
        
        return 0
    else:
        print(f"Failed to delete template {template_id}.")
        return 1

if __name__ == "__main__":
    sys.exit(main())