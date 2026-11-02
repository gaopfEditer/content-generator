"""File-backed store for duanzi pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import yaml

from .draft_io import (
    count_chinese_chars,
    get_section,
    parse_draft,
    replace_section,
    set_meta_field,
)
from .paths import (
    DAILY_CSV,
    DIRECTIONS_YAML,
    DUANZI_ROOT,
    FINGERPRINTS,
    NEXT_STATUS,
    RUNTIME_CONFIG,
    TEMPLATE_PATH,
    VALID_DIRECTIONS,
)


def load_directions_config() -> dict[str, Any]:
    with DIRECTIONS_YAML.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def direction_path(direction: str) -> Path:
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"未知方向: {direction}")
    cfg = load_directions_config()
    rel = cfg.get("directions", {}).get(direction, {}).get("path", f"directions/{direction}")
    return DUANZI_ROOT / rel


def ensure_direction_dirs(direction: str) -> None:
    base = direction_path(direction)
    (base / "inbox").mkdir(parents=True, exist_ok=True)
    (base / "drafts").mkdir(parents=True, exist_ok=True)


def list_drafts(direction: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    dirs = [direction] if direction else list(VALID_DIRECTIONS)
    for d in dirs:
        ensure_direction_dirs(d)
        drafts_dir = direction_path(d) / "drafts"
        for p in sorted(drafts_dir.glob("*.md")):
            text = p.read_text(encoding="utf-8")
            meta, _ = parse_draft(text)
            items.append(
                {
                    "id": meta.get("id") or p.stem,
                    "filename": p.name,
                    "direction": meta.get("direction") or d,
                    "title": meta.get("title") or p.stem,
                    "status": meta.get("status") or "drafting",
                    "topic_tags": meta.get("topic_tags") or [],
                    "path": str(p.relative_to(DUANZI_ROOT)),
                }
            )
    return sorted(items, key=lambda x: (x["direction"], x["id"]))


def read_draft(direction: str, draft_id: str) -> dict[str, Any]:
    p = _find_draft_file(direction, draft_id)
    text = p.read_text(encoding="utf-8")
    meta, _ = parse_draft(text)
    return {
        "meta": meta,
        "content": text,
        "path": str(p.relative_to(DUANZI_ROOT)),
        "sections": {
            "structure": get_section(text, "结构槽位"),
            "body": get_section(text, "正文"),
            "self_check": get_section(text, "机械自检摘要"),
        },
    }


def _find_draft_file(direction: str, draft_id: str) -> Path:
    drafts_dir = direction_path(direction) / "drafts"
    for p in drafts_dir.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        meta, _ = parse_draft(text)
        if meta.get("id") == draft_id or p.stem == draft_id:
            return p
    raise FileNotFoundError(draft_id)


def write_draft(direction: str, draft_id: str, content: str) -> dict[str, Any]:
    p = _find_draft_file(direction, draft_id)
    p.write_text(content, encoding="utf-8")
    return read_draft(direction, draft_id)


def transition_draft(direction: str, draft_id: str, action: str) -> dict[str, Any]:
    draft = read_draft(direction, draft_id)
    text = draft["content"]
    meta = draft["meta"]
    status = meta.get("status") or "drafting"

    if action == "advance":
        new_status = NEXT_STATUS.get(status)
        if not new_status:
            raise ValueError(f"状态 {status} 无法前进")
        text = set_meta_field(text, "status", new_status)
    elif action == "reject":
        text = set_meta_field(text, "status", "rejected")
        _bump_stat(direction, rejected_delta=1)
    elif action == "approve":
        if status != "reviewing":
            raise ValueError("仅 reviewing 可批准为 ready")
        text = set_meta_field(text, "status", "ready")
    elif action == "back_to_inbox":
        text = set_meta_field(text, "status", "inbox")
    else:
        raise ValueError(f"未知动作: {action}")

    return write_draft(direction, draft_id, text)


def publish_draft(direction: str, draft_id: str, confirm: bool) -> dict[str, Any]:
    if not confirm:
        raise ValueError("发布须显式 confirm=true；本系统不自动发帖")
    draft = read_draft(direction, draft_id)
    status = draft["meta"].get("status")
    if status != "ready":
        raise ValueError("仅 ready 状态可标记 published（导出发稿包，不代发社交平台）")
    text = set_meta_field(draft["content"], "status", "published")
    result = write_draft(direction, draft_id, text)
    _bump_stat(direction, published_delta=1)
    return result


def load_runtime_config() -> dict[str, Any]:
    default = {
        "model_primary": "cursor_pro",
        "model_fallback": "ollama",
        "cursor_api_base": "",
        "ollama_base_url": "http://127.0.0.1:11434",
        "ollama_model": "qwen2.5:7b",
        "timeout_seconds": 120,
        "retry_once": True,
    }
    if RUNTIME_CONFIG.exists():
        data = json.loads(RUNTIME_CONFIG.read_text(encoding="utf-8"))
        default.update(data)
    return default


def save_runtime_config(data: dict[str, Any]) -> dict[str, Any]:
    forbidden = {"cursor_api_key", "api_key", "secret"}
    clean = {k: v for k, v in data.items() if k.lower() not in forbidden}
    merged = load_runtime_config()
    merged.update(clean)
    RUNTIME_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_CONFIG.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def read_daily_stats() -> list[dict[str, str]]:
    if not DAILY_CSV.exists():
        return []
    with DAILY_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_daily_stats(rows: list[dict[str, str]]) -> None:
    fieldnames = ["date", "direction", "intake", "rejected", "published", "notes"]
    DAILY_CSV.parent.mkdir(parents=True, exist_ok=True)
    with DAILY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def upsert_daily_row(row: dict[str, str]) -> list[dict[str, str]]:
    rows = read_daily_stats()
    key = (row.get("date"), row.get("direction"))
    updated = False
    for i, r in enumerate(rows):
        if (r.get("date"), r.get("direction")) == key:
            rows[i] = {**r, **row}
            updated = True
            break
    if not updated:
        rows.append(row)
    write_daily_stats(rows)
    return rows


def _bump_stat(direction: str, intake_delta: int = 0, rejected_delta: int = 0, published_delta: int = 0) -> None:
    today = date.today().isoformat()
    rows = read_daily_stats()
    found = None
    for r in rows:
        if r.get("date") == today and r.get("direction") == direction:
            found = r
            break
    if not found:
        found = {"date": today, "direction": direction, "intake": "0", "rejected": "0", "published": "0", "notes": ""}
        rows.append(found)

    def add(field: str, delta: int) -> None:
        found[field] = str(int(found.get(field) or 0) + delta)

    add("intake", intake_delta)
    add("rejected", rejected_delta)
    add("published", published_delta)
    write_daily_stats(rows)


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    host = (p.netloc or "").lower()
    if host.startswith("mobile."):
        host = host[7:]
    if host == "twitter.com":
        host = "x.com"
    path = p.path.rstrip("/").lower()
    return urlunparse((p.scheme or "https", host, path, "", "", ""))


def content_fingerprint(text: str) -> str:
    norm = re.sub(r"\s+", "", text.lower())
    norm = re.sub(r"[^\w\u4e00-\u9fff]", "", norm)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def load_fingerprints() -> list[dict[str, Any]]:
    if not FINGERPRINTS.exists() or FINGERPRINTS.stat().st_size == 0:
        return []
    lines = FINGERPRINTS.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def append_fingerprint(entry: dict[str, Any]) -> None:
    FINGERPRINTS.parent.mkdir(parents=True, exist_ok=True)
    with FINGERPRINTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def list_inbox(direction: str) -> list[dict[str, Any]]:
    ensure_direction_dirs(direction)
    inbox = direction_path(direction) / "inbox"
    items = []
    for p in sorted(inbox.glob("*.json")):
        items.append(json.loads(p.read_text(encoding="utf-8")))
    return items


def import_inbox_item(direction: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_direction_dirs(direction)
    item_id = payload.get("id") or f"I-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
    norm_url = normalize_url(payload.get("url") or "")
    summary = payload.get("summary") or payload.get("title") or ""
    fp = content_fingerprint(summary)
    existing = {e.get("fp") for e in load_fingerprints()}
    duplicate = fp in existing or any(
        normalize_url(s.get("url", "")) == norm_url
        for e in load_fingerprints()
        for s in e.get("sources", [])
        if norm_url
    )
    item = {
        "id": item_id,
        "direction": direction,
        "title": payload.get("title") or "未命名进料",
        "summary": summary,
        "published_at": payload.get("published_at") or datetime.now().astimezone().isoformat(),
        "sources": payload.get("sources")
        or ([{"platform": payload.get("platform", "manual"), "url": payload.get("url", ""), "published_at": payload.get("published_at")}] if payload.get("url") else []),
        "fingerprint": fp,
        "norm_url": norm_url,
        "domestic_echo": bool(payload.get("domestic_echo", False)),
        "status": "duplicate" if duplicate else "inbox",
    }
    if not duplicate:
        path = direction_path(direction) / "inbox" / f"{item_id}.json"
        path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        append_fingerprint(
            {
                "fp": fp,
                "norm_url": norm_url,
                "canonical_id": f"{direction}/{item_id}",
                "sources": item["sources"],
                "created_at": datetime.now().astimezone().isoformat(),
            }
        )
        _bump_stat(direction, intake_delta=1)
    return item


def simulate_intake(direction: str, count: int = 3) -> list[dict[str, Any]]:
    """Stub fetch: synthesize inbox items (real X/Reddit behind future fetcher interface)."""
    samples = [
        ("热帖梗：远程办公与时区", "Reddit 热帖：经理说 async，会议却排在你凌晨三点。"),
        ("链上群聊反差", "X 热帖：数据驱动群，置顶却是情绪投票。"),
        ("AI 工具日常", "开发者帖：Copilot 写测试，人写注释给 Copilot 看。"),
    ]
    out = []
    for i in range(min(count, len(samples))):
        title, summary = samples[i]
        out.append(
            import_inbox_item(
                direction,
                {
                    "title": title,
                    "summary": summary,
                    "platform": "stub",
                    "url": f"https://example.com/stub/{direction}/{i}",
                },
            )
        )
    return out


def dedup_report(direction: str | None = None) -> list[dict[str, Any]]:
    dirs = [direction] if direction else list(VALID_DIRECTIONS)
    fps = load_fingerprints()
    fp_set = {e.get("fp") for e in fps}
    report = []
    for d in dirs:
        for item in list_inbox(d):
            report.append(
                {
                    **item,
                    "is_duplicate": item.get("status") == "duplicate" or item.get("fingerprint") in fp_set,
                }
            )
    return report


def generate_draft_from_inbox(direction: str, inbox_id: str) -> dict[str, Any]:
    ensure_direction_dirs(direction)
    inbox_path = direction_path(direction) / "inbox" / f"{inbox_id}.json"
    if not inbox_path.exists():
        raise FileNotFoundError(inbox_id)
    item = json.loads(inbox_path.read_text(encoding="utf-8"))
    cfg = load_runtime_config()
    model_used = cfg.get("model_primary", "cursor_pro")
    draft_id = f"D-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
    template = TEMPLATE_PATH.read_text(encoding="utf-8") if TEMPLATE_PATH.exists() else ""
    meta = {
        "id": draft_id,
        "direction": direction,
        "title": item.get("title", "待生成标题"),
        "author": "段子创作",
        "status": "drafting",
        "topic_tags": load_directions_config().get("directions", {}).get(direction, {}).get("tags", [])[:2],
        "source_refs": [inbox_id],
        "字数目标": "180-450",
        "model_used": model_used,
    }
    body = f"""```yaml
{yaml.dump(meta, allow_unicode=True, sort_keys=False).strip()}
```

