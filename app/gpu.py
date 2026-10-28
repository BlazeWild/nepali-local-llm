import asyncio
import subprocess


class GpuMonitor:
    def __init__(self, interval_seconds: float = 0.5):
        self.interval_seconds = interval_seconds
        self.current_used_mib: int | None = None
        self.peak_used_mib: int | None = None
        self.total_mib: int | None = None
        self.utilization_percent: int | None = None
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def close(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    def snapshot(self) -> dict:
        return {
            "scope": "all_processes_on_gpu",
            "current_used_mib": self.current_used_mib,
            "peak_used_mib": self.peak_used_mib,
            "total_mib": self.total_mib,
            "utilization_percent": self.utilization_percent,
            "sample_interval_seconds": self.interval_seconds,
        }

    async def _run(self) -> None:
        while True:
            await asyncio.to_thread(self._sample)
            await asyncio.sleep(self.interval_seconds)

    def _sample(self) -> None:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.used,memory.total,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            first_gpu = result.stdout.strip().splitlines()[0]
            used, total, utilization = (
                int(value.strip()) for value in first_gpu.split(",")
            )
        except (FileNotFoundError, IndexError, subprocess.SubprocessError, ValueError):
            return

        self.current_used_mib = used
        self.total_mib = total
        self.utilization_percent = utilization
        self.peak_used_mib = max(self.peak_used_mib or 0, used)
