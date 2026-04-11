from mosaicolabs import Message
from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter
from mosaicolabs.packs.manipulation.ontology.terminate_episode import (
    TerminateEpisode,
)


class FractalRT1TerminateEpisodeAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.terminate_episode"
    ontology_type = TerminateEpisode

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=TerminateEpisode(
                terminate_episode=[int(value) for value in payload["value"]]
            ),
        )
