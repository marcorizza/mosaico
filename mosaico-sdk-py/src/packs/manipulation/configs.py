from mosaicolabs import RobotJoint, Pose, Velocity, ForceTorque, Image, CompressedImage

SEQUENCE_METADATA = {"dataset": "REASSEMBLE"}

ROBOT_JOINT_NAMES = [f"joint_{i}" for i in range(1, 8)]

EVENT_CAMERA_WIDTH = 346
EVENT_CAMERA_HEIGHT = 260
EVENT_IMAGE_ENCODING = "mono8"

ROBOT_TOPICS_DATA = {
    "capture_node-camera-image": {
        "ontology": CompressedImage,
        "metadata": {
            "sensor_model": "iniVation DAVIS346",
            "sensor_type": "event_camera",
            "resolution": [EVENT_CAMERA_WIDTH, EVENT_CAMERA_HEIGHT],
            "frame_sensor": "APS grayscale",
            "datasheet": "https://inivation.com/wp-content/uploads/2019/08/DAVIS346.pdf",
        },
        "timestamps": "timestamps/capture_node-camera-image",
        "fields": {"video": "capture_node-camera-image"},
        "source_type": "video"
    },
    "hama1": {
        "ontology": CompressedImage,
        "metadata": {},
        "timestamps": "timestamps/hama1",
        "fields": {"video": "hama1"},
        "source_type": "video"
    },
    "hama2": {
        "ontology": CompressedImage,
        "metadata": {},
        "timestamps": "timestamps/hama2",
        "fields": {"video": "hama2"},
        "source_type": "video"
    },
    "hand": {
        "ontology": CompressedImage,
        "metadata": {},
        "timestamps": "timestamps/hand",
        "fields": {"video": "hand"},
        "source_type": "video"
    },
    "events": {
        "ontology": Image,
        "metadata": {
            "sensor_model": "iniVation DAVIS346",
            "sensor_type": "event_camera",
            "resolution": [EVENT_CAMERA_WIDTH, EVENT_CAMERA_HEIGHT],
            "representation": "binary event image",
        },
        "timestamps": "timestamps/events",
        "fields": {"event": "events"},
        "source_type": "event_stream",
    },
    "robot_state/joint_state": {
        "ontology": RobotJoint,
        "metadata": {"n_joints": 7},
        "timestamps": "timestamps/joint_positions",
        "fields": {
            "position": "robot_state/joint_positions",
            "velocity": "robot_state/joint_velocities",
            "effort": "robot_state/joint_efforts",
        },
    },
    "robot_state/pose": {
        "ontology": Pose,
        "metadata": {},
        "timestamps": "timestamps/pose",
        "fields": {"pose": "robot_state/pose"},
    },
    "robot_state/velocity": {
        "ontology": Velocity,
        "metadata": {},
        "timestamps": "timestamps/velocity",
        "fields": {"velocity": "robot_state/velocity"},
    },
    "robot_state/compensated_base_force_torque": {
        "ontology": ForceTorque,
        "metadata": {},
        "timestamps": "timestamps/compensated_base_force",
        "fields": {
            "compensated_base_force": "robot_state/compensated_base_force",
            "compensated_base_torque": "robot_state/compensated_base_torque",
        },
    },
    "robot_state/measured_force_torque": {
        "ontology": ForceTorque,
        "metadata": {},
        "timestamps": "timestamps/measured_force",
        "fields": {
            "measured_force": "robot_state/measured_force",
            "measured_torque": "robot_state/measured_torque",
        },
    },
}
