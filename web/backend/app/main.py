from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import store
from .paths import VALID_DIRECTIONS

app = FastAPI(title="段子产线控制台 API", version="1.0.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InboxImport(BaseModel):
    title: str = ""
    summary: str = ""
    url: str = ""
    platform: str = "manual"
    published_at: str | None = None
    domestic_echo: bool = False


class DraftUpdate(BaseModel):
    content: str


class TransitionBody(BaseModel):
    action: str = Field(description="advance | reject | approve | back_to_inbox")


class PublishBody(BaseModel):
    confirm: bool = False


class DailyRow(BaseModel):
    date: str
    direction: str
    intake: str = "0"
    rejected: str = "0"
    published: str = "0"
    notes: str = ""


class IntakeBody(BaseModel):
    count: int = 3


class GenerateBody(BaseModel):
    inbox_id: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/directions")
def get_directions() -> dict[str, Any]:
    cfg = store.load_directions_config()
    return cfg


@app.patch("/api/directions/{direction}/enabled")
def set_direction_enabled(direction: str, enabled: bool) -> dict[str, Any]:
    if direction not in VALID_DIRECTIONS:
        raise HTTPException(400, "无效方向")
    from .paths import DIRECTIONS_YAML

    import yaml

    path = DIRECTIONS_YAML
    cfg = store.load_directions_config()
    cfg.setdefault("directions", {}).setdefault(direction, {})["enabled"] = enabled
    path.write_text(yaml.dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return cfg


@app.get("/api/config/models")
def get_models_config() -> dict[str, Any]:
    return {
        "priority": [
            {"rank": 1, "id": "cursor_pro", "label": "Cursor Pro API（主力）"},
            {"rank": 2, "id": "ollama", "label": "Ollama 本地（备用）"},
        ],
        "runtime": store.load_runtime_config(),
        "note": "API 密钥请用环境变量 CURSOR_API_KEY，勿写入仓库",
    }


@app.put("/api/config/models")
def put_models_config(body: dict[str, Any]) -> dict[str, Any]:
    return {"runtime": store.save_runtime_config(body)}


@app.get("/api/stats/daily")
def get_daily_stats() -> list[dict[str, str]]:
    return store.read_daily_stats()


@app.put("/api/stats/daily")
def put_daily_stats(rows: list[DailyRow]) -> list[dict[str, str]]:
    store.write_daily_stats([r.model_dump() for r in rows])
    return store.read_daily_stats()


@app.post("/api/stats/daily/row")
def post_daily_row(row: DailyRow) -> list[dict[str, str]]:
    return store.upsert_daily_row(row.model_dump())


@app.get("/api/drafts")
def get_drafts(direction: str | None = None) -> list[dict[str, Any]]:
    try:
        return store.list_drafts(direction)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/drafts/{direction}/{draft_id}")
def get_draft(direction: str, draft_id: str) -> dict[str, Any]:
    try:
        return store.read_draft(direction, draft_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.put("/api/drafts/{direction}/{draft_id}")
def put_draft(direction: str, draft_id: str, body: DraftUpdate) -> dict[str, Any]:
    try:
        return store.write_draft(direction, draft_id, body.content)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/api/drafts/{direction}/{draft_id}/transition")
def transition(direction: str, draft_id: str, body: TransitionBody) -> dict[str, Any]:
    try:
        return store.transition_draft(direction, draft_id, body.action)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/drafts/{direction}/{draft_id}/self-check")
def self_check(direction: str, draft_id: str) -> dict[str, Any]:
    try:
        return store.mechanical_self_check(direction, draft_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.post("/api/drafts/{direction}/{draft_id}/publish")
def publish(direction: str, draft_id: str, body: PublishBody) -> dict[str, Any]:
    try:
        return store.publish_draft(direction, draft_id, body.confirm)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/drafts/{direction}/{draft_id}/export")
def export_draft(direction: str, draft_id: str) -> dict[str, str]:
    try:
        return store.export_ready_draft(direction, draft_id)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/inbox/{direction}")
def get_inbox(direction: str) -> list[dict[str, Any]]:
    try:
        return store.list_inbox(direction)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/inbox/{direction}/import")
def import_inbox(direction: str, body: InboxImport) -> dict[str, Any]:
    try:
        return store.import_inbox_item(direction, body.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/pipeline/{direction}/intake")
def pipeline_intake(direction: str, body: IntakeBody) -> list[dict[str, Any]]:
    try:
        return store.simulate_intake(direction, body.count)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/pipeline/dedup")
def pipeline_dedup(direction: str | None = None) -> list[dict[str, Any]]:
    return store.dedup_report(direction)


@app.post("/api/pipeline/{direction}/generate")
def pipeline_generate(direction: str, body: GenerateBody) -> dict[str, Any]:
    try:
        return store.generate_draft_from_inbox(direction, body.inbox_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
