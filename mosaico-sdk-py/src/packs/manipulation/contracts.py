from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, Iterable


@dataclass
class TopicDescriptor:
    topic_name: str
    ontology_type: type
    adapter_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamps_path: str | None = None
    fields: dict[str, str] = field(default_factory=dict)
    reader_method: str = "iter_records"
    reader_kwargs: dict[str, Any] = field(default_factory=dict)


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
