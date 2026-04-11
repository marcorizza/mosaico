from mosaicolabs import Floating32, Message
from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter


class FractalRT1Floating32Adapter(BaseAdapter):
    adapter_id = "fractal_rt1.floating32"
    ontology_type = Floating32

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp_ns"]),
            data=Floating32(data=float(payload["value"])),
        )
