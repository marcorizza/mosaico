from mosaicolabs import Message, Quaternion

from mosaicopacks.manipulation.adapters.base import BaseAdapter


class FractalRT1QuaternionAdapter(BaseAdapter):
    adapter_id = "fractal_rt1.quaternion"
    ontology_type = Quaternion

    @classmethod
    def translate(cls, payload: dict) -> Message:
        vector = payload["vector"]
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=Quaternion(
                w=vector[0],
                x=vector[1],
                y=vector[2],
                z=vector[3],
            ),
        )
