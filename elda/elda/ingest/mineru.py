"""MinerU PDF parsing — optional high-quality backend."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class MinerUError(RuntimeError):
    pass


def parse_pdf_mineru(pdf_path: Path, output_dir: Path) -> dict[str, str | list[str]]:
    """Run MinerU CLI (not available on Ubuntu 16.04 / old glibc)."""
    if not pdf_path.is_file():
        raise MinerUError(f"PDF not found: {pdf_path}")
    if shutil.which("mineru") is None:
        raise MinerUError("MinerU CLI not in PATH")

    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["mineru", "-p", str(pdf_path), "-o", str(output_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise MinerUError(
            f"MinerU failed (code {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
        )

    md_files = sorted(output_dir.rglob("*.md"))
    if not md_files:
        md_files = sorted(output_dir.rglob("*.mmd"))
    if not md_files:
        raise MinerUError(f"MinerU produced no markdown under {output_dir}")

    parts: list[str] = []
    paths: list[str] = []
    for md in md_files:
        text = md.read_text(encoding="utf-8", errors="replace")
        parts.append(f"<!-- file: {md.relative_to(output_dir)} -->\n{text}")
        paths.append(str(md))

    return {
        "markdown": "\n\n".join(parts),
        "markdown_paths": paths,
        "output_dir": str(output_dir),
        "extract_backend": "mineru",
    }
