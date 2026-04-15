from mosaicolabs import Message, Vector2d

from mosaicopacks.manipulation.adapters.base import BaseAdapter


class FractalRT1Vector2dAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.vector2d"
    ontology_type = Vector2d

    @classmethod
    def translate(cls, payload: dict) -> Message:
        vector = payload["vector"]
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=Vector2d(x=vector[0], y=vector[1]),
        )
