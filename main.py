#!/usr/bin/env python3
"""
Main CLI interface for Dia-1.6B RunPod serverless deployment and management.

Note: Text-to-speech generation functionality has been moved to the dedicated
inference package located in the /inference directory. See /inference/README.md
for usage instructions.
"""
import os
import sys
import argparse
import json
from pathlib import Path

# Import our modules
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.api_config import validate_api_config

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

def main():
    """Main entry point for the CLI"""
    show_banner()
    
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Dia-1.6B RunPod Serverless Deployment & Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add global arguments
    parser.add_argument("--endpoint-id", type=str, help="RunPod endpoint ID (overrides env var)")
    parser.add_argument("--api-key", type=str, help="RunPod API key (overrides env var)")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup environment and dependencies")
    setup_parser.add_argument("--force", action="store_true", help="Force setup even if already set up")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy serverless endpoint")
    deploy_parser.add_argument("--name", type=str, default="Dia-1.6B-Endpoint", help="Name of the endpoint")
    deploy_parser.add_argument("--template-id", type=str, help="Template ID to use (required)")
    deploy_parser.add_argument("--min-workers", type=int, help="Minimum active workers")
    deploy_parser.add_argument("--max-workers", type=int, help="Maximum active workers")
    deploy_parser.add_argument("--flash-boot", action="store_true", help="Enable flash boot")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check endpoint status")
    status_parser.add_argument("--endpoint-id", type=str, help="Endpoint ID to check (overrides global)")
    
    # Delete endpoint command
    delete_parser = subparsers.add_parser("delete", help="Delete serverless endpoint")
    delete_parser.add_argument("--endpoint-id", type=str, help="Endpoint ID to delete (overrides global)")
    delete_parser.add_argument("--force", action="store_true", help="Force deletion without confirmation")
    
    # Delete template command
    delete_template_parser = subparsers.add_parser("delete-template", help="Delete serverless template")
    delete_template_parser.add_argument("--template-id", type=str, help="Template ID to delete (overrides env var)")
    delete_template_parser.add_argument("--force", action="store_true", help="Force deletion without confirmation")
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command is specified, show help
    if not args.command:
        parser.print_help()
        return 0
    
    # Validate API configuration
    is_valid, message = validate_api_config()
    if not is_valid and args.command not in ['setup']:
        print(f"Error: {message}")
        print("Run 'python main.py setup' to configure your environment.")
        return 1
    
    # Execute the command
    if args.command == "setup":
        return setup_environment(args)
    elif args.command == "deploy":
        return deploy_endpoint(args)
    elif args.command == "status":
        return check_status(args)
    elif args.command == "delete":
        return delete_endpoint(args)
    elif args.command == "delete-template":
        return delete_template(args)
    else:
        parser.print_help()
        return 0

def setup_environment(args):
    """Set up the environment and dependencies"""
    from scripts.setup_venv import setup_venv
    from scripts.update_requirements import update_requirements
    
    print("Setting up Dia-1.6B RunPod serverless environment...")
    
    # Create .env file if it doesn't exist
    env_path = Path(__file__).resolve().parent / '.env'
    if not env_path.exists() or args.force:
        print("Creating .env file...")
        with open(env_path, 'w') as f:
            with open(Path(__file__).resolve().parent / '.env.example', 'r') as example:
                f.write(example.read())
        print("Created .env file. Please edit it with your API keys and settings.")
    
    # Set up virtual environment
    result = setup_venv(force=args.force)
    if not result:
        print("Failed to set up virtual environment.")
        return 1
    
    # Update requirements
    result = update_requirements()
    if not result:
        print("Failed to update requirements.")
        return 1
    
    print("Environment setup complete!")
    print("Next steps:")
    print("1. Edit the .env file with your RunPod API key")
    print("2. Run './scripts/create_template.sh' to create a RunPod template")
    print("3. Run 'python main.py deploy --template-id <your-template-id>' to deploy")
    
    return 0

