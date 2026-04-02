from typing import Any, Optional

from mosaicolabs.packs.manipulation.ontology import AudioInfo
from mosaicolabs.packs.manipulation.ontology.audio import AudioFormat
from mosaicolabs.ros_bridge import ROSAdapterBase


class AudioInfoAdapter(ROSAdapterBase[AudioInfo]):
    ros_msgtype = "audio_common_msgs/msg/AudioInfo"
    __mosaico_ontology_type__ = AudioInfo
    _REQUIRED_KEYS = (
        "channels",
        "sample_rate",
        "sample_format",
        "bitrate",
        "coding_format",
    )

    @classmethod
    def from_dict(cls, ros_data: dict) -> AudioInfo:
        return AudioInfo(
            channels=int(ros_data["channels"]),
            sample_rate=int(ros_data["sample_rate"]),
            sample_format=str(ros_data["sample_format"]),
            bitrate=(
                None if ros_data.get("bitrate") is None else int(ros_data["bitrate"])
            ),
            coding_format=AudioFormat(str(ros_data["coding_format"]).lower()),
        )

    @classmethod
    def schema_metadata(cls, ros_data: dict, **kwargs: Any) -> Optional[dict]:
        return None
