from pathlib import Path

import h5py
import numpy as np

from packs.manipulation.utils.extract_video_frame import extract_video_frames


class HDF5Reader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._handle = None

    def __enter__(self):
        self._handle = h5py.File(self.file_path, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        return None

    def iter_records(self, timestamps_path: str, fields: dict[str, str]):
        if self._handle is None:
            raise RuntimeError("HDF5Reader is not open")

        timestamps = self._handle[timestamps_path][:]
        fields_value = {
            fields_name: self._handle[fields_path][:]
            for fields_name, fields_path in fields.items()
        }

        for i, ts in enumerate(timestamps):
            payload = {"timestamp": ts}
            for field_name, field_value in fields_value.items():
                payload[field_name] = field_value[i]
            yield payload

    def iter_video_frames(self, video_path: str, timestamps_path: str):
        if self._handle is None:
            raise RuntimeError("HDF5Reader is not open")

        timestamps = self._handle[timestamps_path][:]
        yield from extract_video_frames(self._handle, video_path, timestamps)

    def iter_event_frames(
        self,
        events_path: str,
        timestamps_path: str,
        window_seconds: float = 0.033
    ):
        if self._handle is None:
            raise RuntimeError("HDF5Reader is not open")

        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

        timestamps_seconds = self._handle[timestamps_path][:]
        if len(timestamps_seconds) == 0:
            return

        timestamps_ns = np.rint(timestamps_seconds * 1e9).astype(np.int64)
        window_ns = int(round(window_seconds * 1e9))
        events_dataset = self._handle[events_path]

        first_ts = int(timestamps_ns[0])
        last_ts = int(timestamps_ns[-1])
        num_windows = int(np.ceil((last_ts - first_ts + 1) / window_ns))
        boundaries_ns = first_ts + np.arange(num_windows + 1, dtype=np.int64) * window_ns

        split_indices = np.searchsorted(timestamps_ns, boundaries_ns, side="left")

        for i in range(num_windows):
            start_idx = int(split_indices[i])
            end_idx = int(split_indices[i + 1])
            w_start = int(boundaries_ns[i])
            w_end = int(boundaries_ns[i + 1])

            event_timestamps_ns = timestamps_ns[start_idx:end_idx]

            yield {
                "timestamp_ns": int(event_timestamps_ns[-1]) if end_idx > start_idx else w_end,
                "t_start_ns": w_start,
                "t_end_ns": w_end,
                "events": events_dataset[start_idx:end_idx],
                "event_timestamps_ns": event_timestamps_ns,
            }

    def get_audio(self, audio_path: str, timestamps_path: str):
        if self._handle is None:
            raise RuntimeError("HDF5Reader is not open")

        ts_start = self._handle[timestamps_path][0]
        ts_end = self._handle[timestamps_path][-1]
        ts_duration = ts_end - ts_start
        audio_data = self._handle[audio_path][:]

        yield {
            "ts_start": ts_start,
            "ts_duration": ts_duration,
            "audio": audio_data,
        }
