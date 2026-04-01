from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

from mosaicolabs.models import Serializable


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


class DatasetPlugin(Protocol):
    dataset_id: str

    def supports(self, root: Path) -> bool: ...

    def discover_sequences(self, root: Path) -> Iterable[Path]: ...

    def create_sequence_descriptor(self, sequence_path: Path) -> SequenceDescriptor: ...
