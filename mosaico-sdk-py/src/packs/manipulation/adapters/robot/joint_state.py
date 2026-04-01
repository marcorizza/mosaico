from mosaicolabs import Message, RobotJoint
from packs.manipulation.adapters.base import BaseAdapter


class JointStateAdapter(BaseAdapter):
    adapter_id = "reassemble.joint_state"
    ontology_type = RobotJoint

    JOINT_NAMES = [f"joint_{i}" for i in range(1, 8)]

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=RobotJoint(
                names=cls.JOINT_NAMES,
                positions=payload["position"],
                velocities=payload["velocity"],
                efforts=payload["effort"],
            ),
        )
