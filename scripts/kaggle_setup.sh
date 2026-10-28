#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="${KAGGLE_WORKING_DIR:-/kaggle/working}"
LLAMA_DIR="${WORK_DIR}/llama.cpp"
CUDA_LINK_DIR="${WORK_DIR}/cuda-driver-lib"

if [[ ! -d "${LLAMA_DIR}/.git" ]]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "${LLAMA_DIR}"
fi

# Kaggle provides the NVIDIA driver as libcuda.so.1 but its CMake environment
# may not provide the unversioned libcuda.so link required by FindCUDAToolkit.
mkdir -p "${CUDA_LINK_DIR}"
CUDA_DRIVER="$(find /usr/lib /usr/local -name 'libcuda.so.1' -print -quit 2>/dev/null || true)"
if [[ -n "${CUDA_DRIVER}" ]]; then
  ln -sfn "${CUDA_DRIVER}" "${CUDA_LINK_DIR}/libcuda.so"
else
  CUDA_DRIVER_STUB="$(find /usr/local/cuda -path '*/stubs/libcuda.so' -print -quit 2>/dev/null || true)"
  if [[ -z "${CUDA_DRIVER_STUB}" ]]; then
    echo "Could not find libcuda.so.1 or a CUDA driver stub" >&2
    exit 1
  fi
  ln -sfn "${CUDA_DRIVER_STUB}" "${CUDA_LINK_DIR}/libcuda.so"
fi

cmake -S "${LLAMA_DIR}" -B "${LLAMA_DIR}/build" \
  -DGGML_CUDA=ON \
  -DCMAKE_LIBRARY_PATH="${CUDA_LINK_DIR}" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${LLAMA_DIR}/build" --config Release -j 2 --target llama-server

python -m pip install -r requirements.txt
python -m pip install pyngrok

echo "Kaggle dependencies are ready. Run: python scripts/kaggle_start.py"
