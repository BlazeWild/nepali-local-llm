# Kaggle Gemma API

Create a GPU notebook with Internet enabled. Accept the Gemma license for
`google/gemma-3-12b-it-qat-q4_0-gguf` using the same Hugging Face account as the
token.

Add these Kaggle secrets and enable notebook access for each one:

- `HF_TOKEN`: Hugging Face read token
- `NGROK_AUTHTOKEN`: ngrok account token
- `NGROK_DOMAIN`: assigned static domain without a path, for example `name.ngrok-free.app`
- `MODEL_API_KEY`: a random API secret used by the Node backend

Run these cells:

```bash
!git clone https://github.com/BlazeWild/nepali-local-llm.git
%cd /kaggle/working/nepali-local-llm
!bash scripts/kaggle_setup.sh
```

Then keep this cell running:

```bash
!python scripts/kaggle_start.py
```

Gemma 3 12B QAT Q4 is the default model; no model setting is required in the
notebook.

Point the local Node backend at the printed address:

```dotenv
LLM_API_URL=https://name.ngrok-free.app
LLM_API_KEY=the-same-value-as-MODEL_API_KEY
```

The endpoint is `POST /v1/generate`. The tunnel and inference server stop when
the Kaggle session stops; the assigned ngrok domain can be reused next session.
