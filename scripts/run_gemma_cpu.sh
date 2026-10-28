#!/usr/bin/env bash
set -euo pipefail

echo "scripts/run_gemma_cpu.sh is kept for compatibility; use scripts/run_gemma.sh." >&2
exec "$(dirname "$0")/run_gemma.sh"
