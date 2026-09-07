"""Binary Merkle tree (SHA-256, duplicate-last-if-odd).

Only the 32-byte root of this tree ever touches the blockchain. Anyone
holding a leaf and its proof can recompute the root locally and check it
against the on-chain value, without needing access to the rest of the
tree's data. That is what makes batched anchoring possible: many pieces of
evidence collapse into one cheap on-chain write while each one stays
independently, individually verifiable.
"""
import hashlib
from typing import List, Tuple

Proof = List[Tuple[bytes, str]]


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _hash_pair(left: bytes, right: bytes) -> bytes:
    return _hash(left + right)


class MerkleTree:
    def __init__(self, leaves: List[bytes]):
        if not leaves:
            raise ValueError("MerkleTree requires at least one leaf")
        self.leaves = list(leaves)
        self.levels: List[List[bytes]] = [self.leaves]
        self._build()

    def _build(self) -> None:
        level = self.levels[0]
        while len(level) > 1:
            if len(level) % 2 == 1:
                level = level + [level[-1]]
            next_level = [
                _hash_pair(level[i], level[i + 1]) for i in range(0, len(level), 2)
            ]
            self.levels.append(next_level)
            level = next_level

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    def get_proof(self, index: int) -> Proof:
        if index < 0 or index >= len(self.leaves):
            raise IndexError("leaf index out of range")
        proof: Proof = []
        idx = index
        for level in self.levels[:-1]:
            pair_level = level if len(level) % 2 == 0 else level + [level[-1]]
            if idx % 2 == 0:
                sibling_idx, position = idx + 1, "R"
            else:
                sibling_idx, position = idx - 1, "L"
            proof.append((pair_level[sibling_idx], position))
            idx //= 2
        return proof

    @staticmethod
    def verify_proof(leaf: bytes, proof: Proof, root: bytes) -> bool:
        current = leaf
        for sibling, position in proof:
            current = (
                _hash_pair(current, sibling)
                if position == "R"
                else _hash_pair(sibling, current)
            )
        return current == root
