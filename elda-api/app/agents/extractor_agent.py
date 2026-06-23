"""ExtractorAgent — MinerU markdown + Bailian qwen3-max."""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.validation.schemas import validate_extractor_output


class ExtractorAgent(BaseAgent):
    async def extract(self, payload: dict[str, Any], doc_type: str = "peripheral") -> dict[str, Any]:
        self.bind(payload)
        markdown = payload.get("markdown", "")
        if not markdown:
            raise ValueError("No datasheet markdown — run pdf.mineru_extract (PyMuPDF/pdftotext/MinerU) first")

        excerpt = markdown[:150000]
        label = "SoC reference manual" if doc_type == "soc" else "peripheral datasheet"
        messages = [
            {
                "role": "user",
                "content": (
                    f"Extract hardware facts from this {label} markdown. "
                    "ONLY facts present in the text — do NOT invent registers or GPIO.\n\n"
                    "Output JSON keys:\n"
                    "- register_map: {registers:[{name,address,access,default,bits,description,source_page}]}\n"
                    "- init_sequence: {steps:[{action,register,value,delay_ms,description}]}\n"
                    "- pin_requirements: {interface, bus, gpios, power, notes}\n\n"
                    f"--- MARKDOWN ---\n{excerpt}"
                ),
            }
        ]
        raw = await self.bailian_reasoner.chat_json(messages)
        validate_extractor_output(raw)
        raw["register_map"]["_source"] = payload.get("markdown_paths", [])
        raw["register_map"]["_doc_type"] = doc_type
        return {
            "register_map": raw["register_map"],
            "init_sequence": raw["init_sequence"],
            "pin_requirements": raw["pin_requirements"],
        }
