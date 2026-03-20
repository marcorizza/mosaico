from pathlib import Path

from mosaicolabs import MosaicoClient, OnErrorPolicy
from packs.manipulation.adapters import build_default_adapter_registry
from packs.manipulation.datasets import build_default_dataset_registry
from packs.manipulation.readers import HDF5Reader


class ManipulationRunner:
    def __init__(self) -> None:
        self.adapter_registry = build_default_adapter_registry()
        self.dataset_registry = build_default_dataset_registry()

    def ingest_root(self, root: Path, client: MosaicoClient) -> None:
        plugin = self.dataset_registry.resolve(root)

        for sequence_path in plugin.discover_sequences(root):
            self.ingest_sequence(sequence_path, plugin, client)

    def ingest_sequence(self, sequence_path: Path, plugin, client: MosaicoClient) -> None:
        plan = plugin.create_sequence_descriptor(sequence_path)

        with HDF5Reader(sequence_path) as reader:
            with client.sequence_create(
                    sequence_name=plan.sequence_name,
                    metadata=plan.sequence_metadata,
                    on_error=OnErrorPolicy.Delete,
            ) as swriter:
                for topic in plan.topics:
                    writer = swriter.get_topic_writer(topic_name=topic.topic_name)

                    if writer is None:
                        writer = swriter.topic_create(
                            topic_name=topic.topic_name,
                            metadata=topic.metadata,
                            ontology_type=topic.ontology_type,
                        )

                    adapter_cls = self.adapter_registry.get(topic.adapter_id)

                    if topic.reader_method == "iter_records":
                        payload_iter = reader.iter_records(
                            timestamps_path=topic.timestamps_path,
                            fields=topic.fields,
                        )
                    else:
                        # HDF5 Reader has a custom method for iterating over video frames
                        # getattr is used to call the method on the HDF5Reader instance
                        reader_fn = getattr(reader, topic.reader_method)
                        payload_iter = reader_fn(**topic.reader_kwargs)

                    for payload in payload_iter:
                        writer.push(adapter_cls.translate(payload))
