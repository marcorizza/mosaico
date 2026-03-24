from mosaicolabs import Message
from packs.manipulation.adapters.base import BaseAdapter
from packs.manipulation.ontology.audio import AudioData, AudioDataStamped


class AudioAdapter(BaseAdapter):
    adapter_id = "reassemble.audio"
    ontology_type = AudioDataStamped

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["ts_start"] * 1e9),
            data=AudioDataStamped(
                audio_data=AudioData(
                    data=bytes(payload["audio"]),
                ),
            )
        )
