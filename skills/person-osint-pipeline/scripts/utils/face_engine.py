"""Local face verification using InsightFace (buffalo_l) — no external API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_engine: Optional["FaceEngine"] = None


class FaceEngine:
    """Wraps InsightFace for reference embedding and per-image similarity scoring."""

    def __init__(self, model_name: str = "buffalo_l", det_size: tuple[int, int] = (640, 640)):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as e:
            raise ImportError(
                "insightface is required. Run: pip install -r requirements.txt"
            ) from e

        self.app = FaceAnalysis(name=model_name, providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=det_size)
        self._reference_embedding: np.ndarray | None = None

    def load_reference(self, image_path: Path) -> bool:
        """Extract and store normalized embedding from reference photo."""
        faces = self._detect(image_path)
        if not faces:
            logger.error("No face detected in reference image: %s", image_path)
            return False
        emb = faces[0].normed_embedding
        self._reference_embedding = np.asarray(emb, dtype=np.float32)
        logger.info("Reference face loaded from %s", image_path)
        return True

    def score_image(self, image_path: Path) -> tuple[float, int]:
        """
        Return (best_similarity, face_count) for image.
        Similarity is cosine between reference and best-matching face (0..1).
        Returns (-1.0, 0) if no faces or no reference loaded.
        """
        if self._reference_embedding is None:
            raise RuntimeError("Reference embedding not loaded")

        faces = self._detect(image_path)
        if not faces:
            return -1.0, 0

        best = -1.0
        ref = self._reference_embedding
        for face in faces:
            emb = np.asarray(face.normed_embedding, dtype=np.float32)
            sim = float(np.dot(ref, emb))
            best = max(best, sim)
        return best, len(faces)

    def has_face(self, image_path: Path) -> bool:
        return len(self._detect(image_path)) > 0

    def _detect(self, image_path: Path):
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            logger.warning("Could not read image: %s", image_path)
            return []
        return self.app.get(img)


def get_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine
