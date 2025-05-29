# Dia TTS RunPod Serverless Deployment

This project provides a comprehensive implementation for deploying the Hugging Face text-to-speech model "nari-labs/Dia-1.6B" on RunPod's serverless infrastructure. Dia-1.6B generates realistic dialogue from text scripts with multiple speakers and non-verbal sounds like laughter.

> **IMPORTANT**: This implementation uses RunPod's REST API exclusively instead of the GraphQL API for all serverless operations.

## Features

- **Complete Serverless Implementation**: Docker container with handler code for running Dia-1.6B on RunPod serverless.
- **Deployment Automation**: Scripts for creating, managing, and monitoring RunPod serverless endpoints.
- **Client Libraries**: Python client libraries for both regular and streaming TTS generation.
- **Voice Cloning Support**: Support for voice cloning using reference audio samples.
- **Dual CLI Interface**: Separate interfaces for deployment/management and inference operations.
- **Model Caching**: Support for network volumes to cache model files between runs, reducing startup time.
- **Security Features**: Secure handling of Hugging Face tokens via RunPod secrets.

## Requirements

- Python 3.8+ (Python 3.10+ recommended)
- RunPod account with API key
- Docker (for building and pushing the container image)
- GPU with at least 16GB VRAM (A4000 or better recommended)
- Hugging Face account and API token (for model access)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/dia-tts-runpod-serverless.git
cd dia-tts-runpod-serverless
```

### 2. Set up the environment

```bash
source activate.sh
```

This will automatically create a virtual environment if needed and install dependencies.

### 3. Configure your API keys

Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

Then edit the `.env` file and add your RunPod API key and Hugging Face token:

```
# Authentication
RUNPOD_API_KEY=your_runpod_api_key_here
HUGGINGFACE_TOKEN=your_huggingface_token_here

# Runpod Network Volume (optional)
# NETWORK_VOLUME_ID=your_network_volume_id
```

### 4. Build and push the Docker image

```bash
cd serverless
./build_with_token.sh
```

This will:
1. Build the Docker image with cross-platform compatibility (targeting linux/amd64)
2. Push it to Docker Hub if you choose (requires Docker Hub account)
3. Properly handle security by NOT embedding the Hugging Face token in the image

#### Security Note:

We provide two build scripts:
- `build_with_token.sh`: The recommended script, which uses Docker Buildx for cross-platform compatibility and ensures tokens are handled securely.
- `build_and_push.sh`: A simpler legacy script that doesn't handle cross-platform builds. Not recommended.

#### Why cross-platform builds matter:

If you're building on an ARM-based machine (like an M1/M2 Mac), you need to use `build_with_token.sh` to ensure the image is compatible with RunPod's x86_64 (amd64) servers.

### 5. Create a RunPod template

You can create a template using the provided script:

```bash
./scripts/create_template.sh
```

This script will:
1. Create a template using your RUNPOD_API_KEY from the .env file
2. Configure the HUGGING_FACE_TOKEN as a RunPod secret automatically
3. Set up network volume mounting if you've provided a NETWORK_VOLUME_ID in your .env file
4. Save the template ID to your .env file for deployment

#### Advanced Options:

The script accepts the following parameters:
```bash
./scripts/create_template.sh [--name NAME] [--image IMAGE] [--disk-size SIZE] [--volume-id ID] [--volume-path PATH] [--hf-token TOKEN]
```

#### Manual Template Creation:

You can also create a template manually via the RunPod dashboard:
1. Go to RunPod dashboard → Serverless → Templates
2. Click "New Template"
3. Enter the following details:
   - Name: Dia-1.6B TTS
   - Container Image: tuckertucker/dia-1.6b-tts-runpod:latest
   - Container Disk Size: 20GB
4. Add the following secret:
   - Key: HUGGING_FACE_TOKEN
   - Value: Your Hugging Face token (same as in your .env file)
5. (Optional) Configure a network volume:
   - Network Volume ID: Your volume ID
   - Mount Path: /data
6. Click "Save Template"
7. Note the template ID for deployment

### 6. Deploy the serverless endpoint

Once you have created a template (using the script or manually), you can deploy a serverless endpoint:

```bash
./scripts/deploy.sh --template-id your_template_id
```

If you used the create_template.sh script, the template ID was saved to your .env file, so you can simply run:

```bash
./scripts/deploy.sh
```

#### Advanced Deployment Options:

The script accepts the following parameters:
```bash
./scripts/deploy.sh --template-id YOUR_TEMPLATE_ID [--name NAME] [--min-workers NUM] [--max-workers NUM] [--no-flash-boot] [--network-volume-id ID]
```

You can also deploy using the main CLI:
```bash
python main.py deploy --template-id your_template_id [--name NAME] [--min-workers NUM] [--max-workers NUM] [--flash-boot]
```

### 7. Generate speech

You can use the standalone inference package:

```bash
# Using the script in the inference package
python inference/inference.py "[S1] Hello, this is a test of the Dia TTS model." --output test.wav

