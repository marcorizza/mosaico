from mosaicolabs import Message
from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter
from mosaicolabs.packs.manipulation.ontology.end_effector import EndEffector


class EndEffectorAdapter(BaseAdapter):
    adapter_id = "reassemble.end_effector"
    ontology_type = "end_effector"

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=EndEffector(
                efforts=payload["gripper_efforts"],
                positions=payload["gripper_positions"],
                velocities=payload["gripper_velocities"],
            ),
        )
