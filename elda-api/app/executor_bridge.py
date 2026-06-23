"""Bridge to Local Tool Executor via poll/result API."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import yaml

from app.store import task_store


class ExecutorBridge:
    async def tool_call(
        self,
        task_id: str,
        tool: str,
        args: dict[str, Any],
        wait: bool = True,
        timeout: float = 600.0,
    ) -> dict[str, Any]:
        call = await task_store.enqueue_tool_call(task_id, tool, args)
        if not wait:
            return {"call_id": call.id}

        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            refreshed = await task_store.get_tool_call(call.id)
            if refreshed and refreshed.status in ("done", "failed"):
                if refreshed.status == "failed":
                    raise RuntimeError(refreshed.error or "Tool call failed")
                return refreshed.result
            await asyncio.sleep(0.5)
        raise TimeoutError(f"Tool call {tool} timed out waiting for executor")

    async def write_workspace_files(
        self,
        project_root: str,
        drafts: dict[str, Any],
        subdir: str = "",
    ) -> Path:
        root = Path(project_root)
        ws = root / "workspace" / subdir if subdir else root / "workspace"
        ws.mkdir(parents=True, exist_ok=True)
        mapping = {
            "register_map.json": drafts.get("register_map", {}),
            "init_sequence.yaml": drafts.get("init_sequence", {}),
            "pin_requirements.yaml": drafts.get("pin_requirements", {}),
        }
        for name, data in mapping.items():
            path = ws / name
            if name.endswith(".json"):
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            else:
                path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        return ws
