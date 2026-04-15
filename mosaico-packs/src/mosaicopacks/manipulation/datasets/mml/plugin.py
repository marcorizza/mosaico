from pathlib import Path

from rosbags.highlevel import AnyReader

from mosaicopacks.manipulation.adapters.mml import (
    AudioDataAdapter,
    AudioInfoAdapter,
    JointTorqueCommandAdapter,
    TekscanSensorAdapter,
)
from mosaicopacks.manipulation.contracts import (
    RosbagSequenceDescriptor,
    normalize_topic_name,
)


class MMLPlugin:
    dataset_id = "mml"

    SIGNATURE_TOPICS = (
        "/allegro_hand_right/joint_states",
        "/iiwa/TorqueController/command",
        "/tekscan/frame",
    )

    DEFAULT_TOPICS = (
        "/allegro_hand_right/joint_states",
        "/audio/audio",
        "/audio/audio_info",
        "/iiwa/TorqueController/command",
        "/iiwa/eePose",
        "/iiwa/joint_states",
        "/tekscan/frame",
        "/trialInfo",
    )

    def supports(self, root: Path) -> bool:
        bag_paths = self.discover_sequences(root)
        if not bag_paths:
            return False

        for bag_path in bag_paths:
            try:
                with AnyReader([bag_path]) as reader:
                    available_topics = {
                        normalize_topic_name(connection.topic)
                        for connection in reader.connections
                    }
            except Exception:
                continue

            if set(self.SIGNATURE_TOPICS).issubset(available_topics):
                return True

        return False

    def discover_sequences(self, root: Path) -> list[Path]:
        return sorted(
            sequence_path
            for sequence_path in root.glob("*.bag")
            if not sequence_path.name.startswith("._")
        )

    def create_ingestion_plan(self, sequence_path: Path) -> RosbagSequenceDescriptor:
        return RosbagSequenceDescriptor(
            bag_path=sequence_path,
            sequence_name=f"{self.dataset_id}_{sequence_path.stem}",
            sequence_metadata={
                "dataset_id": self.dataset_id,
                "ingestion_backend": "rosbag",
                "source_file": sequence_path.name,
                "source_path": str(sequence_path),
            },
            default_topics=self.DEFAULT_TOPICS,
            adapter_overrides={
                "/audio/audio": AudioDataAdapter,
                "/audio/audio_info": AudioInfoAdapter,
                "/iiwa/TorqueController/command": JointTorqueCommandAdapter,
                "/tekscan/frame": TekscanSensorAdapter,
            },
        )
