# Dia-1.6B RunPod Serverless Scripts

This directory contains scripts for managing Dia-1.6B RunPod serverless deployments.

## Script Overview

### create_template.sh
Creates a RunPod template for the Dia-1.6B TTS model.

**Usage:**
```bash
./scripts/create_template.sh [options]
```

**Options:**
- `--name NAME` - Template name (default: "Dia-1.6B-TTS")
- `--image IMAGE` - Docker image name (default: "tuckertucker/dia-1.6b-tts-runpod:latest")
- `--disk-size SIZE` - Container disk size in GB (default: 20)
- `--volume-id ID` - Network volume ID to mount
- `--volume-path PATH` - Path to mount volume in container (default: "/data")
- `--hf-token TOKEN` - Hugging Face token for model downloads

**Example:**
```bash
./scripts/create_template.sh --name "My-Dia-TTS" --hf-token "hf_..."
```

### deploy.sh
Deploys a serverless endpoint using a template.

**Usage:**
```bash
./scripts/deploy.sh [options]
```

**Options:**
- `--name NAME` - Endpoint name (default: "Dia-1.6B-Endpoint")
- `--template-id ID` - Template ID to use
- `--min-workers N` - Minimum active workers
- `--max-workers N` - Maximum active workers
- `--idle-timeout SECONDS` - Worker idle timeout

**Example:**
```bash
./scripts/deploy.sh --template-id "abc123" --min-workers 1
```

### delete_template.sh
Deletes a RunPod template.

**Usage:**
```bash
./scripts/delete_template.sh [options]
```

**Options:**
- `--template-id ID` - Template ID to delete
- `--force` - Force deletion without confirmation

**Example:**
```bash
./scripts/delete_template.sh --template-id "abc123" --force
```

### delete_endpoint.sh
Deletes a RunPod serverless endpoint.

**Usage:**
```bash
./scripts/delete_endpoint.sh [options]
```

**Options:**
- `--endpoint-id ID` - Endpoint ID to delete
- `--force` - Force deletion without confirmation

**Example:**
```bash
./scripts/delete_endpoint.sh --endpoint-id "def456" --force
```

### monitor.sh
Monitors the status of a RunPod serverless endpoint.

**Usage:**
```bash
./scripts/monitor.sh [options]
```

**Options:**
- `--endpoint-id ID` - Endpoint ID to monitor

**Example:**
```bash
./scripts/monitor.sh --endpoint-id "def456"
```

### setup_venv.sh
Sets up a Python virtual environment for local development.

**Usage:**
```bash
./scripts/setup_venv.sh [options]
```

**Options:**
- `--force` - Force setup even if virtual environment already exists

### update_requirements.sh
Updates Python dependencies in the virtual environment.

**Usage:**
```bash
./scripts/update_requirements.sh
```

## Environment Variables

These scripts use the following environment variables from the `.env` file:

- `RUNPOD_API_KEY` - RunPod API key for authentication
- `TEMPLATE_ID` - ID of the template to use for deployment
- `ENDPOINT_ID` - ID of the deployed endpoint
- `NETWORK_VOLUME_ID` - ID of the network volume to mount
- `HUGGINGFACE_TOKEN` - Hugging Face token for model downloads
- `MIN_WORKERS` - Minimum active workers
- `MAX_WORKERS` - Maximum active workers
- `IDLE_TIMEOUT` - Worker idle timeout in seconds
- `FLASH_BOOT` - Enable/disable flash boot (true/false)