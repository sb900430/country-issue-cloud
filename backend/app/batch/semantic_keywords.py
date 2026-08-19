from collections.abc import Mapping, Sequence
from typing import Protocol, cast

import numpy as np
from numpy.typing import NDArray

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_MODEL_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"


class TextEmbeddingModel(Protocol):
    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]: ...


class _SentenceEncoder(Protocol):
    def encode(self, texts: list[str], **kwargs: object) -> object: ...


class SentenceTransformerEmbeddingModel:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        model_revision: str = DEFAULT_MODEL_REVISION,
    ) -> None:
        self.model_name = model_name
        self.model_revision = model_revision
        self._model: _SentenceEncoder | None = None

    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]

            self._model = cast(
                _SentenceEncoder,
                SentenceTransformer(self.model_name, revision=self.model_revision),
            )
        encoded = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return cast(NDArray[np.float32], np.asarray(encoded, dtype=np.float32))


class SemanticCandidateGrouper:
    def __init__(
        self,
        model: TextEmbeddingModel,
        similarity_threshold: float = 0.95,
        minimum_label_length: int = 4,
        maximum_cluster_size: int = 3,
        use_title_cohesion: bool = False,
    ) -> None:
        if not 0.0 < similarity_threshold <= 1.0:
            raise ValueError("semantic similarity threshold must be within (0, 1]")
        if minimum_label_length < 2:
            raise ValueError("semantic label length must be at least two")
        if maximum_cluster_size < 2:
            raise ValueError("semantic cluster size must be at least two")
        self.model = model
        self.similarity_threshold = similarity_threshold
        self.minimum_label_length = minimum_label_length
        self.maximum_cluster_size = maximum_cluster_size
        self.use_title_cohesion = use_title_cohesion

    def group(
        self,
        labels: Mapping[str, str],
        document_frequencies: Mapping[str, int],
    ) -> dict[str, str]:
        assignments = {key: key for key in labels}
        eligible_keys = [
            key
            for key, label in labels.items()
            if len("".join(label.split())) >= self.minimum_label_length
        ]
        ordered_keys = sorted(
            eligible_keys,
            key=lambda key: (
                -document_frequencies[key],
                len(labels[key]),
                labels[key].casefold(),
                key,
            ),
        )
        if not ordered_keys:
            return assignments
        vectors = self.model.encode([labels[key] for key in ordered_keys])
        if vectors.ndim != 2 or vectors.shape[0] != len(ordered_keys):
            raise ValueError("embedding model returned an invalid matrix")
        if not np.isfinite(vectors).all():
            raise ValueError("embedding model returned non-finite values")

        representatives: list[int] = []
        cluster_sizes: dict[str, int] = {}
        for index, key in enumerate(ordered_keys):
            if not representatives:
                representatives.append(index)
                assignments[key] = key
                cluster_sizes[key] = 1
                continue
            similarities = vectors[representatives] @ vectors[index]
            best_offset = int(np.argmax(similarities))
            representative_key = ordered_keys[representatives[best_offset]]
            if (
                float(similarities[best_offset]) >= self.similarity_threshold
                and cluster_sizes[representative_key] < self.maximum_cluster_size
            ):
                assignments[key] = representative_key
                cluster_sizes[representative_key] += 1
            else:
                representatives.append(index)
                assignments[key] = key
                cluster_sizes[key] = 1
        return assignments


def build_local_semantic_grouper() -> SemanticCandidateGrouper:
    return SemanticCandidateGrouper(
        SentenceTransformerEmbeddingModel(), use_title_cohesion=True
    )
