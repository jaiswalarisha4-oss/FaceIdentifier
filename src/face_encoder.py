"""Face detection and 128-d embedding extraction, via the `face_recognition`
library (dlib's ResNet-based face encoder)."""
from pathlib import Path
from typing import Union

import face_recognition
import numpy as np


class NoFaceFoundError(RuntimeError):
    pass


class FaceEncoder:
    def encode(self, image_path: Union[str, Path]) -> np.ndarray:
        image = face_recognition.load_image_file(str(image_path))
        locations = face_recognition.face_locations(image)
        if not locations:
            raise NoFaceFoundError(f"No face detected in {image_path}")
        encodings = face_recognition.face_encodings(image, known_face_locations=locations)
        return encodings[0]

    @staticmethod
    def compare(known_encoding: np.ndarray, candidate_encoding: np.ndarray, tolerance: float = 0.6) -> bool:
        distance = np.linalg.norm(known_encoding - candidate_encoding)
        return bool(distance <= tolerance)
