from pathlib import Path
from typing import Callable, Iterable

from mosaicolabs.packs.manipulation.readers import HDF5Reader


def iter_records(
    timestamps_path: str,
    fields: dict[str, str],
) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        with HDF5Reader(sequence_path) as reader:
            yield from reader.iter_records(
                timestamps_path=timestamps_path,
                fields=fields,
            )

    return _fn


def count_records(timestamps_path: str) -> Callable[[Path], int]:
    def _fn(sequence_path: Path) -> int:
        with HDF5Reader(sequence_path) as reader:
            return reader.count_records(timestamps_path)

    return _fn


def iter_video_frames(
    video_path: str,
    timestamps_path: str,
) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        with HDF5Reader(sequence_path) as reader:
            yield from reader.iter_video_frames(
                video_path=video_path,
                timestamps_path=timestamps_path,
            )

    return _fn


def count_video_frames(timestamps_path: str) -> Callable[[Path], int]:
    def _fn(sequence_path: Path) -> int:
        with HDF5Reader(sequence_path) as reader:
            return reader.count_video_frames(timestamps_path)

    return _fn


def iter_event_frames(
    events_path: str,
    timestamps_path: str,
    window_seconds: float = 0.033,
) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        with HDF5Reader(sequence_path) as reader:
            yield from reader.iter_event_frames(
                events_path=events_path,
                timestamps_path=timestamps_path,
                window_seconds=window_seconds,
            )

    return _fn


def count_event_frames(
    timestamps_path: str,
    window_seconds: float = 0.033,
) -> Callable[[Path], int]:
    def _fn(sequence_path: Path) -> int:
        with HDF5Reader(sequence_path) as reader:
            return reader.count_event_frames(timestamps_path, window_seconds)

    return _fn


def iter_audio(
    audio_path: str,
    timestamps_path: str,
) -> Callable[[Path], Iterable[dict]]:
    def _fn(sequence_path: Path) -> Iterable[dict]:
        with HDF5Reader(sequence_path) as reader:
            yield from reader.get_audio(
                audio_path=audio_path,
                timestamps_path=timestamps_path,
            )

    return _fn


def count_audio(audio_path: str, timestamps_path: str) -> Callable[[Path], int]:
    def _fn(sequence_path: Path) -> int:
        with HDF5Reader(sequence_path) as reader:
            return reader.count_audio(
                audio_path=audio_path,
                timestamps_path=timestamps_path,
            )

    return _fn
