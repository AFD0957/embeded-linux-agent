"""HTTP client for elda-api."""

from __future__ import annotations

import time
from typing import Any

import httpx
from rich.console import Console

console = Console()


class EldaApiClient:
    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(self._url("/health"))
            r.raise_for_status()
            return r.json()

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(self._url("/v1/projects"), json=payload)
            r.raise_for_status()
            return r.json()

    def submit_task(self, task_type: str, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {"type": task_type, "project_id": project_id, "payload": payload}
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(self._url("/v1/tasks"), json=body)
            r.raise_for_status()
            return r.json()

    def get_task(self, task_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(self._url(f"/v1/tasks/{task_id}"))
            r.raise_for_status()
            return r.json()

    def wait_task(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        timeout: float = 3600.0,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            task = self.get_task(task_id)
            status = task.get("status", "")
            if status in ("done", "failed", "waiting_verify"):
                return task
            console.print(f"[dim]Task {task_id}: {status} — {task.get('message', '')}[/dim]")
            time.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

    def poll_tool_call(self, executor_id: str) -> dict[str, Any] | None:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                self._url("/v1/executor/poll"),
                params={"executor_id": executor_id},
            )
            r.raise_for_status()
            data = r.json()
            return data.get("tool_call")

    def submit_tool_result(
        self,
        executor_id: str,
        call_id: str,
        success: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        body = {
            "executor_id": executor_id,
            "call_id": call_id,
            "success": success,
            "result": result or {},
            "error": error,
        }
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(self._url("/v1/executor/result"), json=body)
            r.raise_for_status()

    def register_executor(self, executor_id: str, project_root: str) -> None:
        body = {"executor_id": executor_id, "project_root": project_root}
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(self._url("/v1/executor/register"), json=body)
            r.raise_for_status()

    def chat(
        self,
        project_id: str,
        message: str,
        history: list[dict[str, str]] | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = {
            "project_id": project_id,
            "message": message,
            "history": history or [],
        }
        if model_config:
            body["model_keys"] = model_config.get("model_keys", {})
            body["project_root"] = model_config.get("project_root", "")
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(self._url("/v1/chat"), json=body)
            r.raise_for_status()
            return r.json()
