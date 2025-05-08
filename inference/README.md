# Dia TTS Inference Client

This is a standalone client for the Dia-1.6B Text-to-Speech model deployed on RunPod serverless infrastructure. It provides a simple CLI for generating speech using the Dia model without the deployment and management functionality of the full project.

## Requirements

- Python 3.8+ (Python 3.10+ recommended)
- RunPod account with API key
- A deployed Dia TTS RunPod serverless endpoint

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables:

Create a `.env` file in the project root with your RunPod API key and endpoint ID:

```
RUNPOD_API_KEY=your_runpod_api_key
ENDPOINT_ID=your_deployed_endpoint_id
```

Alternatively, set these environment variables directly in your shell.

## Usage

### Command Line Interface

The `inference.py` script provides a simple CLI for generating speech:

```bash
# Generate speech (basic)
python inference.py "Your text to convert to speech"

# Generate speech with parameters
python inference.py "Custom voice sample" --temperature 1.2 --top-p 0.9 --output my_audio.wav

# Stream audio output
python inference.py "Stream this text" --stream

# Use voice cloning with reference audio
python inference.py "Clone this voice" --audio-prompt reference.wav

# Check endpoint status
python inference.py --status
```

See `USAGE.md` for more detailed examples.

### Using as a Python Package

You can also use this as a Python package in your own code:

```python
# Import the clients
from inference import DiaTTSClient, DiaStreamingClient

# Basic speech generation
client = DiaTTSClient()
success, result = client.generate_speech(
    text="[S1] Hello, this is generated speech.",
    temperature=1.3,
    save_path="output.wav"
)

# Voice cloning
client = DiaTTSClient()
success, result = client.generate_speech(
    text="[S1] This is my cloned voice.",
    audio_prompt="reference.wav",
    save_path="cloned.wav"
)

# Streaming audio
streaming_client = DiaStreamingClient()
success, result = streaming_client.stream_speech(
    text="[S1] This text will be streamed as it's generated.",
    save_path="streamed.wav"
)
```

For more examples, check the `examples/` directory:
- `basic_usage.py` - Basic speech generation
- `voice_cloning.py` - Voice cloning with reference audio
- `streaming.py` - Streaming audio generation

## Project Structure

- **inference.py**: Main CLI interface for text-to-speech generation
- **client/**: Client libraries for interacting with the endpoint
  - `inference.py`: Client for running inference
  - `streaming.py`: Client for streaming responses
- **config/**: Configuration modules
  - `api_config.py`: API authentication and endpoint configuration
- **examples/**: Example scripts showing how to use the package
  - `basic_usage.py`: Basic speech generation example
  - `voice_cloning.py`: Voice cloning example
  - `streaming.py`: Streaming audio example

## Speaker Tags and Non-Verbal Sounds

Use speaker tags to denote different speakers:

```
[S1] This is the first speaker. [S2] This is the second speaker.
[S1] I can speak in a natural way (laughs) with non-verbal sounds.
```