def deploy_endpoint(args):
    """Deploy a serverless endpoint"""
    # Import here to handle module not found errors gracefully
    try:
        from deployment.create_endpoint import create_endpoint
    except ImportError:
        print("Error: Failed to import deployment modules.")
        print("Make sure you've run 'python main.py setup' first.")
        return 1
    
    if not args.template_id:
        # Try to get from environment
        template_id = os.environ.get("TEMPLATE_ID")
        if template_id:
            args.template_id = template_id
        else:
            print("Error: --template-id is required")
            print("Run './scripts/create_template.sh' first to create a template.")
            return 1
    
    print(f"Deploying Dia-1.6B RunPod serverless endpoint '{args.name}'...")
    
    # Gather deployment parameters
    params = {
        'name': args.name,
        'template_id': args.template_id,
    }
    
    # Add optional parameters if provided
    if args.min_workers is not None:
        params['min_workers'] = args.min_workers
    
    if args.max_workers is not None:
        params['max_workers'] = args.max_workers
    
    if args.flash_boot is not None:
        params['flash_boot'] = args.flash_boot
    
    # Create the endpoint
    endpoint = create_endpoint(**params)
    
    if endpoint:
        print(f"Endpoint deployed successfully!")
        print(f"Endpoint ID: {endpoint['id']}")
        
        # Save endpoint ID to .env file
        env_path = Path(__file__).resolve().parent / '.env'
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
        print("Deployment failed.")
        return 1

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


def delete_endpoint(args):
    """Delete a serverless endpoint"""
    # Import here to handle module not found errors gracefully
    try:
        from deployment.delete_endpoint import delete_endpoint
    except ImportError:
        print("Error: Failed to import deployment modules.")
        print("Make sure you've run 'python main.py setup' first.")
        return 1
    
    from config.api_config import ENDPOINT_ID
    
    endpoint_id = args.endpoint_id or ENDPOINT_ID
    
    if not endpoint_id:
        print("Error: No endpoint ID provided")
        return 1
    
    # Confirm deletion if not forced
    if not args.force:
        confirm = input(f"Are you sure you want to delete endpoint {endpoint_id}? This action cannot be undone. (y/n): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return 0
    
    print(f"Deleting endpoint {endpoint_id}...")
    
    # Delete the endpoint
    success = delete_endpoint(endpoint_id)
    
    if success:
        print(f"Endpoint {endpoint_id} deleted successfully!")
        
        # Update .env file
        env_path = Path(__file__).resolve().parent / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Remove ENDPOINT_ID
            env_content = '\n'.join([
                line for line in env_content.splitlines()
                if not line.startswith('ENDPOINT_ID=')
            ])
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            print(f"Endpoint ID removed from .env file.")
        
        return 0
    else:
        print(f"Failed to delete endpoint {endpoint_id}.")
        return 1

def delete_template(args):
    """Delete a serverless template"""
    # Import here to handle module not found errors gracefully
    try:
        from deployment.delete_template import delete_template
    except ImportError:
        print("Error: Failed to import deployment modules.")
        print("Make sure you've run 'python main.py setup' first.")
        return 1
    
    # Get template ID from args or environment
    template_id = args.template_id
    if not template_id:
        template_id = os.environ.get('TEMPLATE_ID')
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
    
    print(f"Deleting template {template_id}...")
    
    # Delete the template
    success = delete_template(template_id)
    
    if success:
        print(f"Template {template_id} deleted successfully!")
        
        # Update .env file
        env_path = Path(__file__).resolve().parent / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Remove TEMPLATE_ID
            env_content = '\n'.join([
                line for line in env_content.splitlines()
                if not line.startswith('TEMPLATE_ID=')
            ])
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            print(f"Template ID removed from .env file.")
        
        return 0
    else:
        print(f"Failed to delete template {template_id}.")
        return 1

if __name__ == "__main__":
    sys.exit(main())