from mosaicolabs import Message, String

from mosaicopacks.manipulation.adapters.base import BaseAdapter


class FractalRT1StringAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.string"
    ontology_type = String

    @classmethod
    def translate(cls, payload: dict) -> Message:
        value = payload["value"]
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace")
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=String(data=str(value)),
        )
