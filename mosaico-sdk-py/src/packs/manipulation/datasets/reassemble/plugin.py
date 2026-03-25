from pathlib import Path

from mosaicolabs import RobotJoint, Pose, Velocity, ForceTorque, CompressedImage

from packs.manipulation.contracts import SequenceDescriptor, TopicDescriptor
from packs.manipulation.datasets.reassemble.iterators import *
from packs.manipulation.ontology.audio import AudioDataStamped
from packs.manipulation.ontology.event_camera import EventCamera
from packs.manipulation.ontology.end_effector import EndEffector


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
                    payload_iter=iter_video_frames(
                        video_path="capture_node-camera-image",
                        timestamps_path="timestamps/capture_node-camera-image",
                    ),
                    message_count=count_video_frames(
                        "timestamps/capture_node-camera-image"
                    ),
                    metadata={
                        "sensor_model": "iniVation DAVIS346",
                        "sensor_type": "event_camera",
                        "resolution": "[346, 260]",
                        "frame_sensor": "APS grayscale",
                        "datasheet": "https://inivation.com/wp-content/uploads/2019/08/DAVIS346.pdf",
                    },
                ),
                TopicDescriptor(
                    topic_name="events",
                    ontology_type=EventCamera,
                    adapter_id="reassemble.events",
                    payload_iter=iter_event_frames(
                        events_path="events",
                        timestamps_path="timestamps/events",
                    ),
                    message_count=count_event_frames("timestamps/events"),
                    metadata={
                        "sensor_model": "iniVation DAVIS346",
                        "sensor_type": "event_camera",
                        "resolution": "[346, 260]",
                        "representation": "33ms event window with raw events",
                        "window_ms": 33,
                    },
                ),
                TopicDescriptor(
                    topic_name="hama1",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    payload_iter=iter_video_frames(
                        video_path="hama1",
                        timestamps_path="timestamps/hama1",
                    ),
                    message_count=count_video_frames("timestamps/hama1"),
                ),
                TopicDescriptor(
                    topic_name="hama1_audio",
                    ontology_type=AudioDataStamped,
                    adapter_id="reassemble.audio",
                    payload_iter=iter_audio(
                        audio_path="hama1_audio",
                        timestamps_path="timestamps/hama1",
                    ),
                    message_count=count_audio(
                        audio_path="hama1_audio",
                        timestamps_path="timestamps/hama1",
                    ),
                ),
                TopicDescriptor(
                    topic_name="hama2",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    payload_iter=iter_video_frames(
                        video_path="hama2",
                        timestamps_path="timestamps/hama2",
                    ),
                    message_count=count_video_frames("timestamps/hama2"),
                ),
                TopicDescriptor(
                    topic_name="hama2_audio",
                    ontology_type=AudioDataStamped,
                    adapter_id="reassemble.audio",
                    payload_iter=iter_audio(
                        audio_path="hama2_audio",
                        timestamps_path="timestamps/hama2",
                    ),
                    message_count=count_audio(
                        audio_path="hama2_audio",
                        timestamps_path="timestamps/hama2",
                    ),
                ),
                TopicDescriptor(
                    topic_name="hand",
                    ontology_type=CompressedImage,
                    adapter_id="reassemble.video_frame",
                    payload_iter=iter_video_frames(
                        video_path="hand",
                        timestamps_path="timestamps/hand",
                    ),
                    message_count=count_video_frames("timestamps/hand"),
                ),
                TopicDescriptor(
                    topic_name="hand_audio",
                    ontology_type=AudioDataStamped,
                    adapter_id="reassemble.audio",
                    payload_iter=iter_audio(
                        audio_path="hand_audio",
                        timestamps_path="timestamps/hand",
                    ),
                    message_count=count_audio(
                        audio_path="hand_audio",
                        timestamps_path="timestamps/hand",
                    ),
                ),
                TopicDescriptor(
                    topic_name="robot_state/joint_state",
                    ontology_type=RobotJoint,
                    adapter_id="reassemble.joint_state",
                    payload_iter=iter_records(
                        timestamps_path="timestamps/joint_positions",
                        fields={
                            "position": "robot_state/joint_positions",
                            "velocity": "robot_state/joint_velocities",
                            "effort": "robot_state/joint_efforts",
                        },
                    ),
                    message_count=count_records("timestamps/joint_positions"),
                    metadata={"n_joints": 7},
                ),
                TopicDescriptor(
                    topic_name="robot_state/pose",
                    ontology_type=Pose,
                    adapter_id="reassemble.pose",
                    payload_iter=iter_records(
                        timestamps_path="timestamps/pose",
                        fields={"pose": "robot_state/pose"},
                    ),
                    message_count=count_records("timestamps/pose"),
                ),
                TopicDescriptor(
                    topic_name="robot_state/velocity",
                    ontology_type=Velocity,
                    adapter_id="reassemble.velocity",
                    payload_iter=iter_records(
                        timestamps_path="timestamps/velocity",
                        fields={"velocity": "robot_state/velocity"},
                    ),
                    message_count=count_records("timestamps/velocity"),
                ),
                TopicDescriptor(
                    topic_name="robot_state/compensated_base_force_torque",
                    ontology_type=ForceTorque,
                    adapter_id="reassemble.compensated_base_force_torque",
                    payload_iter=iter_records(
                        timestamps_path="timestamps/compensated_base_force",
                        fields={
                            "compensated_base_force": "robot_state/compensated_base_force",
                            "compensated_base_torque": "robot_state/compensated_base_torque",
                        },
                    ),
                    message_count=count_records(
                        "timestamps/compensated_base_force"
                    ),
                ),
                TopicDescriptor(
                    topic_name="robot_state/measured_force_torque",
                    ontology_type=ForceTorque,
                    adapter_id="reassemble.measured_force_torque",
                    payload_iter=iter_records(
                        timestamps_path="timestamps/measured_force",
                        fields={
                            "measured_force": "robot_state/measured_force",
                            "measured_torque": "robot_state/measured_torque",
                        },
                    ),
                    message_count=count_records("timestamps/measured_force"),
                ),
                TopicDescriptor(
                    topic_name="robot_state/end_effector",
                    ontology_type=EndEffector,
                    adapter_id="reassemble.end_effector",
                    payload_iter=iter_records(
                        timestamps_path="timestamps/gripper_efforts",
                        fields={
                            "gripper_efforts": "robot_state/gripper_efforts",
                            "gripper_positions": "robot_state/gripper_positions",
                            "gripper_velocities": "robot_state/gripper_velocities",
                        },
                    ),
                    message_count=count_records("timestamps/gripper_efforts"),
                )
            ],
        )
