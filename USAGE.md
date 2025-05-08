# Dia TTS RunPod Command-Line Interface

This project now provides two separate command-line interfaces:

## 1. Deployment & Management CLI (main.py)

The `main.py` script is focused on deploying and managing RunPod serverless endpoints:

```bash
# Setup environment 
python main.py setup

# Deploy a serverless endpoint
python main.py deploy --template-id <template-id> --name "My Endpoint"

# Check endpoint status
python main.py status

# Delete an endpoint
python main.py delete --endpoint-id <endpoint-id>

# Delete a template
python main.py delete-template --template-id <template-id>
```

## 2. Inference CLI (inference.py)

The `inference.py` script is a simplified interface focused solely on text-to-speech generation:

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

## Environment Variables

Both CLIs use the same environment variables:

- `RUNPOD_API_KEY`: Your RunPod API key
- `ENDPOINT_ID`: Your deployed endpoint ID

These can be set in your environment or in a `.env` file in the project root.