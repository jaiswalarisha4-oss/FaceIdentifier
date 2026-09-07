#!/usr/bin/env python3
"""Run the full pipeline: face scan -> social media search -> blockchain
anchoring.

Usage:
    python scripts/run_pipeline.py --image path/to/face.jpg
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pipeline import FaceVerificationPipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Path to the input face scan image")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Perceptual-hash similarity threshold for accepting a match (0-1)",
    )
    args = parser.parse_args()

    pipeline = FaceVerificationPipeline()
    result = pipeline.run(args.image, phash_threshold=args.threshold)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
