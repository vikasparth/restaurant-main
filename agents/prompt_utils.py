from __future__ import annotations

def build_system_prompt(text: str) -> list[dict]:
    return [
        {
            "type": "text",
            "text": text,
            "cache_control": {"type": "ephemeral"},
        }
    ]
