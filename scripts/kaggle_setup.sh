#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="${KAGGLE_WORKING_DIR:-/kaggle/working}"
LLAMA_DIR="${WORK_DIR}/llama.cpp"

if [[ ! -d "${LLAMA_DIR}/.git" ]]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "${LLAMA_DIR}"
fi

cmake -S "${LLAMA_DIR}" -B "${LLAMA_DIR}/build" \
  -DGGML_CUDA=ON \
  -DLLAMA_CURL=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${LLAMA_DIR}/build" --config Release -j 2 --target llama-server

python -m pip install -r requirements.txt
python -m pip install pyngrok

echo "Kaggle dependencies are ready. Run: python scripts/kaggle_start.py"
