"""ReportAgent — generate final markdown/HTML reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import markdown

from app.agents.base import BaseAgent


class ReportAgent(BaseAgent):
    async def generate(self, payload: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, str]:
        self.bind(payload)
        messages = [
            {
                "role": "user",
                "content": (
                    "Generate a comprehensive ELDA bring-up report in Markdown. "
                    "Sections: Summary, Inputs, Hardware Facts, Driver Plan, Patches Applied, "
                    "Build Results, Test Results, Risks, Manual Confirmations, Next Steps.\n"
                    f"Artifacts JSON:\n{json.dumps(artifacts, ensure_ascii=False)[:20000]}"
                ),
            }
        ]
        md = await self.reasoner.chat(messages)
        return {"markdown": md, "generated_at": datetime.now(timezone.utc).isoformat()}


def write_reports(project_root: str, markdown_text: str) -> dict[str, str]:
    root = Path(project_root)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    md_path = reports / "final_report.md"
    html_path = reports / "final_report.html"
    md_path.write_text(markdown_text, encoding="utf-8")
    body = markdown.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "toc", "nl2br"],
    )
    html_path.write_text(_html_document(body, title="ELDA Report"), encoding="utf-8")
    return {"markdown": str(md_path), "html": str(html_path)}


def _html_document(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #1a1a1a; }}
    h1, h2, h3 {{ color: #0d47a1; }}
    pre, code {{ background: #f5f5f5; border-radius: 4px; }}
    pre {{ padding: 1rem; overflow-x: auto; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
    th {{ background: #e3f2fd; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
