import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root.parent / "nepali-chat-demo/backend/.env")
    system_prompt = (repo_root / "prompts/nepali_government_assistant.txt").read_text(
        encoding="utf-8"
    ).strip()

    api_url = os.getenv(
        "LLM_API_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/") + "/v1/generate"
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        sys.exit("Set LLM_API_KEY before running this script.")

    response = httpx.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "नेपालको राजधानी के हो?"},
            ],
            "max_tokens": 1024,
        },
        timeout=300,
    )

    print("Status:", response.status_code)
    response.raise_for_status()
    print("Answer:", response.json()["response"])


if __name__ == "__main__":
    main()
