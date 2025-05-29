import runpod
import torch
import soundfile as sf
import io
import base64
import os
import json
import logging
from huggingface_hub import login
from dia.model import Dia

# Disable torch dynamo/inductor compilation to avoid C compiler requirement
import torch._dynamo
torch._dynamo.config.suppress_errors = True

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dia-tts-handler")

# Global model instance (loaded once per container)
model = None

def load_model(force_refresh=False):
    global model
    if model is None or force_refresh:
        if force_refresh and model is not None:
            logger.info("Force refreshing model from Hugging Face...")
            # Delete the old model reference to free up memory
            del model
            model = None
            # Force garbage collection to release memory
            import gc
            gc.collect()
            # Clear torch CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("CUDA cache cleared")
        
        # Check for HF token in RunPod secrets
        try:
            secrets_json = os.environ.get("RUNPOD_SECRETS", "{}")
            secrets = json.loads(secrets_json)
            hf_token = secrets.get("HUGGING_FACE_TOKEN")
            
            # Fall back to env var if secret not found
            if not hf_token:
                hf_token = os.environ.get("HUGGING_FACE_HUB_TOKEN")
                
            if hf_token:
                logger.info("Authenticating with Hugging Face Hub...")
                login(token=hf_token)
            else:
                logger.warning("No Hugging Face token found. Attempting anonymous download.")
        except Exception as e:
            logger.error(f"Error loading HF token: {str(e)}")
        
        # Configure cache directories to use network volume if available
        check_and_configure_cache_dirs()
        
        # Get model ID from environment or use default
        model_id = os.environ.get("MODEL_ID", "nari-labs/Dia-1.6B")
        compute_dtype = os.environ.get("COMPUTE_DTYPE", "float16")
        
        # Handle cache behavior for model refreshing
        if force_refresh:
            logger.info(f"Loading {model_id} model with cache disabled (force_refresh=True)...")
            # Configure HuggingFace environment to bypass cache
            os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"  # Disable cached token
            os.environ["TRANSFORMERS_OFFLINE"] = "0"  # Ensure online mode
            os.environ["HF_HOME"] = "/tmp/hf_temp_nocache"  # Use a temporary directory
            
            # Clear any existing temp directory
            if os.path.exists("/tmp/hf_temp_nocache"):
                import shutil
                try:
                    shutil.rmtree("/tmp/hf_temp_nocache")
                    os.makedirs("/tmp/hf_temp_nocache", exist_ok=True)
                    logger.info("Cleared temporary cache directory")
                except Exception as e:
                    logger.warning(f"Failed to clear temp directory: {e}")
        else:
            logger.info(f"Loading {model_id} model with cache enabled...")
            
        # Load the model with specified parameters - don't pass extra params to Dia.from_pretrained
        model = Dia.from_pretrained(model_id, compute_dtype=compute_dtype)
        logger.info("Model loaded successfully!")
        
    return model

