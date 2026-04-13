from enum import Enum
from typing import Optional

from mosaicolabs import MosaicoField, MosaicoType, Serializable


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

    channels: MosaicoType.uint8 = MosaicoField(
        nullable=True,
        description="Number of audio channels in the stream.",
    )
    sample_rate: MosaicoType.uint32 = MosaicoField(
        nullable=True,
        description="Sampling rate of the audio stream in hertz.",
    )
    sample_format: MosaicoType.string = MosaicoField(
        nullable=True,
        description="Sample representation format, for example s16le or float32.",
    )
    bitrate: Optional[MosaicoType.uint32] = MosaicoField(
        default=None,
        description="Encoded bitrate of the audio stream in bits per second when available.",
    )
    coding_format: MosaicoType.string = MosaicoField(
        nullable=True,
        description="Declared coding format of the audio stream.",
    )


class AudioData(Serializable):
    __ontology_tag__ = "audio_data"

    data: MosaicoType.binary = MosaicoField(
        description="Binary payload containing the audio data."
    )


class AudioDataStamped(Serializable):
    __ontology_tag__ = "audio_data_stamped"

    audio_data: AudioData = MosaicoField(
        description="Audio payload for the current message."
    )
    audio_info: Optional[AudioInfo] = MosaicoField(
        default=None,
        description="Optional metadata describing the audio payload.",
    )