# If you've installed the package
# pip install -e ./inference
dia-tts "[S1] Hello, this is a test of the Dia TTS model." --output test.wav
```

You can also generate speech with voice cloning:

```bash
python inference/inference.py "[S1] This is my cloned voice speaking." --audio-prompt reference.wav --output cloned.wav
```

Or use streaming mode:

```bash
python inference/inference.py "[S1] This text will be generated and streamed in real-time." --stream --output stream_test.wav
```

You can also use the inference package programmatically in your own scripts:

```python
from inference import DiaTTSClient

client = DiaTTSClient()
client.generate_speech(
    text="[S1] Hello, this is programmatic TTS generation.",
    save_path="output.wav"
)
```

> **Note**: The original `python main.py generate` command is no longer supported. All speech generation functionality has been moved to the dedicated `inference` package.

## Security Considerations

- **Hugging Face Token**: The Hugging Face token is not baked into the Docker image. Instead, it is provided via RunPod secrets at runtime, which is a more secure approach.
- **Environment Variables**: Sensitive information like API keys should be stored in the `.env` file, which is not committed to version control.
- **Network Volumes**: For sharing data between serverless workers, use RunPod network volumes instead of embedding data in the container.

## API Implementation

This project uses RunPod's APIs as follows:

1. **Endpoint Management**: REST API (v1) at `api.runpod.io` for creating, updating, and monitoring endpoints
2. **Inference Requests**: Serverless API (v2) at `api.runpod.ai` for running speech generation

This dual-domain approach provides several benefits:

1. **Improved Reliability**: The REST API is more stable and better documented for endpoint management
2. **Better Error Handling**: More consistent error responses and status codes
3. **Optimized Performance**: Using the dedicated inference domain (`api.runpod.ai`) for serverless requests
4. **Future Compatibility**: In line with RunPod's recommended API usage for each operation type

> **IMPORTANT**: Note the domain difference: `.io` for management operations and `.ai` for inference operations

### Example API Usage

**Endpoint Management (using `.io` domain):**
```bash
# Get endpoint details
curl -X GET https://api.runpod.io/v1/endpoints/YOUR_ENDPOINT_ID \
  -H "Authorization: Bearer YOUR_API_KEY"

