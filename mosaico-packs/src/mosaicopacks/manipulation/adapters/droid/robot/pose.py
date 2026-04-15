import math

from mosaicolabs import Message, Point3d, Pose, Quaternion

from mosaicopacks.manipulation.adapters.base import BaseAdapter


class DroidPoseAdapter(BaseAdapter):
    adapter_id = "droid.pose"
    ontology_type = Pose

    @classmethod
    def translate(cls, payload: dict) -> Message:
        pose = payload.get("pose", [0.0] * 6)
        if pose is None or len(pose) != 6:
            pose = [0.0] * 6

        x, y, z, rx, ry, rz = pose
        if rx == 0 and ry == 0 and rz == 0:
            quat = [0.0, 0.0, 0.0, 1.0]
        else:
            cr = math.cos(rx * 0.5)
            sr = math.sin(rx * 0.5)
            cp = math.cos(ry * 0.5)
            sp = math.sin(ry * 0.5)
            cy = math.cos(rz * 0.5)
            sy = math.sin(rz * 0.5)

            qw = cr * cp * cy - sr * sp * sy
            qx = sr * cp * cy + cr * sp * sy
            qy = cr * sp * cy - sr * cp * sy
            qz = cr * cp * sy + sr * sp * cy
            quat = [qx, qy, qz, qw]

        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=Pose(
                position=Point3d(x=x, y=y, z=z),
                orientation=Quaternion(x=quat[0], y=quat[1], z=quat[2], w=quat[3]),
            ),
        )
