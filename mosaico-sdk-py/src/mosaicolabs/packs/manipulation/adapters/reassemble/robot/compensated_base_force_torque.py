from mosaicolabs import ForceTorque, Message, Vector3d
from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter


class ReassembleCompensatedBaseForceTorqueAdapter(BaseAdapter):
    adapter_id = "reassemble.compensated_base_force_torque"
    ontology_type = ForceTorque

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=ForceTorque(
                force=Vector3d(
                    x=payload["compensated_base_force"][0],
                    y=payload["compensated_base_force"][1],
                    z=payload["compensated_base_force"][2],
                ),
                torque=Vector3d(
                    x=payload["compensated_base_torque"][0],
                    y=payload["compensated_base_torque"][1],
                    z=payload["compensated_base_torque"][2],
                ),
            ),
        )