def check_and_configure_cache_dirs():
    """Configure cache directories to use network volume if available"""
    # Log RUNPOD_SECRETS environment variable to understand what's available
    try:
        # Get the raw value without decoding to avoid logging actual secrets
        runpod_secrets_raw = os.environ.get("RUNPOD_SECRETS", "not set")
        has_secrets = runpod_secrets_raw != "not set" and runpod_secrets_raw != "{}"
        logger.info(f"RUNPOD_SECRETS is available: {has_secrets}")
        
        # Try to extract network volume information from secrets safely
        try:
            secrets = json.loads(os.environ.get("RUNPOD_SECRETS", "{}"))
            has_network_volume_id = "NETWORK_VOLUME_ID" in secrets
            has_volume_mount_path = "VOLUME_MOUNT_PATH" in secrets
            logger.info(f"Found NETWORK_VOLUME_ID in secrets: {has_network_volume_id}")
            logger.info(f"Found VOLUME_MOUNT_PATH in secrets: {has_volume_mount_path}")
            
            # If we have the volume ID, log it safely (partial redaction)
            if has_network_volume_id:
                vol_id = secrets["NETWORK_VOLUME_ID"]
                safe_vol_id = vol_id[:4] + "..." + vol_id[-4:] if len(vol_id) > 8 else "***"
                logger.info(f"Network Volume ID from secrets: {safe_vol_id}")
            
            # If we have the mount path, log it
            if has_volume_mount_path:
                logger.info(f"Volume Mount Path from secrets: {secrets['VOLUME_MOUNT_PATH']}")
        except Exception as e:
            logger.warning(f"Error parsing RUNPOD_SECRETS: {str(e)}")
    
        # Check for environment variables related to volumes
        network_volume_id_env = os.environ.get("NETWORK_VOLUME_ID", "not set")
        volume_mount_path_env = os.environ.get("VOLUME_MOUNT_PATH", "not set")
        logger.info(f"NETWORK_VOLUME_ID environment variable: {'set' if network_volume_id_env != 'not set' else 'not set'}")
        logger.info(f"VOLUME_MOUNT_PATH environment variable: {volume_mount_path_env if volume_mount_path_env != 'not set' else 'not set'}")
        
        # Log RunPod specific environment variables
        for env_var, value in os.environ.items():
            if env_var.startswith("RUNPOD_") and env_var != "RUNPOD_SECRETS":
                logger.info(f"Environment variable {env_var}: {value}")
        
        # Log other volume related environment variables
        for env_var, value in os.environ.items():
            if ("VOLUME" in env_var or "MOUNT" in env_var) and env_var not in ["NETWORK_VOLUME_ID", "VOLUME_MOUNT_PATH"]:
                logger.info(f"Environment variable {env_var}: {value}")
        
        # Try to get mount information
        import subprocess
        mount_output = subprocess.check_output("mount", shell=True).decode('utf-8')
        logger.info(f"Mount points: {mount_output}")
        
        # Check if 'df' command shows any network volumes
        df_output = subprocess.check_output("df -h", shell=True).decode('utf-8')
        logger.info(f"Disk usage (df -h): {df_output}")
        
        # List root directory contents
        root_dirs = os.listdir("/")
        logger.info(f"Root directory contents: {root_dirs}")
        
        # List contents of potential mount paths
        for path in ["/mnt", "/run", "/var", "/data", "/volume", "/runpod-volume"]:
            if os.path.exists(path):
                try:
                    contents = os.listdir(path)
                    logger.info(f"Contents of {path}: {contents}")
                    
                    # If this directory exists, check if we can write to it
                    try:
                        test_file = os.path.join(path, ".test_write_permission")
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        logger.info(f"✅ Have write permission to {path}")
                    except Exception as e:
                        logger.warning(f"❌ No write permission to {path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Could not list contents of {path}: {str(e)}")
    except Exception as e:
        logger.warning(f"Could not check mount points: {str(e)}")
    
    # First check if RunPod provides the mount path via environment variables
    volume_mount_path = None
    
    # Check both environment variables and secrets for volume mount path
    try:
        # Check environment variables first
        volume_mount_path = os.environ.get("VOLUME_MOUNT_PATH")
        
        # If not found, check secrets
        if not volume_mount_path:
            secrets_json = os.environ.get("RUNPOD_SECRETS", "{}")
            secrets = json.loads(secrets_json)
            volume_mount_path = secrets.get("VOLUME_MOUNT_PATH")
            
        if volume_mount_path:
            logger.info(f"Found volume mount path in environment: {volume_mount_path}")
    except Exception as e:
        logger.warning(f"Error getting volume mount path from environment: {str(e)}")
    
    # Build list of possible mount paths
    possible_data_dirs = []
    
    # Add the environment-provided path first if available
    if volume_mount_path and os.path.exists(volume_mount_path):
        possible_data_dirs.append(volume_mount_path)
    
    # Check for VOLUME_SEARCH_PATHS environment variable
    volume_search_paths = os.environ.get("VOLUME_SEARCH_PATHS", "")
    if volume_search_paths:
        logger.info(f"Found VOLUME_SEARCH_PATHS environment variable: {volume_search_paths}")
        paths = volume_search_paths.split(":")
        for path in paths:
            if path and path not in possible_data_dirs and os.path.exists(path):
                logger.info(f"Adding path from VOLUME_SEARCH_PATHS: {path}")
                possible_data_dirs.append(path)
    
    # Add common paths where RunPod might mount a network volume
    possible_data_dirs.extend([
        "/data",                # Standard RunPod mount path
        "/runpod-volume",       # Alternative RunPod mount path
        "/mnt/networkvolume",   # Another possible path
        "/mnt/data",            # Yet another possible path
        "/volume",              # One more possibility
        "/mnt/network-volume",  # Hyphenated version
        "/mnt/runpod-volume",   # RunPod prefixed version
        "/workspace/network-volume",  # Workspace mount
        "/mnt/volume",          # Simple volume name
        "/run/user/1000/gvfs",  # Another potential mount point
        "/media/user",          # Media mount point
        "/volumes"              # Additional potential location
    ])
    
    # Check for network volume ID in environment variable first
    network_volume_id = None
    try:
        secrets_json = os.environ.get("RUNPOD_SECRETS", "{}")
        secrets = json.loads(secrets_json)
        network_volume_id = secrets.get("NETWORK_VOLUME_ID")
        
        # Fall back to env var if secret not found
        if not network_volume_id:
            network_volume_id = os.environ.get("NETWORK_VOLUME_ID")
            
        if network_volume_id:
            # Try to find a mount directory specific to this volume ID
            logger.info(f"Looking for mount locations containing network volume ID")
            vol_id_lower = network_volume_id.lower()
            
            # Check for volume-specific paths (RunPod might mount with volume ID in path)
            vol_specific_paths = [
                f"/volume-{network_volume_id}",
                f"/volume_{network_volume_id}",
                f"/runpod-volume-{network_volume_id}",
                f"/runpod-volume_{network_volume_id}",
                f"/mnt/volume-{network_volume_id}",
                f"/mnt/volume_{network_volume_id}",
                f"/mnt/volumes/{network_volume_id}",
                f"/volumes/{network_volume_id}"
            ]
            
            for vol_path in vol_specific_paths:
                if os.path.exists(vol_path):
                    logger.info(f"Found volume-specific path: {vol_path}")
                    # Add this to the front of possible_data_dirs
                    possible_data_dirs.insert(0, vol_path)
    except Exception as e:
        logger.error(f"Error reading network volume ID: {str(e)}")
    
    # Try each possible mount location
    for data_dir in possible_data_dirs:
        if os.path.exists(data_dir) and os.path.isdir(data_dir):
            logger.info(f"Found potential network volume at {data_dir}")
            
            # List contents to help with debugging
            try:
                dir_contents = os.listdir(data_dir)
                logger.info(f"Contents of {data_dir}: {dir_contents}")
            except Exception as e:
                logger.warning(f"Could not list contents of {data_dir}: {str(e)}")
            
            # Create cache directories on the network volume
            hf_cache_dir = os.path.join(data_dir, "hf_cache")
            torch_cache_dir = os.path.join(data_dir, "torch_cache")
            
            try:
                os.makedirs(hf_cache_dir, exist_ok=True)
                os.makedirs(torch_cache_dir, exist_ok=True)
                
                # Verify write permissions by creating a test file
                test_file_path = os.path.join(data_dir, ".volume_test")
                with open(test_file_path, 'w') as f:
                    f.write("test")
                os.remove(test_file_path)
                
                # Set environment variables to use these directories
                os.environ["HF_HOME"] = hf_cache_dir
                os.environ["TRANSFORMERS_CACHE"] = hf_cache_dir
                os.environ["TORCH_HOME"] = torch_cache_dir
                
                logger.info(f"Using network volume for cache directories:")
                logger.info(f"  HF_HOME: {hf_cache_dir}")
                logger.info(f"  TORCH_HOME: {torch_cache_dir}")
                return  # Successfully configured
            except Exception as e:
                logger.warning(f"Found volume at {data_dir} but couldn't set up cache: {str(e)}")
                continue  # Try next possible location
    
    # Last resort: search the filesystem for volume paths
    logger.info("Searching filesystem for potential network volume paths...")
    try:
        import subprocess
        
        # Find directories with significant free space (likely to be network volumes)
        df_output = subprocess.check_output("df -h | sort -rn -k4 | head -n 5", shell=True).decode('utf-8')
        logger.info(f"Top directories by free space: {df_output}")
        
        # Parse df output to find directories with significant space
        # This might catch the network volume if it's mounted in a non-standard location
        try:
            for line in df_output.splitlines()[1:]:  # Skip header line
                parts = line.split()
                if len(parts) >= 6:  # Expected format: Filesystem Size Used Avail Use% Mounted on
                    mountpoint = parts[5]
                    available = parts[3]
                    
                    # Check if this mountpoint has significant space (at least 1G)
                    if 'G' in available or 'T' in available:
                        logger.info(f"Found high-capacity mountpoint: {mountpoint} with {available} available")
                        
                        # Try to use this as a cache directory
                        if os.path.exists(mountpoint) and os.access(mountpoint, os.W_OK):
                            try:
                                # Test write access
                                test_file = os.path.join(mountpoint, ".volume_test")
                                with open(test_file, 'w') as f:
                                    f.write("test")
                                os.remove(test_file)
                                
                                # Set up cache directories
                                hf_cache_dir = os.path.join(mountpoint, "hf_cache")
                                torch_cache_dir = os.path.join(mountpoint, "torch_cache")
                                
                                os.makedirs(hf_cache_dir, exist_ok=True)
                                os.makedirs(torch_cache_dir, exist_ok=True)
                                
                                # Set environment variables
                                os.environ["HF_HOME"] = hf_cache_dir
                                os.environ["TRANSFORMERS_CACHE"] = hf_cache_dir
                                os.environ["TORCH_HOME"] = torch_cache_dir
                                
                                logger.info(f"Using high-capacity mountpoint for cache directories:")
                                logger.info(f"  HF_HOME: {hf_cache_dir}")
                                logger.info(f"  TORCH_HOME: {torch_cache_dir}")
                                return  # Successfully configured
                            except Exception as e:
                                logger.warning(f"Found mountpoint at {mountpoint} but couldn't set up cache: {str(e)}")
        except Exception as e:
            logger.warning(f"Error processing df output: {str(e)}")
        
        # Check for any directory that might be a mount point
        # Skipping full filesystem search as it might be too expensive for serverless
        
        # Check if we can identify RunPod's specific volume structure
        for potential_dir in ["/mnt", "/run", "/volume", "/data", "/media"]:
            if os.path.exists(potential_dir):
                subdirs = os.listdir(potential_dir)
                logger.info(f"Checking {potential_dir} subdirectories: {subdirs}")
                
                # Look for anything that might be a volume
                volume_keywords = ["vol", "disk", "storage", "mount", "network", "runpod"]
                for subdir in subdirs:
                    for keyword in volume_keywords:
                        if keyword in subdir.lower():
                            full_path = os.path.join(potential_dir, subdir)
                            logger.info(f"Found potential volume at {full_path}")
                            
                            # Test if we can write to it
                            try:
                                test_file = os.path.join(full_path, ".volume_test")
                                with open(test_file, 'w') as f:
                                    f.write("test")
                                os.remove(test_file)
                                
                                # We found a writable directory! Try to use it
                                hf_cache_dir = os.path.join(full_path, "hf_cache")
                                torch_cache_dir = os.path.join(full_path, "torch_cache")
                                
                                try:
                                    os.makedirs(hf_cache_dir, exist_ok=True)
                                    os.makedirs(torch_cache_dir, exist_ok=True)
                                    
                                    # Set environment variables to use these directories
                                    os.environ["HF_HOME"] = hf_cache_dir
                                    os.environ["TRANSFORMERS_CACHE"] = hf_cache_dir
                                    os.environ["TORCH_HOME"] = torch_cache_dir
                                    
                                    logger.info(f"Using last-resort network volume for cache directories:")
                                    logger.info(f"  HF_HOME: {hf_cache_dir}")
                                    logger.info(f"  TORCH_HOME: {torch_cache_dir}")
                                    return  # Successfully configured
                                except Exception as e:
                                    logger.warning(f"Found volume at {full_path} but couldn't set up cache: {str(e)}")
                            except Exception as e:
                                logger.warning(f"Cannot write to {full_path}: {str(e)}")
    except Exception as e:
        logger.warning(f"Error during filesystem search: {str(e)}")
    
    # If we reach here, no usable network volume was found
    logger.warning("No network volume found, using default cache directories")
    
    # Log the default directories we're using
    logger.info(f"Default HF_HOME: {os.environ.get('HF_HOME')}")
    logger.info(f"Default TRANSFORMERS_CACHE: {os.environ.get('TRANSFORMERS_CACHE')}")
    logger.info(f"Default TORCH_HOME: {os.environ.get('TORCH_HOME')}")

