import asyncio
import secrets
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .llm import generate
from .queue import InferenceQueue
from .schemas import GenerateRequest, GenerateResponse

inference_queue = InferenceQueue(settings.max_queue_size)
bearer_scheme = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None or not secrets.compare_digest(
        credentials.credentials, settings.adapter_api_key
    ):
        raise HTTPException(401, "Invalid or missing API key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    inference_queue.start()
    yield
    await inference_queue.close()


app = FastAPI(title="Stateless Nepali LLM Adapter", version="0.3.0", lifespan=lifespan)


@app.get("/health")
async def health():
    device = "cpu" if settings.use_cpu else "gpu"
    return {"status": "ok", "model": settings.llm_model, "device": device, "queued": inference_queue.jobs.qsize()}


@app.post(
    "/v1/generate",
    response_model=GenerateResponse,
    dependencies=[Depends(require_api_key)],
)
async def generate_text(body: GenerateRequest):
    async def work() -> str:
        return await generate(
            [message.model_dump() for message in body.messages],
            body.temperature,
            body.top_p,
            body.top_k,
            body.max_tokens,
        )

    try:
        answer, position = await inference_queue.submit(work)
    except asyncio.QueueFull:
        raise HTTPException(429, "LLM inference queue is full") from None
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"LLM server error: {exc}") from exc
    return GenerateResponse(response=answer, queue_position=position)
