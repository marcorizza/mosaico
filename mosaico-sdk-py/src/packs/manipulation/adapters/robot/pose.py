from mosaicolabs import Message, Point3d, Pose, Quaternion
from packs.manipulation.adapters.base import BaseAdapter


class PoseAdapter(BaseAdapter):
    adapter_id = "reassemble.pose"
    ontology_type = Pose

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=Pose(
                position=Point3d(
                    x=payload["pose"][0],
                    y=payload["pose"][1],
                    z=payload["pose"][2],
                ),
                orientation=Quaternion(
                    x=payload["pose"][3],
                    y=payload["pose"][4],
                    z=payload["pose"][5],
                    w=payload["pose"][6],
                ),
            )
        )
