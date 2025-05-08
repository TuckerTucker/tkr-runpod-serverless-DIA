# Base image with PyTorch and CUDA support
# Note: No platform specification to allow native builds for both amd64 and arm64
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Install system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    wget \
    ffmpeg \
    libsndfile1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR /home/user

# Set up cache directories
ENV HF_HOME=/home/user/hf_cache \
    TRANSFORMERS_CACHE=/home/user/hf_cache \
    TORCH_HOME=/home/user/torch_cache \
    MODEL_ID="nari-labs/Dia-1.6B" \
    COMPUTE_DTYPE="float16" \
    DEFAULT_TEMPERATURE="1.3" \
    DEFAULT_TOP_P="0.95" \
    DEFAULT_SEED="42"
RUN mkdir -p /home/user/hf_cache /home/user/torch_cache

# Copy requirements first for better layer caching
COPY --chown=user requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy handler code
COPY --chown=user handler.py ./

# Start the serverless handler
CMD ["python3", "-u", "handler.py"]