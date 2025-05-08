"""
LLM-specific configuration for Dia-1.6B Text-to-Speech model
"""
import os
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=str(env_path))

# Model configuration
MODEL_ID = os.environ.get('MODEL_ID', 'nari-labs/Dia-1.6B')
COMPUTE_DTYPE = os.environ.get('COMPUTE_DTYPE', 'float16')

# Generation parameters
DEFAULT_TEMPERATURE = float(os.environ.get('DEFAULT_TEMPERATURE', '1.3'))
DEFAULT_TOP_P = float(os.environ.get('DEFAULT_TOP_P', '0.95'))
DEFAULT_SEED = int(os.environ.get('DEFAULT_SEED', '42')) if os.environ.get('DEFAULT_SEED') else None

# Audio parameters
SAMPLE_RATE = 44100

# Speaker tag guide
SPEAKER_TAGS = {
    'S1': 'Speaker 1 (typically main character)',
    'S2': 'Speaker 2 (secondary character)',
    'S3': 'Speaker 3 (if needed)',
    'S4': 'Speaker 4 (if needed)'
}

# Non-verbal sounds supported (partial list)
SUPPORTED_NONVERBALS = [
    '(laughs)',
    '(coughs)',
    '(sighs)',
    '(clears throat)',
    '(gasps)',
    '(sneezes)',
    '(yawns)',
    '(crying)',
    '(whispers)',
    '(chuckles)'
]

# Example prompt with suggested maximum length 
MAX_PROMPT_LENGTH = 2000
EXAMPLE_PROMPT = """
[S1] Welcome to the Dia text-to-speech model. [S2] This is a different speaker.
[S1] I can produce natural sounding dialogue (laughs) with different voices and non-verbal sounds.
[S2] That's right! And you can use reference audio to clone specific voices.
"""

def get_model_parameters(temperature=None, top_p=None, seed=None):
    """Get model parameters with defaults
    
    Args:
        temperature (float, optional): Generation temperature. Defaults to DEFAULT_TEMPERATURE.
        top_p (float, optional): Top-p sampling parameter. Defaults to DEFAULT_TOP_P.
        seed (int, optional): Random seed for reproducible outputs. Defaults to DEFAULT_SEED.
    
    Returns:
        dict: Dictionary of model parameters
    """
    return {
        'temperature': temperature if temperature is not None else DEFAULT_TEMPERATURE,
        'top_p': top_p if top_p is not None else DEFAULT_TOP_P,
        'seed': seed if seed is not None else DEFAULT_SEED
    }

def format_script_with_speakers(lines, default_speaker='S1'):
    """Format a plain text script with speaker tags
    
    Args:
        lines (list): List of dialogue lines
        default_speaker (str, optional): Default speaker tag. Defaults to 'S1'.
    
    Returns:
        str: Formatted script with speaker tags
    """
    formatted_lines = []
    current_speaker = default_speaker
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line already has a speaker tag
        if line.startswith('[S'):
            formatted_lines.append(line)
        else:
            formatted_lines.append(f"[{current_speaker}] {line}")
            
            # Alternate speakers
            current_speaker = 'S2' if current_speaker == 'S1' else 'S1'
    
    return '\n'.join(formatted_lines)