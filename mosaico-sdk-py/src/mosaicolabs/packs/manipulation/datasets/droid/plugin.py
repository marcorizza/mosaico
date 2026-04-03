from pathlib import Path

from mosaicolabs import (
    Boolean,
    CompressedImage,
    Floating64,
    Integer64,
    Pose,
    RobotJoint,
)
from mosaicolabs.packs.manipulation.contracts import SequenceDescriptor, TopicDescriptor
from mosaicolabs.packs.manipulation.datasets.droid.iterators import (
    count_parquet_records,
    iter_mp4_frames,
    iter_parquet_records,
)
from mosaicolabs.packs.manipulation.ontology.end_effector import EndEffector


class DROIDPlugin:
    dataset_id = "droid"

    def supports(self, root: Path) -> bool:
        return any(root.glob("**/*.parquet"))

    def discover_sequences(self, root: Path) -> list[Path]:
        import pyarrow.parquet as pq

        sequences = []
        for p in root.glob("**/*.parquet"):
            try:
                table = pq.read_table(p, columns=["episode_index"])
                episodes = table.column("episode_index").unique().to_pylist()
                for ep in episodes:
                    virtual_name = f"{p.stem}@@{ep:06d}{p.suffix}"
                    sequences.append(p.with_name(virtual_name))
            except Exception:
                pass
        return sorted(sequences)

    def _extract_episode_metadata(
        self, real_path: Path, episode_index: int, base_metadata: dict
    ) -> dict:
        metadata = dict(base_metadata)
        try:
            import pyarrow.dataset as ds

            d = ds.dataset(real_path, format="parquet")
            schema_names = d.schema.names

            meta_cols = [
                "language_instruction",
                "language_instruction_2",
                "language_instruction_3",
                "task_category",
                "building",
                "collector_id",
                "date",
                "is_episode_successful",
            ]
            valid_cols = [c for c in meta_cols if c in schema_names]

            if valid_cols:
                scanner = d.scanner(
                    columns=valid_cols,
                    filter=(ds.field("episode_index") == episode_index),
                )
                df = scanner.head(1).to_pandas()
                if len(df) > 0:
                    row = df.iloc[0]
                    for col in valid_cols:
                        if col in row:
                            val = row[col]
                            if col == "is_episode_successful":
                                import pandas as pd

                                metadata[col] = bool(val) if not pd.isna(val) else False
                            else:
                                metadata[col] = val
        except Exception:
            pass

        return metadata

    def _find_missing_paths(self, sequence_path: Path, required_paths: tuple[str, ...]) -> tuple[str, ...]:
        import pyarrow.dataset as ds

        real_path = sequence_path
        if "@@" in sequence_path.name:
            real_stem = sequence_path.stem.split("@@")[0]
            real_path = sequence_path.with_name(f"{real_stem}{sequence_path.suffix}")

        try:
            dataset = ds.dataset(real_path, format="parquet")
            available_paths = set(dataset.schema.names)
        except Exception:
            available_paths = set()

        return tuple(p for p in required_paths if p not in available_paths)

    def create_ingestion_plan(self, sequence_path: Path) -> SequenceDescriptor:
        if "@@" in sequence_path.name:
            stem, rest = sequence_path.name.split("@@", 1)
            ep_str_suffix = rest

            ep_str = ep_str_suffix.split(".")[0]
            episode_index = int(ep_str)

            real_name = f"{stem}{sequence_path.suffix}"
            real_path = sequence_path.with_name(real_name)
        else:
            real_path = sequence_path
            episode_index = 0

        seq_name = f"{self.dataset_id}_{real_path.stem}_ep{episode_index}"

        base_metadata = {
            "dataset_id": self.dataset_id,
            "ingestion_backend": "file",
            "source_file": real_path.name,
            "episode_index": episode_index,
        }
        metadata = self._extract_episode_metadata(
            real_path, episode_index, base_metadata
        )

        return SequenceDescriptor(
            sequence_name=seq_name,
            sequence_metadata=metadata,
            find_missing_paths=self._find_missing_paths,
            topics=[
                TopicDescriptor(
                    topic_name="/observation/state/joint_position",
                    ontology_type=RobotJoint,
                    adapter_id="droid.joint_state",
                    payload_iter=iter_parquet_records(
                        fields={"position": "observation.state.joint_position"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("observation.state.joint_position",),
                ),
                TopicDescriptor(
                    topic_name="/step/is_first",
                    ontology_type=Boolean,
                    adapter_id="droid.boolean",
                    payload_iter=iter_parquet_records(
                        fields={"value": "is_first"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("is_first",),
                ),
                TopicDescriptor(
                    topic_name="/step/is_last",
                    ontology_type=Boolean,
                    adapter_id="droid.boolean",
                    payload_iter=iter_parquet_records(
                        fields={"value": "is_last"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("is_last",),
                ),
                TopicDescriptor(
                    topic_name="/step/is_terminal",
                    ontology_type=Boolean,
                    adapter_id="droid.boolean",
                    payload_iter=iter_parquet_records(
                        fields={"value": "is_terminal"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("is_terminal",),
                ),
                TopicDescriptor(
                    topic_name="/step/reward",
                    ontology_type=Floating64,
                    adapter_id="droid.floating64",
                    payload_iter=iter_parquet_records(
                        fields={"value": "reward"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("reward",),
                ),
                TopicDescriptor(
                    topic_name="/step/discount",
                    ontology_type=Floating64,
                    adapter_id="droid.floating64",
                    payload_iter=iter_parquet_records(
                        fields={"value": "discount"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("discount",),
                ),
                TopicDescriptor(
                    topic_name="/step/task_index",
                    ontology_type=Integer64,
                    adapter_id="droid.integer64",
                    payload_iter=iter_parquet_records(
                        fields={"value": "task_index"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("task_index",),
                ),
                TopicDescriptor(
                    topic_name="/step/frame_index",
                    ontology_type=Integer64,
                    adapter_id="droid.integer64",
                    payload_iter=iter_parquet_records(
                        fields={"value": "frame_index"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("frame_index",),
                ),
                TopicDescriptor(
                    topic_name="/observation/state/cartesian_position",
                    ontology_type=Pose,
                    adapter_id="droid.pose",
                    payload_iter=iter_parquet_records(
                        fields={"pose": "observation.state.cartesian_position"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("observation.state.cartesian_position",),
                ),
                TopicDescriptor(
                    topic_name="/observation/state/gripper_position",
                    ontology_type=EndEffector,
                    adapter_id="droid.end_effector",
                    payload_iter=iter_parquet_records(
                        fields={"position": "observation.state.gripper_position"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("observation.state.gripper_position",),
                ),
                TopicDescriptor(
                    topic_name="/action/joint_position",
                    ontology_type=RobotJoint,
                    adapter_id="droid.joint_state",
                    payload_iter=iter_parquet_records(
                        fields={
                            "position": "action.joint_position",
                            "velocity": "action.joint_velocity",
                        },
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("action.joint_position",),
                ),
                TopicDescriptor(
                    topic_name="/action/cartesian_position",
                    ontology_type=Pose,
                    adapter_id="droid.pose",
                    payload_iter=iter_parquet_records(
                        fields={"pose": "action.cartesian_position"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("action.cartesian_position",),
                ),
                TopicDescriptor(
                    topic_name="/action/gripper_position",
                    ontology_type=EndEffector,
                    adapter_id="droid.end_effector",
                    payload_iter=iter_parquet_records(
                        fields={
                            "position": "action.gripper_position",
                            "velocity": "action.gripper_velocity",
                        },
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("action.gripper_position",),
                ),
                TopicDescriptor(
                    topic_name="/camera_extrinsics/wrist_left",
                    ontology_type=Pose,
                    adapter_id="droid.pose",
                    payload_iter=iter_parquet_records(
                        fields={"pose": "camera_extrinsics.wrist_left"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("camera_extrinsics.wrist_left",),
                ),
                TopicDescriptor(
                    topic_name="/camera_extrinsics/exterior_1_left",
                    ontology_type=Pose,
                    adapter_id="droid.pose",
                    payload_iter=iter_parquet_records(
                        fields={"pose": "camera_extrinsics.exterior_1_left"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("camera_extrinsics.exterior_1_left",),
                ),
                TopicDescriptor(
                    topic_name="/camera_extrinsics/exterior_2_left",
                    ontology_type=Pose,
                    adapter_id="droid.pose",
                    payload_iter=iter_parquet_records(
                        fields={"pose": "camera_extrinsics.exterior_2_left"},
                        real_path=real_path,
                        episode_index=episode_index,
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                    required_paths=("camera_extrinsics.exterior_2_left",),
                ),
                TopicDescriptor(
                    topic_name="/observation/images/wrist_left",
                    ontology_type=CompressedImage,
                    adapter_id="droid.video_frame",
                    payload_iter=iter_mp4_frames(
                        real_path, episode_index, "observation.images.wrist_left"
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                ),
                TopicDescriptor(
                    topic_name="/observation/images/exterior_1_left",
                    ontology_type=CompressedImage,
                    adapter_id="droid.video_frame",
                    payload_iter=iter_mp4_frames(
                        real_path, episode_index, "observation.images.exterior_1_left"
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                ),
                TopicDescriptor(
                    topic_name="/observation/images/exterior_2_left",
                    ontology_type=CompressedImage,
                    adapter_id="droid.video_frame",
                    payload_iter=iter_mp4_frames(
                        real_path, episode_index, "observation.images.exterior_2_left"
                    ),
                    message_count=count_parquet_records(real_path, episode_index),
                ),
            ],
        )
