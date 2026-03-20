from pathlib import Path

from mosaicolabs import RobotJoint, Pose, Velocity, ForceTorque, CompressedImage, Image
from packs.manipulation.contracts import SequenceDescriptor, TopicDescriptor


class ReassemblePlugin:
    dataset_id = "reassemble"

    def supports(self, root: Path) -> bool:
        return any(root.glob("*.h5"))

    def discover_sequences(self, root: Path) -> list[Path]:
        return sorted(root.glob("*.h5"))

    def create_sequence_descriptor(self, sequence_path: Path) -> SequenceDescriptor:
        return SequenceDescriptor(
            sequence_name=sequence_path.stem,
            sequence_metadata={
                "dataset_id": self.dataset_id,
                "source_file": sequence_path.name,
            },
            topics=[
                TopicDescriptor(
                    topic_name="capture_node-camera-image",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    metadata={
                        "sensor_model": "iniVation DAVIS346",
                        "sensor_type": "event_camera",
                        "resolution": "[346, 260]",
                        "frame_sensor": "APS grayscale",
                        "datasheet": "https://inivation.com/wp-content/uploads/2019/08/DAVIS346.pdf",
                    },
                    reader_method="iter_video_frames",
                    reader_kwargs={
                        "video_path": "capture_node-camera-image",
                        "timestamps_path": "timestamps/capture_node-camera-image",
                    },
                ),
                TopicDescriptor(
                    topic_name="events",
                    ontology_type=Image,
                    adapter_id="reassemble.events",
                    metadata={
                        "sensor_model": "iniVation DAVIS346",
                        "sensor_type": "event_camera",
                        "resolution": "[346, 260]",
                        "representation": "binary event image",
                    },
                    timestamps_path="timestamps/events",
                    fields={"event": "events"},
                ),
                TopicDescriptor(
                    topic_name="hama1",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    reader_method="iter_video_frames",
                    reader_kwargs={
                        "video_path": "hama1",
                        "timestamps_path": "timestamps/hama1",
                    },
                ),
                TopicDescriptor(
                    topic_name="hama2",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    reader_method="iter_video_frames",
                    reader_kwargs={
                        "video_path": "hama2",
                        "timestamps_path": "timestamps/hama2",
                    },
                ),
                TopicDescriptor(
                    topic_name="hand",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    reader_method="iter_video_frames",
                    reader_kwargs={
                        "video_path": "hand",
                        "timestamps_path": "timestamps/hand",
                    },
                ),
                TopicDescriptor(
                    topic_name="robot_state/joint_state",
                    ontology_type=RobotJoint,
                    adapter_id="reassemble.joint_state",
                    metadata={"n_joints": 7},
                    timestamps_path="timestamps/joint_positions",
                    fields={
                        "position": "robot_state/joint_positions",
                        "velocity": "robot_state/joint_velocities",
                        "effort": "robot_state/joint_efforts",
                    },
                ),
                TopicDescriptor(
                    topic_name="robot_state/pose",
                    ontology_type=Pose,
                    adapter_id="reassemble.pose",
                    timestamps_path="timestamps/pose",
                    fields={"pose": "robot_state/pose"},
                ),
                TopicDescriptor(
                    topic_name="robot_state/velocity",
                    ontology_type=Velocity,
                    adapter_id="reassemble.velocity",
                    timestamps_path="timestamps/velocity",
                    fields={"velocity": "robot_state/velocity"},
                ),
                TopicDescriptor(
                    topic_name="robot_state/compensated_base_force_torque",
                    ontology_type=ForceTorque,
                    adapter_id="reassemble.compensated_base_force_torque",
                    timestamps_path="timestamps/compensated_base_force",
                    fields={
                        "compensated_base_force": "robot_state/compensated_base_force",
                        "compensated_base_torque": "robot_state/compensated_base_torque",
                    },
                ),
                TopicDescriptor(
                    topic_name="robot_state/measured_force_torque",
                    ontology_type=ForceTorque,
                    adapter_id="reassemble.measured_force",
                    timestamps_path="timestamps/measured_force",
                    fields={
                        "measured_force": "robot_state/measured_force",
                        "measured_torque": "robot_state/measured_torque",
                    },
                ),
            ]
        )
