"""Parse and write duanzi draft markdown (```yaml block + sections)."""

from __future__ import annotations

import re
from typing import Any

import yaml

YAML_BLOCK = re.compile(r"^```yaml\s*\n(.*?)\n```", re.DOTALL | re.MULTILINE)


def parse_draft(text: str) -> tuple[dict[str, Any], str]:
    m = YAML_BLOCK.search(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, text


def get_section(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    m = re.search(pattern, text, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""


def set_meta_field(text: str, key: str, value: Any) -> str:
    meta, _ = parse_draft(text)
    meta[key] = value
    return replace_yaml_block(text, meta)


def replace_yaml_block(text: str, meta: dict[str, Any]) -> str:
    block = "```yaml\n" + yaml.dump(meta, allow_unicode=True, sort_keys=False).strip() + "\n```"
    if YAML_BLOCK.search(text):
        return YAML_BLOCK.sub(block, text, count=1)
    return block + "\n\n" + text


def replace_section(text: str, heading: str, body: str) -> str:
    new_sec = f"## {heading}\n\n{body.strip()}\n"
    pattern = rf"^## {re.escape(heading)}\s*\n.*?(?=^## |\Z)"
    if re.search(pattern, text, re.DOTALL | re.MULTILINE):
        return re.sub(pattern, new_sec, text, count=1, flags=re.DOTALL | re.MULTILINE)
    return text.rstrip() + "\n\n" + new_sec


def count_chinese_chars(body: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", body))
