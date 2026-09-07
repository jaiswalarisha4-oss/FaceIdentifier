"""Local off-chain metadata store for discovered evidence records.

Only a SHA-256 leaf hash (folded into a Merkle root) ever goes on-chain;
the human-readable evidence backing that hash lives here so it can be
re-fetched and re-hashed at verification time. Swap this for IPFS or any
other content-addressed store without changing the pipeline's interface —
`add`/`get`/`all` is all `pipeline.py` relies on.
"""
import json
from pathlib import Path
from typing import Any, Dict, List


class EvidenceStore:
    def __init__(self, path: str = "evidence_store.json"):
        self.path = Path(path)
        if self.path.exists():
            self.records: List[Dict[str, Any]] = json.loads(self.path.read_text())
        else:
            self.records = []

    def add(self, record: Dict[str, Any]) -> int:
        self.records.append(record)
        self._save()
        return len(self.records) - 1

    def get(self, index: int) -> Dict[str, Any]:
        return self.records[index]

    def all(self) -> List[Dict[str, Any]]:
        return self.records

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.records, indent=2))
