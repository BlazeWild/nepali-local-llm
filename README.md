# Nepali Local LLM API

Stateless FastAPI adapter for a local OpenAI-compatible model server. It stores no users, sessions, prompts, or chat history. Node sends the complete message list for each generation.

## Architecture

`Node/MongoDB -> stateless FastAPI global queue -> private llama.cpp Gemma server`

Node owns application state: users, sessions, memory, prompts, and message history. FastAPI owns only a bounded global generation queue, so multiple projects cannot make the one Gemma process generate simultaneously. llama.cpp only generates tokens.

## Run

Install llama.cpp once, then run Gemma locally on CPU:

```bash
curl -LsSf https://llama.app/install.sh | sh
source ~/.bashrc
./scripts/run_gemma_cpu.sh
```

Gemma is the model; llama.cpp is the runtime that loads its GGUF file. `USE_CPU=true` selects `-ngl 0`; set `USE_CPU=false` to use `GPU_LAYERS` (default `99`). `--no-webui` disables llama.cpp's optional page. The model download happens automatically on first launch.

Set `MODEL_ID` and `LLM_MODEL` to the same complete Hugging Face ID in `.env`. The available Q4 options are:

- `google/gemma-4-E2B-it-qat-q4_0-gguf:Q4_0` — default, lightest
- `google/gemma-4-E4B-it-qat-q4_0-gguf:Q4_0` — better quality, more memory
- `google/gemma-4-12B-it-qat-q4_0-gguf:Q4_0` — best of these three, use 12–16 GB VRAM

For a manual development launch, first start an OpenAI-compatible model server on port 8080, then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

The API's defaults follow Google's published Gemma 4 sampling guidance: temperature `1.0`, top-p `0.95`, top-k `64`, and maximum output `512` tokens. Node may send lower values for short government answers. Thinking is deliberately disabled: it increases latency and raw internal reasoning must never be returned to citizens. A safe internal-only thinking workflow requires a separate parser/audit flow, so it is intentionally not enabled in this first deployment.

Direct llama.cpp CPU command, if you prefer not to use the script:

```bash
llama-server -hf google/gemma-4-E2B-it-qat-q4_0-gguf:Q4_0 --host 127.0.0.1 --port 8080 -ngl 0 -c 4096 --no-webui
```

The linked official repository currently lists Apache-2.0 and provides `gemma-4-E2B_q4_0-it.gguf` (3.35 GB). The `-hf` command downloads it automatically.

## API

- `POST /v1/generate` — accept a complete prompt and generation controls, return generated text and global queue position
- `GET /health` — adapter configuration status

`POST /v1/generate` request example:

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful Nepali assistant."},
    {"role": "user", "content": "नमस्ते"}
  ],
  "temperature": 0.3,
  "top_p": 0.95,
  "top_k": 64,
  "max_tokens": 512
}
```

The adapter never writes any of these messages to a database.

Run `pytest -q` for the stateless adapter test.
