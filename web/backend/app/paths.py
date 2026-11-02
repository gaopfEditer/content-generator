from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DUANZI_ROOT = REPO_ROOT / "content-os" / "duanzi"
DIRECTIONS_YAML = DUANZI_ROOT / "config" / "directions.yaml"
MODELS_MD = DUANZI_ROOT / "config" / "models.md"
RUNTIME_CONFIG = DUANZI_ROOT / "config" / "runtime.json"
DAILY_CSV = DUANZI_ROOT / "stats" / "daily.csv"
FINGERPRINTS = DUANZI_ROOT / "stats" / "fingerprints.jsonl"
TEMPLATE_PATH = DUANZI_ROOT / "templates" / "段子成稿.md"

VALID_DIRECTIONS = ("crypto", "invest", "scitech", "engineering")

STATUS_FLOW = (
    "inbox",
    "drafting",
    "self_check",
    "reviewing",
    "ready",
    "published",
    "archived",
    "rejected",
    "draft_failed",
)

NEXT_STATUS = {
    "inbox": "drafting",
    "drafting": "self_check",
    "self_check": "reviewing",
    "reviewing": "ready",
}
