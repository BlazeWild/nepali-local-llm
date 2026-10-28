#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f "$repo_dir/.env" ]]; then
  echo "Missing $repo_dir/.env. Run: cp .env.example .env" >&2
  exit 1
fi

set -a
source "$repo_dir/.env"
set +a
: "${MODEL_ID:?MODEL_ID must be set in .env}"

if [[ "${USE_CPU:-false}" == "true" ]]; then
  gpu_layers=0
  echo "Starting $MODEL_ID on CPU"
else
  gpu_layers="${GPU_LAYERS:-99}"
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "GPU mode is enabled, but nvidia-smi was not found." >&2
    echo "Install/enable the NVIDIA driver or set USE_CPU=true." >&2
    exit 1
  fi
  echo "Starting $MODEL_ID with GPU offload (-ngl $gpu_layers)"
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

exec llama serve \
  -hf "$MODEL_ID" \
  --host 127.0.0.1 \
  --port 8080 \
  -ngl "$gpu_layers" \
  -c "${CONTEXT_SIZE:-8192}" \
  --no-webui
