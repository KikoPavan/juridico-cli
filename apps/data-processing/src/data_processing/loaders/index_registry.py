"""
Index registry: tracks which source files have been processed and their outputs.

Persisted as a JSON file at var/artifacts/index_registry.json.
Enables incremental runs (skip already-processed files) and audit trails.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_REGISTRY_PATH = Path("var/artifacts/index_registry.json")


class IndexRegistry:
    def __init__(self, registry_path: str | Path = _DEFAULT_REGISTRY_PATH) -> None:
        self.path = Path(registry_path)
        self._data: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                self._data = json.load(f)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def register(
        self,
        source_id: str,
        collector: str,
        output_path: str,
        status: str = "ok",
    ) -> None:
        """Record that source_id was processed by collector and saved to output_path."""
        self._data[source_id] = {
            "collector": collector,
            "output_path": str(output_path),
            "status": status,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def is_registered(self, source_id: str) -> bool:
        return source_id in self._data

    def get(self, source_id: str) -> Optional[dict]:
        return self._data.get(source_id)

    def all_entries(self) -> Dict[str, dict]:
        return dict(self._data)
