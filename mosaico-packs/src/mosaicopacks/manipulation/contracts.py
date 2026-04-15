from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal, Protocol, TypeAlias

from mosaicolabs.models import Serializable

if TYPE_CHECKING:
    from mosaicolabs.ros_bridge import ROSAdapterBase


def normalize_topic_name(topic_name: str) -> str:
    topic_name = topic_name.strip()
    if not topic_name:
        raise ValueError("topic_name cannot be empty")
    return topic_name if topic_name.startswith("/") else f"/{topic_name}"


@dataclass
class TopicDescriptor:
    topic_name: str
    ontology_type: type[Serializable]
    adapter_id: str
    payload_iter: Callable[[Path], Iterable[dict]]
    message_count: Callable[[Path], int]
    metadata: dict[str, Any] = field(default_factory=dict)
    required_paths: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class SequenceDescriptor:
    sequence_name: str
    sequence_metadata: dict[str, Any] = field(default_factory=dict)
    topics: list[TopicDescriptor] = field(default_factory=list)
    find_missing_paths: Callable[[Path, tuple[str, ...]], tuple[str, ...]] | None = None
    backend: str = field(init=False, default="file")


@dataclass
class RosbagSequenceDescriptor:
    bag_path: Path
    sequence_name: str
    sequence_metadata: dict[str, Any] = field(default_factory=dict)
    default_topics: tuple[str, ...] = field(default_factory=tuple)
    adapter_overrides: dict[str, type["ROSAdapterBase"]] = field(default_factory=dict)
    backend: str = field(init=False, default="rosbag")


IngestionDescriptor: TypeAlias = SequenceDescriptor | RosbagSequenceDescriptor
WriteMode: TypeAlias = Literal["sync", "async"]


class DatasetPlugin(Protocol):
    dataset_id: str

    def supports(self, root: Path) -> bool: ...

    def discover_sequences(self, root: Path) -> Iterable[Path]: ...

    def create_ingestion_plan(self, sequence_path: Path) -> IngestionDescriptor: ...
