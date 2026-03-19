from mosaicolabs import (
    Pose,
    Velocity,
    ForceTorque,
    Point3d,
    Quaternion,
    Vector3d,
    CompressedImage,
    ImageFormat,
)
from mosaicolabs.models import Message
from mosaicolabs.models.sensors import RobotJoint

from configs import ROBOT_JOINT_NAMES
from extract_event_image import extract_event_image


def custom_translator(schema_name: str, payload: dict) -> Message | None:
    if schema_name in {"capture_node-camera-image", "hama1", "hama2", "hand"}:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=CompressedImage(
                data=payload["image"],
                format=ImageFormat.JPEG,
            )
        )

    if schema_name == "events":
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=extract_event_image(payload["event"]),
        )

    if schema_name == "robot_state/joint_state":
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=RobotJoint(
                names=ROBOT_JOINT_NAMES,
                positions=payload["position"],
                velocities=payload["velocity"],
                efforts=payload["effort"],
            )
        )

    if schema_name == "robot_state/pose":
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=Pose(
                position=Point3d(
                    x=payload["pose"][0],
                    y=payload["pose"][1],
                    z=payload["pose"][2]
                ),
                orientation=Quaternion(
                    x=payload["pose"][3],
                    y=payload["pose"][4],
                    z=payload["pose"][5],
                    w=payload["pose"][6]
                )
            )
        )

    if schema_name == "robot_state/velocity":
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=Velocity(
                linear=Vector3d(
                    x=payload["velocity"][0],
                    y=payload["velocity"][1],
                    z=payload["velocity"][2]
                ),
                angular=Vector3d(
                    x=payload["velocity"][3],
                    y=payload["velocity"][4],
                    z=payload["velocity"][5]
                )
            )
        )

    if schema_name == "robot_state/compensated_base_force_torque":
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=ForceTorque(
                force=Vector3d(
                    x=payload["compensated_base_force"][0],
                    y=payload["compensated_base_force"][1],
                    z=payload["compensated_base_force"][2]
                ),
                torque=Vector3d(
                    x=payload["compensated_base_torque"][0],
                    y=payload["compensated_base_torque"][1],
                    z=payload["compensated_base_torque"][2]
                )
            )
        )

    if schema_name == "robot_state/measured_force_torque":
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

    return None
