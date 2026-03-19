from mosaicolabs import Message, ForceTorque, Vector3d
from packs.manipulation.adapters.base import BaseAdapter


class MeasuredForceAdapter(BaseAdapter):
    adapter_id = "reassemble.measured_force"
    ontology_type = ForceTorque

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=ForceTorque(
                force=Vector3d(
                    x=payload["measured_force"][0],
                    y=payload["measured_force"][1],
                    z=payload["measured_force"][2]
                ),
                torque=Vector3d(
                    x=payload["measured_torque"][0],
                    y=payload["measured_torque"][1],
                    z=payload["measured_torque"][2]
                )
            )
        )