def handler(event):
    global model
    
    # Get input data from the request
    input_data = event.get("input", {})
    
    # Command to manually set the cache directory
    if input_data.get("command") == "set_cache_dir":
        logger.info("Received set_cache_dir command")
        cache_dir = input_data.get("cache_dir")
        
        if not cache_dir:
            return {
                "status": "error",
                "message": "Missing cache_dir parameter"
            }
            
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to create cache directory: {str(e)}"
                }
        
        try:
            # Test write permissions
            test_file = os.path.join(cache_dir, ".cache_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            # Create subdirectories
            hf_cache_dir = os.path.join(cache_dir, "hf_cache")
            torch_cache_dir = os.path.join(cache_dir, "torch_cache")
            
            os.makedirs(hf_cache_dir, exist_ok=True)
            os.makedirs(torch_cache_dir, exist_ok=True)
            
            # Set environment variables
            os.environ["HF_HOME"] = hf_cache_dir
            os.environ["TRANSFORMERS_CACHE"] = hf_cache_dir
            os.environ["TORCH_HOME"] = torch_cache_dir
            
            return {
                "status": "success",
                "message": f"Cache directories set to {cache_dir}",
                "hf_cache": hf_cache_dir,
                "torch_cache": torch_cache_dir
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to set up cache directories: {str(e)}"
            }
    
    # Special debug command to return environment and filesystem information
    if input_data.get("command") == "debug_volumes":
        logger.info("Received debug_volumes command")
        import subprocess
        import platform
        
        debug_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "user": subprocess.check_output("whoami", shell=True).decode().strip(),
            "working_directory": os.getcwd(),
            "environment_variables": {
                k: v for k, v in os.environ.items() 
                if not k.startswith("AWS") and k != "RUNPOD_SECRETS" and "TOKEN" not in k
            }
        }
        
        # Check if network volume is mounted
        try:
            # List all mount points
            mounts = subprocess.check_output("mount", shell=True).decode()
            debug_info["mounts"] = mounts
            
            # Check disk usage
            disk_usage = subprocess.check_output("df -h", shell=True).decode()
            debug_info["disk_usage"] = disk_usage
            
            # List common directories
            dirs_to_check = ["/", "/data", "/mnt", "/run", "/volume", "/runpod-volume"]
            dir_contents = {}
            
            for d in dirs_to_check:
                if os.path.exists(d):
                    try:
                        dir_contents[d] = os.listdir(d)
                        # Check if we can write to this directory
                        try:
                            test_file = os.path.join(d, ".write_test")
                            with open(test_file, "w") as f:
                                f.write("test")
                            os.remove(test_file)
                            dir_contents[f"{d}_writable"] = True
                        except Exception as e:
                            dir_contents[f"{d}_writable"] = False
                            dir_contents[f"{d}_write_error"] = str(e)
                    except Exception as e:
                        dir_contents[d] = f"Error: {str(e)}"
            
            debug_info["directory_contents"] = dir_contents
        except Exception as e:
            debug_info["volume_check_error"] = str(e)
        
        return {
            "status": "success",
            "debug_info": debug_info
        }
    
    # Check for admin commands
    if input_data.get("command") == "refresh_model":
        logger.info("Received model refresh command")
        model = load_model(force_refresh=True)
        return {
            "status": "success",
            "message": "Model refreshed from Hugging Face Hub"
        }
    
    # Normal model loading if not already loaded
    if model is None:
        model = load_model()
    
    # Get input text from the request
    text = input_data.get("text", "")
    
    if not text:
        return {"error": "No text provided for speech generation."}
    
    # Optional parameters
    audio_prompt_b64 = input_data.get("audio_prompt")
    audio_prompt_bytes = None
    seed = input_data.get("seed")
    temperature = input_data.get("temperature", float(os.environ.get("DEFAULT_TEMPERATURE", 1.3)))
    top_p = input_data.get("top_p", float(os.environ.get("DEFAULT_TOP_P", 0.95)))
    force_model_refresh = input_data.get("force_refresh", False)
    
    # Check if we need to refresh the model for this request
    if force_model_refresh:
        logger.info("Request specified model refresh")
        model = load_model(force_refresh=True)
    
    if audio_prompt_b64:
        # Decode base64 audio prompt
        try:
            audio_prompt_bytes = base64.b64decode(audio_prompt_b64)
        except Exception as e:
            return {"error": f"Error decoding audio prompt: {str(e)}"}
    
    # Generate speech
    try:
        # Set seed for consistent voices if provided
        if seed is not None:
            torch.manual_seed(seed)
            
        # Generate audio
        # IMPORTANT: Do not use torch.compile in serverless environments
        # as it requires a C compiler which is not available by default
        # Additionally, torch._dynamo.config.suppress_errors is set at the top of this file
        try:
            # Set torch environment variables to prevent compilation
            os.environ["TORCH_COMPILE_DISABLE"] = "1"
            os.environ["PYTORCH_JIT"] = "0"
            
            output = model.generate(
                text, 
                audio_prompt=audio_prompt_bytes,
                temperature=temperature,
                top_p=top_p,
                use_torch_compile=False,  # Must be False to avoid C compiler error
                verbose=True
            )
        except RuntimeError as e:
            # If we still get a compilation error, log it and try again with additional flags
            if "Failed to find C compiler" in str(e):
                logger.warning("Compilation attempted despite disabled flags. Retrying with fallback...")
                # Force eager mode execution as a last resort
                with torch.jit.optimized_execution(False), torch.no_grad():
                    output = model.generate(
                        text, 
                        audio_prompt=audio_prompt_bytes,
                        temperature=temperature,
                        top_p=top_p,
                        use_torch_compile=False,
                        verbose=True
                    )
            else:
                # Re-raise if it's a different error
                raise
        
        # Convert audio to base64
        buffer = io.BytesIO()
        sf.write(buffer, output, 44100, format='WAV')
        buffer.seek(0)
        audio_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            "audio": audio_base64,
            "format": "wav",
            "sample_rate": 44100
        }
        
    except Exception as e:
        return {"error": f"Error generating speech: {str(e)}"}

# Start the serverless function
runpod.serverless.start({"handler": handler})