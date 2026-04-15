import functools
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


@functools.lru_cache(maxsize=8)
def _get_tfds(root_dir: str):
    """Initializes and caches the TFDS builder for a given directory."""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    try:
        import absl.logging
        import tensorflow as tf
        import tensorflow_datasets as tfds

        tf.get_logger().setLevel("ERROR")
        absl.logging.set_verbosity(absl.logging.ERROR)
        absl.logging.set_stderrthreshold("error")
        builder = tfds.builder_from_directory(builder_dir=root_dir)
        return tfds, builder
    except ImportError as exc:
        raise RuntimeError(
            "TensorFlow & tensorflow_datasets are required for TFDSReader."
        ) from exc


def _resolve_builder_dir(root: Path) -> Path:
    if (root / "dataset_info.json").exists():
        return root
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "dataset_info.json").exists():
            return child
    return root


class TFDSReader:
    """A reader for handling TensorFlow Datasets (TFDS) sequentially."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = _resolve_builder_dir(Path(root_dir))
        self._tfds = None
        self._builder = None

    def __enter__(self):
        self._tfds, self._builder = _get_tfds(str(self.root_dir))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass  # Cached builder stays resident

    @functools.cached_property
    def dataset_info(self) -> dict:
        info_path = self.root_dir / "dataset_info.json"
        return (
            json.loads(info_path.read_text(encoding="utf-8"))
            if info_path.exists()
            else {}
        )

    @functools.cached_property
    def features_info(self) -> dict:
        info_path = self.root_dir / "features.json"
        return (
            json.loads(info_path.read_text(encoding="utf-8"))
            if info_path.exists()
            else {}
        )

    @property
    def dataset_feature_paths(self) -> frozenset[str]:
        def _walk(node: dict, prefix: str = "") -> set[str]:
            paths: set[str] = set()
            if not isinstance(node, dict):
                return paths

            if node.get("pythonClassName", "").endswith("FeaturesDict"):
                features = node.get("featuresDict", {}).get("features", {})
                for name, child in features.items():
                    child_prefix = f"{prefix}.{name}" if prefix else name
                    paths.update(_walk(child, child_prefix))
                return paths

            if node.get("pythonClassName", "").endswith("Dataset"):
                feature = node.get("sequence", {}).get("feature", {})
                return _walk(feature, prefix)

            if prefix:
                paths.add(prefix)
            return paths

        return frozenset(_walk(self.features_info))

    @property
    def num_examples(self) -> int:
        for split in self.dataset_info.get("splits", []):
            if split.get("name") == "train":
                return sum(int(v) for v in split.get("shardLengths", [])) or int(
                    split.get("numExamples", 0)
                )
        raise ValueError(f"Unable to determine train split size for {self.root_dir}")

    @property
    def available_episodes(self) -> list[int]:
        import re

        for split in self.dataset_info.get("splits", []):
            if split.get("name") == "train":
                shard_lengths = split.get("shardLengths", [])
                if not shard_lengths:
                    num_examples = int(split.get("numExamples", 0))
                    return list(range(num_examples))

                present_shards = set()
                for p in self.root_dir.glob("*.tfrecord-*"):
                    match = re.search(r"-(\d{5})-of-\d{5}", p.name)
                    if match:
                        present_shards.add(int(match.group(1)))

                if not present_shards:
                    return list(range(sum(int(v) for v in shard_lengths)))

                available = []
                current_offset = 0
                for shard_idx, length_str in enumerate(shard_lengths):
                    length = int(length_str)
                    if shard_idx in present_shards:
                        available.extend(range(current_offset, current_offset + length))
                    current_offset += length
                return available
        return []

    def load_episode(self, episode_index: int) -> dict:
        """Loads a single episode slice using TFDS as_numpy."""
        if not self._builder:
            raise RuntimeError("TFDSReader is not open. Use with context manager.")
        split = f"train[{episode_index}:{episode_index + 1}]"
        dataset = self._builder.as_dataset(split=split)
        return next(iter(self._tfds.as_numpy(dataset)))

    @staticmethod
    def sequence_length(tree: Any) -> int:
        if isinstance(tree, dict):
            return TFDSReader.sequence_length(next(iter(tree.values()))) if tree else 0
        if isinstance(tree, np.ndarray):
            return int(tree.shape[0]) if tree.ndim > 0 else 0
        return len(tree) if isinstance(tree, (list, tuple)) else 0

    @staticmethod
    def index_tree(tree: Any, index: int) -> Any:
        if isinstance(tree, dict):
            return {k: TFDSReader.index_tree(v, index) for k, v in tree.items()}
        return tree[index] if isinstance(tree, (np.ndarray, list, tuple)) else tree

    @staticmethod
    def get_nested(data: Any, field_path: str) -> Any:
        current = data
        for part in field_path.split("."):
            current = current[part]
        return current

    @staticmethod
    def as_list(value: Any) -> list:
        if isinstance(value, np.ndarray):
            return value.reshape(-1).tolist()
        return list(value) if isinstance(value, (list, tuple)) else [value]

    @staticmethod
    def as_scalar(value: Any) -> Any:
        if isinstance(value, np.ndarray):
            return value.reshape(-1)[0].item() if value.size > 0 else 0
        if isinstance(value, (list, tuple)):
            return value[0] if value else 0
        return getattr(value, "item", lambda: value)()