# Get endpoint metrics
curl -X GET https://api.runpod.io/v1/endpoints/YOUR_ENDPOINT_ID/metrics \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Inference Operations (using `.ai` domain):**
```bash
# Run speech generation
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"input":{"text":"[S1] Hello, world!"}}'

# Check job status
curl -X GET https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/JOB_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Network Volume for Model Caching

This implementation supports using a RunPod network volume to cache model files between runs, which has several benefits:

1. **Faster Startup**: Once the model is downloaded and cached on the network volume, new serverless workers can use the cached model instead of downloading it again.
2. **Reduced API Calls**: Fewer calls to the Hugging Face API, reducing the risk of rate limiting.
3. **Cost Savings**: Less egress bandwidth from Hugging Face, and less intra-datacenter bandwidth for RunPod.

### How to Use Network Volumes

1. Create a RunPod network volume in the same region as your serverless workers.
2. Add the network volume ID to your `.env` file:
   ```
   NETWORK_VOLUME_ID=your_network_volume_id
   ```
3. When you run `./scripts/create_template.sh`, it will automatically configure the volume.
4. The handler code will detect the mounted volume at `/data` and use it for caching models.

### How It Works

The handler.py file includes code to detect and use a network volume mounted at `/data`:

```python
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
```

This ensures that all model downloads and caching happen on the persistent network volume.

## Project Structure

This project is organized into two main components:

### 1. Deployment & Management Component

- **main.py**: Main CLI interface for deployment and management
- **config/**: Configuration modules
  - `api_config.py`: API authentication and endpoint configuration
  - `llm_config.py`: LLM-specific configuration
  - `system_config.py`: System-level configuration
- **deployment/**: Scripts for managing endpoints
  - `create_endpoint.py`: GraphQL API-based endpoint creation
  - `create_endpoint_rest.py`: REST API-based endpoint creation
  - `create_template.py`: Template creation automation
  - `delete_endpoint.py`: Script to clean up resources
  - `update_endpoint.py`: Script to update endpoint config
- **serverless/**: RunPod handler implementation
  - `handler.py`: Main serverless handler
  - `Dockerfile`: Docker configuration for serverless endpoint
  - `requirements.txt`: Python dependencies for container
  - `build_with_token.sh`: Script to build and push Docker image with secure token handling
  - `build_and_push.sh`: Legacy build script (not recommended)
- **scripts/**: Helper scripts
  - `setup_venv.sh`: Script for environment setup
  - `update_requirements.sh`: Script for updating dependencies
  - `create_template.sh`: Script for creating RunPod template
  - `deploy.sh`: One-command deployment
  - `monitor.sh`: Simple monitoring script
  - `README.md`: Documentation for script usage and options
- **USAGE.md**: Detailed usage examples for both CLIs

### 2. Inference Component (Standalone Package)

- **inference/**: Standalone inference package
  - `inference.py`: Main CLI for text-to-speech generation
  - `__init__.py`: Package initialization with exported classes
  - `setup.py`: Package installation script
  - `README.md`: Inference-specific documentation
  - `requirements.txt`: Dependencies just for inference
  - **client/**: Client libraries
    - `inference.py`: Regular inference client
    - `streaming.py`: Streaming client
  - **config/**: Configuration modules for inference
    - `api_config.py`: API keys and endpoint settings
  - **examples/**: Example usage scripts
    - `basic_usage.py`: Basic TTS generation
    - `voice_cloning.py`: Voice cloning demonstration
    - `streaming.py`: Streaming audio example
  
> **Note**: The inference functionality has been moved to the `/inference` directory as a standalone package. 
> The original `inference.py` file and `client/` directory in the project root are now deprecated and kept
> only for backward compatibility.

## CLI Commands

The project now provides two separate command-line interfaces:

### 1. Deployment & Management CLI (main.py)

The `main.py` script is focused on deploying and managing RunPod serverless endpoints:

```bash
# Setup environment
python main.py setup

# Deploy endpoint
python main.py deploy --template-id your_template_id

# Deploy with advanced options
python main.py deploy --template-id your_template_id --name "Custom Name" --min-workers 1 --max-workers 5 --flash-boot

# Check endpoint status
python main.py status

# Delete endpoint
python main.py delete

# Delete without confirmation prompt
python main.py delete --force

# Delete template
python main.py delete-template

