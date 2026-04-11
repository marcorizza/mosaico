import functools
from pathlib import Path
from typing import Callable, Iterable

from mosaicolabs.packs.manipulation.readers.tfds_reader import TFDSReader

VIRTUAL_SEPARATOR = "@@"
VIRTUAL_SUFFIX = ".episode"
STEP_RATE_HZ = 3.0
STEP_PERIOD_NS = 1_000_000_000 / STEP_RATE_HZ


def num_examples(root: Path) -> int:
    with TFDSReader(root) as reader:
        return reader.num_examples


def available_episodes(root: Path) -> list[int]:
    with TFDSReader(root) as reader:
        return reader.available_episodes


@functools.lru_cache(maxsize=8)
def _dataset_feature_paths(root_str: str) -> frozenset[str]:
    with TFDSReader(root_str) as reader:
        return reader.dataset_feature_paths


@functools.lru_cache(maxsize=8)
def average_episode_size_bytes(root_str: str) -> int:
    root = Path(root_str)
    total_size_bytes = sum(
        p.stat().st_size for p in root.glob("*.tfrecord-*")
    )
    return total_size_bytes // max(1, len(available_episodes(root)))


def make_virtual_sequence_path(root: Path, episode_index: int) -> Path:
    return root / f"train{VIRTUAL_SEPARATOR}{episode_index:06d}{VIRTUAL_SUFFIX}"


def parse_virtual_sequence_path(sequence_path: Path) -> tuple[Path, int]:
    if VIRTUAL_SEPARATOR not in sequence_path.name:
        raise ValueError(f"Invalid fractal_rt1 sequence path '{sequence_path}'")
    stem, suffix = sequence_path.name.split(VIRTUAL_SEPARATOR, 1)
    if stem != "train":
        raise ValueError(f"Unsupported split in sequence path '{sequence_path}'")
    return sequence_path.parent, int(suffix.removesuffix(VIRTUAL_SUFFIX))


@functools.lru_cache(maxsize=16)
def _load_episode(sequence_path_str: str) -> dict:
    root, episode_index = parse_virtual_sequence_path(Path(sequence_path_str))
    with TFDSReader(root) as reader:
        return reader.load_episode(episode_index)


def _steps(sequence_path: Path) -> list[dict]:
    episode = _load_episode(str(sequence_path))
    steps = episode.get("steps", [])
    if isinstance(steps, dict):
        return [
            TFDSReader.index_tree(steps, idx)
            for idx in range(TFDSReader.sequence_length(steps))
        ]
    return list(steps)


def count_steps() -> Callable[[Path], int]:
    return lambda seq_path: len(_steps(seq_path))


def _timestamp_ns(step_index: int) -> int:
    return int(round(step_index * STEP_PERIOD_NS))


def iter_episode_value(
    field_path: str,
    *,
    payload_key: str = "value",
    transform: Callable[[object], object] | None = None,
) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        episode = _load_episode(str(sequence_path))
        value = TFDSReader.get_nested(episode, field_path)
        if transform is not None:
            value = transform(value)
        yield {"timestamp": 0.0, payload_key: value}

    return _fn


def iter_step_value(
    field_path: str,
    *,
    payload_key: str = "value",
    transform: Callable[[object], object] | None = None,
) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        for step_index, step in enumerate(_steps(sequence_path)):
            value = TFDSReader.get_nested(step, field_path)
            if transform is not None:
                value = transform(value)
            yield {"timestamp_ns": _timestamp_ns(step_index), payload_key: value}

    return _fn


def iter_step_image(field_path: str) -> Callable[[Path], Iterable[dict]]:
    return iter_step_value(field_path, payload_key="image")


def iter_step_pose(field_path: str) -> Callable[[Path], Iterable[dict]]:
    return iter_step_value(field_path, payload_key="pose", transform=TFDSReader.as_list)


def iter_step_vector(field_path: str) -> Callable[[Path], Iterable[dict]]:
    return iter_step_value(
        field_path, payload_key="vector", transform=TFDSReader.as_list
    )


def iter_step_values(field_path: str) -> Callable[[Path], Iterable[dict]]:
    return iter_step_value(
        field_path, payload_key="values", transform=TFDSReader.as_list
    )


def iter_step_scalar(field_path: str) -> Callable[[Path], Iterable[dict]]:
    return iter_step_value(
        field_path, payload_key="value", transform=TFDSReader.as_scalar
    )


def iter_step_terminate_episode(field_path: str) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        for step_index, step in enumerate(_steps(sequence_path)):
            value = [
                int(v)
                for v in TFDSReader.as_list(TFDSReader.get_nested(step, field_path))
            ]
            yield {"timestamp_ns": _timestamp_ns(step_index), "value": value}

    return _fn
