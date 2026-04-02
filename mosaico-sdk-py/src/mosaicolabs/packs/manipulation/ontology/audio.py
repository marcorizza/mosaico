from enum import Enum
from typing import Optional

import pyarrow as pa

from mosaicolabs import Serializable


class AudioFormat(str, Enum):
    WAVE = "wave"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    AAC = "aac"
    OPUS = "opus"
    M4A = "m4a"


class AudioInfo(Serializable):
    __ontology_tag__ = "audio_info"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "channels",
                pa.uint8(),
                nullable=False,
            ),
            pa.field(
                "sample_rate",
                pa.uint32(),
                nullable=False,
            ),
            pa.field(
                "sample_format",
                pa.string(),
                nullable=False,
            ),
            pa.field(
                "bitrate",
                pa.uint32(),
                nullable=True,
            ),
            pa.field(
                "coding_format",
                pa.string(),
                nullable=False,
            ),
        ],
    )

    channels: int
    sample_rate: int
    sample_format: str
    bitrate: Optional[int] = None
    coding_format: AudioFormat


class AudioData(Serializable):
    __ontology_tag__ = "audio_data"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "data",
                pa.binary(),
                nullable=False,
            ),
        ],
    )

    data: bytes


class AudioDataStamped(Serializable):
    __ontology_tag__ = "audio_data_stamped"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "audio_data",
                AudioData.__msco_pyarrow_struct__,
                nullable=False,
            ),
            pa.field(
                "audio_info",
                AudioInfo.__msco_pyarrow_struct__,
                nullable=True,
            ),
        ],
    )

    audio_data: AudioData
    audio_info: Optional[AudioInfo] = None
