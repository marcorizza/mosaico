from pathlib import Path

import h5py

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