# Delete template with specific ID
python main.py delete-template --template-id your_template_id --force
```

### 2. Inference CLI (inference package)

The `inference` package provides a simplified interface focused solely on text-to-speech generation:

```bash
# Generate speech (basic)
python inference/inference.py "Your text to convert to speech"

# Generate speech with parameters
python inference/inference.py "Custom voice sample" --temperature 1.2 --top-p 0.9 --output my_audio.wav

# Stream audio output
python inference/inference.py "Stream this text" --stream

# Use voice cloning with reference audio
python inference/inference.py "Clone this voice" --audio-prompt reference.wav

# Check endpoint status
python inference/inference.py --status

# If you've installed the package (pip install -e ./inference)
dia-tts "Your text to convert to speech"
```

Both CLIs use the same environment variables and configuration settings.

## Voice Cloning

To clone a voice, provide a reference audio file with the `--audio-prompt` parameter:

```bash
python main.py generate "[S1] This is my cloned voice speaking." --audio-prompt reference.wav --output cloned.wav
```

The reference audio should be 5-10 seconds long for best results.

## Speaker Tags and Non-Verbal Sounds

Use speaker tags to denote different speakers:

```
[S1] This is the first speaker. [S2] This is the second speaker.
[S1] I can speak in a natural way (laughs) with non-verbal sounds.
```

## Performance and Cost Considerations

- **VRAM**: Minimum 10GB for inference with float16, 16GB recommended
- **Processing Speed**: ~40 tokens/second on A4000 GPU (86 tokens ≈ 1 second of audio)
- **Cold Start**: ~10-30 seconds for initial model loading; reduced to ~250ms with FlashBoot
- **Cost**: From ~$0.00016/s to ~$0.00031/s depending on GPU type
- **Network Volume Caching**: Significantly reduces cold start times after initial model download

## Cleanup and Resource Management

When you're done with your deployment, you can clean up both the endpoint and template to avoid ongoing costs:

### Using Python CLI

```bash
# Delete the endpoint
python main.py delete

# Delete without confirmation prompt
python main.py delete --force

# Delete the template
python main.py delete-template

# Delete template with specific ID
python main.py delete-template --template-id your_template_id --force
```

### Using Shell Scripts

```bash
# Delete endpoint
./scripts/delete_endpoint.sh

# Delete with force flag
./scripts/delete_endpoint.sh --force

# Delete template 
./scripts/delete_template.sh

# Delete template with specific ID
./scripts/delete_template.sh --template-id your_template_id --force
```

## Troubleshooting

### Common Issues

#### "Failed to find C compiler" Error
If you encounter this error: `RuntimeError: Failed to find C compiler. Please specify via CC environment variable.`

**Solution**: The error occurs when PyTorch attempts to use its dynamic compilation features (torch.dynamo or torch.compile). 

This has been fixed in the current version by:
1. Setting `torch._dynamo.config.suppress_errors = True` at the top of handler.py
2. Setting environment variables `TORCH_COMPILE_DISABLE=1` and `PYTORCH_JIT=0`
3. Setting `use_torch_compile=False` in the model generation call
4. Adding a fallback mechanism that catches any remaining compilation errors

These measures ensure compatibility with RunPod's serverless environment, which does not include a C compiler by default. While disabling compilation may result in slightly slower inference, it significantly improves reliability in serverless environments.

**If you're still encountering this error**: You need to rebuild your Docker image with the updated handler.py file to apply these fixes.

#### Cold Start Timeouts
If your requests time out during cold starts:

**Solution**: Enable FlashBoot in your endpoint configuration or increase the execution timeout.

#### Memory Errors
If you see CUDA out of memory errors:

**Solution**: Choose a GPU with more VRAM (16GB+ recommended) or consider reducing batch sizes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [nari-labs/Dia](https://github.com/nari-labs/dia) - The text-to-speech model used in this project
- [RunPod](https://www.runpod.io/) - For the serverless GPU infrastructure