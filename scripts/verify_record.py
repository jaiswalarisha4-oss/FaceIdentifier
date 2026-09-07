#!/usr/bin/env python3
"""Standalone re-verification of a previously anchored evidence record.

Recomputes the evidence leaf hash from evidence_store.json and confirms it
matches the Merkle root that was anchored on-chain (testnet or simulated).
Anyone with the evidence file and chain access can run this independently
of the original search/upload run -- that independence is the point of
anchoring a hash rather than trusting a database.

Usage:
    python scripts/verify_record.py --evidence-index 0
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pipeline import FaceVerificationPipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-index", type=int, required=True)
    args = parser.parse_args()

    pipeline = FaceVerificationPipeline()
    ok = pipeline.verify(args.evidence_index)
    print("VALID" if ok else "TAMPERED / NOT FOUND")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
