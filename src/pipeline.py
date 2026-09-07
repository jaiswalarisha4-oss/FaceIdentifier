"""End-to-end orchestration: face scan -> genuine social-media search ->
privacy-preserving, Merkle-anchored blockchain verification.

See README.md ("Unique feature" section) for the reasoning behind hashing
the face embedding (instead of storing it) and batching evidence through a
Merkle root instead of writing each record on-chain directly.
"""
import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional

from evidence_store import EvidenceStore
from face_encoder import FaceEncoder
from merkle import MerkleTree
from perceptual_hash import compute_phash, hamming_similarity
from simulated_chain import SimulatedChain
from social_search import BingReverseImageSearch, SocialMatch

try:
    from testnet_chain import TestnetAnchor
except ImportError:
    TestnetAnchor = None  # web3 not installed -> simulated chain only


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FaceVerificationPipeline:
    def __init__(
        self,
        salt: Optional[str] = None,
        evidence_store: Optional[EvidenceStore] = None,
        chain_storage: str = "chain.json",
    ):
        self.encoder = FaceEncoder()
        self.salt = salt or os.environ.get("EMBEDDING_SALT", "face-verify-chain-demo-salt")
        self.evidence_store = evidence_store or EvidenceStore()
        self.simulated_chain = SimulatedChain(storage_path=chain_storage)

    def _salted_embedding_hash(self, embedding) -> str:
        return sha256_hex(self.salt.encode() + embedding.tobytes())

    def run(self, image_path: str, phash_threshold: float = 0.75) -> Dict[str, Any]:
        embedding = self.encoder.encode(image_path)
        query_face_hash = self._salted_embedding_hash(embedding)
        query_phash = compute_phash(image_path)

        candidates = BingReverseImageSearch().search(image_path)
        if not candidates:
            raise RuntimeError("No social media matches found for this face scan.")

        ranked = self._rank_candidates(candidates, query_phash, phash_threshold)
        if not ranked:
            raise RuntimeError(
                f"Found {len(candidates)} candidate page(s) but none passed the "
                f"perceptual-similarity threshold ({phash_threshold})."
            )

        best_match, similarity = ranked[0]
        evidence = {
            "query_face_hash": query_face_hash,
            "matched_platform": best_match.platform,
            "matched_post_url": best_match.host_page_url,
            "matched_image_url": best_match.source_url,
            "similarity_score": similarity,
            "discovered_at": time.time(),
        }
        leaf_hex = sha256_hex(_canonical_json(evidence))
        evidence["leaf_hash"] = leaf_hex

        record_index = self.evidence_store.add(evidence)
        tree = MerkleTree([bytes.fromhex(leaf_hex)])
        proof = tree.get_proof(0)
        root_hex = tree.root.hex()

        anchor_result = self._anchor(root_hex, record_index)

        return {
            "evidence": evidence,
            "evidence_index": record_index,
            "merkle_root": root_hex,
            "merkle_proof": [(h.hex(), pos) for h, pos in proof],
            "anchor": anchor_result,
            "candidates_considered": len(candidates),
        }

    def _rank_candidates(self, candidates: List[SocialMatch], query_phash, threshold: float):
        scored = []
        for candidate in candidates:
            similarity = self._score_candidate(candidate, query_phash)
            if similarity >= threshold:
                scored.append((candidate, similarity))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored

    def _score_candidate(self, candidate: SocialMatch, query_phash) -> float:
        import io

        import imagehash
        import requests
        from PIL import Image

        url = candidate.thumbnail_url or candidate.source_url
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        candidate_hash = imagehash.phash(Image.open(io.BytesIO(response.content)))
        return hamming_similarity(query_phash, candidate_hash)

    def _anchor(self, root_hex: str, record_index: int) -> Dict[str, Any]:
        metadata_uri = f"local://evidence_store.json#{record_index}"
        if TestnetAnchor is not None and TestnetAnchor.is_configured():
            anchor = TestnetAnchor()
            tx_hash = anchor.anchor(bytes.fromhex(root_hex), metadata_uri)
            return {"mode": "testnet", "tx_hash": tx_hash, "metadata_uri": metadata_uri}
        block = self.simulated_chain.add_block(
            {"merkle_root": root_hex, "metadata_uri": metadata_uri}
        )
        return {
            "mode": "simulated",
            "block_index": block["index"],
            "block_hash": block["hash"],
            "metadata_uri": metadata_uri,
        }

    def verify(self, record_index: int) -> bool:
        """Standalone re-verification: recompute the evidence leaf hash from
        the stored record and confirm it matches the Merkle root that was
        anchored on-chain (testnet or simulated)."""
        evidence = self.evidence_store.get(record_index)
        leaf_hex = evidence["leaf_hash"]
        recomputed = sha256_hex(
            _canonical_json({k: v for k, v in evidence.items() if k != "leaf_hash"})
        )
        if recomputed != leaf_hex:
            return False

        root_hex = MerkleTree([bytes.fromhex(leaf_hex)]).root.hex()

        if TestnetAnchor is not None and TestnetAnchor.is_configured():
            _, _, metadata_uri = TestnetAnchor().verify(bytes.fromhex(root_hex))
            return metadata_uri.startswith("local://evidence_store.json")

        block = self.simulated_chain.find_block_by_root(root_hex)
        return block is not None and self.simulated_chain.is_valid()
