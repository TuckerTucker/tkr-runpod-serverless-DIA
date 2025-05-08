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

def load_model():
    global model
    if model is None:
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
        
        logger.info(f"Loading {model_id} model with compute_dtype={compute_dtype}...")
        # Load the model with specified parameters
        model = Dia.from_pretrained(model_id, compute_dtype=compute_dtype)
        logger.info("Model loaded successfully!")
        
    return model

def check_and_configure_cache_dirs():
    """Configure cache directories to use network volume if available"""
    # Check if we have a network volume mounted
    data_dir = "/data"
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        # Create cache directories on the network volume
        hf_cache_dir = os.path.join(data_dir, "hf_cache")
        torch_cache_dir = os.path.join(data_dir, "torch_cache")
        
        os.makedirs(hf_cache_dir, exist_ok=True)
        os.makedirs(torch_cache_dir, exist_ok=True)
        
        # Set environment variables to use these directories
        os.environ["HF_HOME"] = hf_cache_dir
        os.environ["TRANSFORMERS_CACHE"] = hf_cache_dir
        os.environ["TORCH_HOME"] = torch_cache_dir
        
        logger.info(f"Using network volume for cache directories:")
        logger.info(f"  HF_HOME: {hf_cache_dir}")
        logger.info(f"  TORCH_HOME: {torch_cache_dir}")
    else:
        logger.info("No network volume found, using default cache directories")

def handler(event):
    global model
    if model is None:
        model = load_model()
    
    # Get input text from the request
    input_data = event.get("input", {})
    text = input_data.get("text", "")
    
    if not text:
        return {"error": "No text provided for speech generation."}
    
    # Optional parameters
    audio_prompt_b64 = input_data.get("audio_prompt")
    audio_prompt_bytes = None
    seed = input_data.get("seed")
    temperature = input_data.get("temperature", float(os.environ.get("DEFAULT_TEMPERATURE", 1.3)))
    top_p = input_data.get("top_p", float(os.environ.get("DEFAULT_TOP_P", 0.95)))
    
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