## 结构槽位

- 场景：{item.get('summary', '')[:40]}…
- 铺垫期待：（待补全）
- 拐点：（待补全）
- 反转：（待补全）
- 余味：（待补全）
- 长度目标: ~300

## 正文

（由 {model_used} 生成占位：请编辑正文，保持铺垫→反转→余味，禁止买卖建议。）

进料摘要：{item.get('summary', '')}

## 机械自检摘要

- 字数：待检
- 清单结果：未检

## 本人品鉴区（留空）

- 深度：
- 是否可发：
"""
    out_path = direction_path(direction) / "drafts" / f"{draft_id}.md"
    out_path.write_text(body, encoding="utf-8")
    item["status"] = "drafted"
    inbox_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return read_draft(direction, draft_id)


def mechanical_self_check(direction: str, draft_id: str) -> dict[str, Any]:
    draft = read_draft(direction, draft_id)
    text = draft["content"]
    body = draft["sections"]["body"]
    structure = draft["sections"]["structure"]
    chars = count_chinese_chars(body)
    required = ["场景", "铺垫期待", "拐点", "反转", "余味", "长度目标"]
    missing = [k for k in required if k not in structure or "待补全" in structure]
    hard_fail = chars < 120
    soft_ok = 180 <= chars <= 450 and not missing
    passed = soft_ok and not hard_fail
    summary = (
        f"- 字数：约 {chars}\n"
        f"- 清单结果：{'通过' if passed else '未通过'}"
        + (f"（项：字数/结构槽位）" if not passed else "（待本人品鉴）")
    )
    text = replace_section(text, "机械自检摘要", summary)
    new_status = "reviewing" if passed else "drafting"
    text = set_meta_field(text, "status", new_status)
    if not passed:
        _bump_stat(direction, rejected_delta=1)
    result = write_draft(direction, draft_id, text)
    result["check"] = {"chars": chars, "passed": passed, "missing_structure": missing}
    return result


def export_ready_draft(direction: str, draft_id: str) -> dict[str, str]:
    draft = read_draft(direction, draft_id)
    if draft["meta"].get("status") not in ("ready", "published"):
        raise ValueError("仅 ready/published 可导出")
    export_dir = DUANZI_ROOT / "exports"
    export_dir.mkdir(exist_ok=True)
    name = f"{draft_id}-{direction}.md"
    out = export_dir / name
    out.write_text(draft["content"], encoding="utf-8")
    return {"path": str(out.relative_to(DUANZI_ROOT)), "filename": name}
