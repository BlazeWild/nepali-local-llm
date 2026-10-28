"""Start llama.cpp, the authenticated FastAPI adapter, and a fixed ngrok tunnel on Kaggle."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx
from pyngrok import conf, ngrok

MODEL_ID = "google/gemma-4-12B-it-qat-q4_0-gguf:Q4_0"
CONTEXT_SIZE = "8192"
WORK_DIR = Path(os.getenv("KAGGLE_WORKING_DIR", "/kaggle/working"))
LLAMA_SERVER = WORK_DIR / "llama.cpp/build/bin/llama-server"


def kaggle_secret(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret(name)
    except Exception as exc:
        raise RuntimeError(f"Missing Kaggle secret: {name}") from exc


def optional_kaggle_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret(name)
    except Exception:
        return None


def wait_for(url: str, headers: dict[str, str] | None = None, timeout: int = 900) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, headers=headers, timeout=5).status_code < 500:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2)
    raise TimeoutError(f"Service did not become ready: {url}")


def main() -> None:
    if not LLAMA_SERVER.exists():
        raise RuntimeError("Run scripts/kaggle_setup.sh before this script")

    env = os.environ.copy()
    env.update(
        {
            # Match the target deployment: one GPU only, even on Kaggle T4 x2.
            "CUDA_VISIBLE_DEVICES": "0",
            "LLM_API_KEY": kaggle_secret("LLM_API_KEY"),
            "LLAMA_BASE_URL": "http://127.0.0.1:8080/v1",
            "LLAMA_API_KEY": "kaggle-internal-llama-key",
            "LLM_MODEL": MODEL_ID,
            "USE_CPU": "false",
            "REQUEST_TIMEOUT_SECONDS": "300",
            "MAX_QUEUE_SIZE": "10",
        }
    )
    hf_token = optional_kaggle_secret("HF_TOKEN")
    if hf_token:
        env["HF_TOKEN"] = hf_token
    ngrok_token = kaggle_secret("NGROK_AUTHTOKEN")
    ngrok_domain = kaggle_secret("NGROK_DOMAIN").removeprefix("https://").rstrip("/")

    llama_log = (WORK_DIR / "llama-server.log").open("w")
    api_log = (WORK_DIR / "nepali-api.log").open("w")
    processes: list[subprocess.Popen] = []

    try:
        processes.append(
            subprocess.Popen(
                [
                    str(LLAMA_SERVER),
                    "-hf",
                    MODEL_ID,
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8080",
                    "--api-key",
                    env["LLAMA_API_KEY"],
                    "-ngl",
                    "99",
                    "-c",
                    CONTEXT_SIZE,
                    "-np",
                    "1",
                    "--no-webui",
                ],
                env=env,
                stdout=llama_log,
                stderr=subprocess.STDOUT,
            )
        )
        print(
            f"Loading Gemma 4 12B on GPU 0 only with {CONTEXT_SIZE}-token context; "
            "follow /kaggle/working/llama-server.log",
            flush=True,
        )
        wait_for(
            "http://127.0.0.1:8080/v1/models",
            {"Authorization": f"Bearer {env['LLAMA_API_KEY']}"},
        )
        subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader",
            ],
            check=False,
        )

        processes.append(
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                stdout=api_log,
                stderr=subprocess.STDOUT,
            )
        )
        wait_for("http://127.0.0.1:8000/health")

        conf.get_default().auth_token = ngrok_token
        tunnel = ngrok.connect(
            addr=8000,
            proto="http",
            url=f"https://{ngrok_domain}",
        )
        print(f"Authenticated model API: {tunnel.public_url}/v1/generate", flush=True)
        print("Keep this cell running. Interrupt it to stop all services.", flush=True)

        while all(process.poll() is None for process in processes):
            time.sleep(5)
        raise RuntimeError("A service stopped; inspect the logs in /kaggle/working")
    except KeyboardInterrupt:
        print("Stopping Kaggle model services...", flush=True)
    finally:
        ngrok.kill()
        for process in reversed(processes):
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
        for handle in (llama_log, api_log):
            handle.close()


if __name__ == "__main__":
    main()
