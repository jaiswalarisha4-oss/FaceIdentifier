"""A minimal local blockchain, used automatically when no real testnet
credentials (RPC_URL / PRIVATE_KEY / CONTRACT_ADDRESS) are configured.

Each block links to the previous block's hash and is mined to a small
proof-of-work target, so any edit to historical data is immediately
detectable — the same tamper-evidence property a public chain provides,
without needing real funds, a wallet, or network access. This lets the
whole pipeline be demoed end-to-end offline; swap in `testnet_chain.py`
for a real public-chain anchor with no other code changes.
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class SimulatedChain:
    def __init__(self, storage_path: str = "chain.json", difficulty: int = 3):
        self.storage_path = Path(storage_path)
        self.difficulty = difficulty
        if self.storage_path.exists():
            self.chain: List[Dict[str, Any]] = json.loads(self.storage_path.read_text())
        else:
            self.chain = [self._genesis_block()]
            self._save()

    def _genesis_block(self) -> Dict[str, Any]:
        block = {
            "index": 0,
            "timestamp": time.time(),
            "data": {"type": "genesis"},
            "previous_hash": "0" * 64,
            "nonce": 0,
        }
        return self._mine(block)

    def _block_hash(self, block: Dict[str, Any]) -> str:
        payload = json.dumps(
            {k: v for k, v in block.items() if k != "hash"}, sort_keys=True
        ).encode()
        return hashlib.sha256(payload).hexdigest()

    def _mine(self, block: Dict[str, Any]) -> Dict[str, Any]:
        target = "0" * self.difficulty
        block = dict(block)
        block["nonce"] = 0
        digest = self._block_hash(block)
        while not digest.startswith(target):
            block["nonce"] += 1
            digest = self._block_hash(block)
        block["hash"] = digest
        return block

    def add_block(self, data: Dict[str, Any]) -> Dict[str, Any]:
        previous = self.chain[-1]
        block = {
            "index": previous["index"] + 1,
            "timestamp": time.time(),
            "data": data,
            "previous_hash": previous["hash"],
            "nonce": 0,
        }
        block = self._mine(block)
        self.chain.append(block)
        self._save()
        return block

    def _save(self) -> None:
        self.storage_path.write_text(json.dumps(self.chain, indent=2))

    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current, previous = self.chain[i], self.chain[i - 1]
            if current["previous_hash"] != previous["hash"]:
                return False
            recomputed = self._block_hash(
                {k: v for k, v in current.items() if k != "hash"}
            )
            if recomputed != current["hash"]:
                return False
        return True

    def find_block_by_root(self, merkle_root_hex: str) -> Optional[Dict[str, Any]]:
        for block in self.chain:
            if block["data"].get("merkle_root") == merkle_root_hex:
                return block
        return None
