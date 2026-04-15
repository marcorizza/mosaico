from mosaicolabs import Message, Vector3d, Velocity

from mosaicopacks.manipulation.adapters.base import BaseAdapter


class ReassembleVelocityAdapter(BaseAdapter):
    adapter_id = "reassemble.velocity"
    ontology_type = Velocity

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=Velocity(
                linear=Vector3d(
                    x=payload["velocity"][0],
                    y=payload["velocity"][1],
                    z=payload["velocity"][2],
                ),
                angular=Vector3d(
                    x=payload["velocity"][3],
                    y=payload["velocity"][4],
                    z=payload["velocity"][5],
                ),
            ),
        )
