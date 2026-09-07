"""Perceptual-hash utilities used to confirm that a page a search engine
returned actually shows a visually similar image to the query face crop —
not just any page mentioning it. This is what keeps the "matching social
media post" genuine rather than "first search result"."""
from pathlib import Path
from typing import Union

import imagehash
from PIL import Image


def compute_phash(image_path: Union[str, "Path"]) -> imagehash.ImageHash:
    with Image.open(image_path) as img:
        return imagehash.phash(img)


def hamming_similarity(hash_a: imagehash.ImageHash, hash_b: imagehash.ImageHash) -> float:
    """Similarity in [0, 1]; 1.0 means identical perceptual hash."""
    distance = hash_a - hash_b
    max_bits = len(hash_a.hash) ** 2
    return 1.0 - (distance / max_bits)
