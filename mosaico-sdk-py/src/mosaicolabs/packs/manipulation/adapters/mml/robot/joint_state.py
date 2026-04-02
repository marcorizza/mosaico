from mosaicolabs import Message, RobotJoint
from mosaicolabs.packs.manipulation import BaseAdapter


class JointStateAdapter(BaseAdapter):
    adapter_id = "mml.joint_state"
    ontology_type = RobotJoint

    @classmethod
    def translate(cls, payload: dict):
        return Message(
            timestamp_ns=payload.get("timestamp_ns", None),
            data=RobotJoint(
                names=payload["name"],
                positions=payload["position"],
                velocities=payload["velocity"],
                efforts=payload["effort"],
            ),
        )
