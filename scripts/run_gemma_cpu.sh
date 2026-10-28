#!/usr/bin/env bash
set -euo pipefail

# Gemma is the model. llama.cpp is the local runtime for its GGUF file.
set -a
source "$(dirname "$0")/../.env"
set +a

: "${MODEL_ID:?MODEL_ID must be set in .env}"

if [[ "${USE_CPU,,}" == "true" ]]; then
  layers=0
else
  layers="${GPU_LAYERS:-99}"
fi

exec llama serve \
  -hf "$MODEL_ID" \
  --host 127.0.0.1 \
  --port 8080 \
  -ngl "$layers" \
  -c "${CONTEXT_SIZE:-8192}" \
  --no-webui
