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
cp .env.cpu.example .env
# Set ADAPTER_API_KEY in .env to the same secret used by the Node backend.
./scripts/run_gemma_cpu.sh
```

The CPU example uses `google/gemma-4-E2B-it-qat-q4_0-gguf:Q4_0`. Gemma is
the model; llama.cpp is the runtime that loads its GGUF file. `USE_CPU=true`
selects `-ngl 0`. The model download happens automatically on first launch.

In a second terminal, start the adapter:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set `MODEL_ID` and `LLM_MODEL` to the same complete Hugging Face ID in `.env`.
The repository default is `google/gemma-4-E2B-it-qat-q4_0-gguf:Q4_0`. Accept
its Gemma license on Hugging Face before using a read token to download it.
The Kaggle launcher explicitly selects Gemma 4 E2B Q4 and offloads it to GPU;
it does not use `.env` for model selection.

For a manual development launch, first start an OpenAI-compatible model server on port 8080, then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

The API defaults to temperature `1.0`, top-p `0.95`, top-k `64`, and maximum
output `512` tokens. Node may send lower values for short government answers.

Direct E2B llama.cpp CPU command, if you prefer not to use the script:

```bash
llama-server -hf google/gemma-4-E2B-it-qat-q4_0-gguf:Q4_0 --host 127.0.0.1 --port 8080 -ngl 0 -c 4096 --no-webui
```

For a Kaggle GPU deployment with a fixed authenticated ngrok endpoint, follow
[`KAGGLE.md`](KAGGLE.md).

## API

- `POST /v1/generate` — accept a complete prompt and generation controls, return generated text and global queue position
- `GET /health` — adapter configuration status

`POST /v1/generate` requires `Authorization: Bearer <ADAPTER_API_KEY>`.

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
