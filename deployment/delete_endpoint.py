#!/usr/bin/env python3
"""
Script to delete a RunPod serverless endpoint
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

API_URL = "https://api.runpod.io/graphql"

def delete_endpoint(endpoint_id):
    """
    Delete a RunPod serverless endpoint
    
    Args:
        endpoint_id (str): ID of the endpoint to delete
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # GraphQL query for deleting endpoint
    query = """
    mutation terminateServerlessEndpoint($id: String!) {
        terminateServerlessEndpoint(input: { id: $id }) {
            success
        }
    }
    """
    
    variables = {
        "id": endpoint_id
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if "errors" in result:
            print(f"Error deleting endpoint: {result['errors']}")
            return False
        
        return result["data"]["terminateServerlessEndpoint"]["success"]
    
    except requests.exceptions.RequestException as e:
        print(f"Error deleting endpoint: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Delete a RunPod serverless endpoint")
    parser.add_argument("endpoint_id", type=str, help="ID of the endpoint to delete")
    parser.add_argument("--force", action="store_true", help="Force deletion without confirmation")
    
    args = parser.parse_args()
    
    if not args.force:
        confirm = input(f"Are you sure you want to delete endpoint {args.endpoint_id}? This action cannot be undone. (y/n): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return
    
    # Delete the endpoint
    success = delete_endpoint(args.endpoint_id)
    
    if success:
        print(f"Endpoint {args.endpoint_id} deleted successfully!")
    else:
        print(f"Failed to delete endpoint {args.endpoint_id}. Check your API key and endpoint ID.")

if __name__ == "__main__":
    main()