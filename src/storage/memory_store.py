import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
DRAFT_LOG = DATA_DIR / "draft_logs.json"

DATA_DIR.mkdir(exist_ok=True)

def log_draft(draft: str, stage: str):
    if not DRAFT_LOG.exists():
        DRAFT_LOG.write_text(json.dumps({"logs": []}, indent=2))

    data = json.loads(DRAFT_LOG.read_text())
    data["logs"].append({
        "stage": stage,
        "draft": draft,
        "timestamp": datetime.utcnow().isoformat()
    })

    DRAFT_LOG.write_text(json.dumps(data, indent=2))
