import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class Job:
    work: Callable[[], Awaitable[str]]
    result: asyncio.Future[str]


class InferenceQueue:
    """One shared worker protects a local model from competing generations."""

    def __init__(self, max_size: int):
        self.jobs: asyncio.Queue[Job] = asyncio.Queue(maxsize=max_size)
        self.worker: asyncio.Task | None = None

    def start(self) -> None:
        self.worker = asyncio.create_task(self._run())

    async def close(self) -> None:
        if self.worker:
            self.worker.cancel()
            try:
                await self.worker
            except asyncio.CancelledError:
                pass

    async def submit(self, work: Callable[[], Awaitable[str]]) -> tuple[str, int]:
        position = self.jobs.qsize() + 1
        result = asyncio.get_running_loop().create_future()
        self.jobs.put_nowait(Job(work=work, result=result))
        return await result, position

    async def _run(self) -> None:
        while True:
            job = await self.jobs.get()
            try:
                job.result.set_result(await job.work())
            except Exception as error:
                job.result.set_exception(error)
            finally:
                self.jobs.task_done()
