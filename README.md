# Nepali Local LLM API

Authenticated, stateless FastAPI adapter for Gemma 4 running through llama.cpp.

Default local configuration:

- Model: `google/gemma-4-12B-it-qat-q4_0-gguf:Q4_0`
- Device: NVIDIA GPU (`USE_CPU=false`, `GPU_LAYERS=99`)
- Context: 8192 tokens
- Maximum requested output: 4096 tokens
- llama.cpp: `http://127.0.0.1:8080`
- FastAPI: `http://127.0.0.1:8000`

The measured peak for this model with an 8192-token context was 7851 MiB on
one Kaggle T4. It should fit on a 12 GiB GPU, although free memory depends on
other GPU processes and the installed llama.cpp version.

## Local GPU setup (recommended)

### 1. Install prerequisites

You need Linux, Python 3.10+, Git, `curl`, `openssl`, and a working NVIDIA
driver. These commands must succeed:

```bash
nvidia-smi
python3 --version
```

Install llama.cpp once:

```bash
curl -LsSf https://llama.app/install.sh | sh
source ~/.bashrc
llama --version
```

### 2. Clone and configure

```bash
git clone https://github.com/BlazeWild/nepali-local-llm.git
cd nepali-local-llm
cp .env.example .env
openssl rand -hex 32
```

Copy the generated value into `.env`:

```env
LLM_API_KEY=PASTE_THE_GENERATED_KEY_HERE
```

The checked-in `.env.example` already enables Gemma 4 12B on the GPU:

```env
MODEL_ID=google/gemma-4-12B-it-qat-q4_0-gguf:Q4_0
LLM_MODEL=google/gemma-4-12B-it-qat-q4_0-gguf:Q4_0
USE_CPU=false
GPU_LAYERS=99
CONTEXT_SIZE=8192
DEFAULT_MAX_TOKENS=4096
```

`.env` is ignored by Git. Never commit its API key.

### 3. Start Gemma 4 12B on the GPU

```bash
chmod +x scripts/run_gemma.sh
./scripts/run_gemma.sh
```

The first run downloads the GGUF model. Keep this terminal running. The script
prints the selected GPU and starts llama.cpp with `-ngl 99`.

### 4. Start FastAPI

Open another terminal in the repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5. Test the API

```bash
curl http://127.0.0.1:8000/health
```

Use the same key stored in `.env`:

```bash
export LLM_API_KEY="PASTE_THE_SAME_KEY_HERE"

curl -X POST "http://127.0.0.1:8000/v1/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -d '{
    "messages": [
      {
        "role": "system",
        "content": "तपाईं नेपालीमा स्पष्ट र तथ्यपरक उत्तर दिने सहायक हुनुहुन्छ।"
      },
      {
        "role": "user",
        "content": "नेपालको राजधानीको छोटो परिचय दिनुहोस्।"
      }
    ],
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 64,
    "max_tokens": 1024
  }'
```

## CPU fallback

Gemma 4 12B is intended for the GPU setup above. For a lighter CPU test, use
Gemma 4 E2B:

```bash
cp .env.cpu.example .env
# Set LLM_API_KEY in .env.
./scripts/run_gemma.sh
```

CPU generation is substantially slower. `.env.cpu.example` selects E2B,
disables GPU offload, and reduces context/output limits.

## Architecture

```text
Node/backend -> authenticated FastAPI queue -> llama.cpp -> Gemma 4 12B
```

The adapter is stateless. It stores no users, prompts, conversations, or chat
history. Each request includes the complete `messages` list. The calling
backend owns authentication, persistence, prompts, and conversation history.
FastAPI supplies a bounded global generation queue.

System-prompt examples:

- `prompts/nepali_government_assistant.txt`
- `prompts/nepali_legal_drafting_assistant.txt`

FastAPI does not inject a prompt automatically. The caller sends the relevant
system message with every request.

## API

- `GET /health` — model status and current/peak NVIDIA GPU memory
- `POST /v1/generate` — authenticated generation endpoint

Generation requires:

```http
Authorization: Bearer <LLM_API_KEY>
```

The maximum accepted `max_tokens` is 4096. The system prompt, chat history,
current input, and generated output must fit within the 8192-token context.

## Tests

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

The optional legal evaluator reads `LLM_API_URL` and `LLM_API_KEY` from `.env`,
tests PDF retrieval/summary, letter generation, and case-data summary, and
writes its generated PDF under the ignored `outputs/` directory:

```bash
python3 examples/legal_workflow_eval.py
```

## Kaggle

Kaggle deployment is separate. See [KAGGLE.md](KAGGLE.md). The local GPU setup
above does not require Kaggle or ngrok.
