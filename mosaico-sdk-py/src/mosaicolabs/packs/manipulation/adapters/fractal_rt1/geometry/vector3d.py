from mosaicolabs import Message, Vector3d
from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter


class FractalRT1Vector3dAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.vector3d"
    ontology_type = Vector3d

    @classmethod
    def translate(cls, payload: dict) -> Message:
        vector = payload["vector"]
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=Vector3d(x=vector[0], y=vector[1], z=vector[2]),
        )
