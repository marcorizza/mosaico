import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from mosaicolabs import MosaicoClient, OnErrorPolicy
from packs.manipulation.contracts import DatasetPlugin
from packs.manipulation.datasets import build_default_dataset_registry
from packs.manipulation.readers import HDF5Reader
from packs.manipulation.runner.sequence_progress import SequenceProgress
from packs.manipulation.runner.topic_ingester import TopicIngester
from packs.manipulation.runner.upload_reporter import UploadReporter

LOGGER = logging.getLogger(__name__)


class ManipulationRunner:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console(stderr=True)
        self.dataset_registry = build_default_dataset_registry()
        self._ingester = TopicIngester()
        self._reporter = UploadReporter(self.console)

    def ingest_root(self, root: Path, client: MosaicoClient) -> None:
        self.console.print(
            Panel("[bold green]Starting Manipulation Ingestion[/bold green]")
        )
        try:
            plugin = self.dataset_registry.resolve(root)
            plugin_id = getattr(plugin, "dataset_id", type(plugin).__name__)
            sequence_paths = list(plugin.discover_sequences(root))
        except Exception:
            LOGGER.exception(
                "Failed to resolve dataset root %s; aborting this ingestion run.",
                root,
            )
            return

        try:
            existing_sequences = set(client.list_sequences())
        except Exception:
            LOGGER.exception(
                "Failed to list existing sequences; continuing without skip detection."
            )
            existing_sequences = set()

        LOGGER.info(
            "Resolved dataset root %s with plugin '%s' and %d sequence(s)",
            root,
            plugin_id,
            len(sequence_paths),
        )
        LOGGER.info("Found %d existing sequence(s) on server", len(existing_sequences))

        if not sequence_paths:
            LOGGER.warning("No sequences discovered under %s", root)
            return

        ingested: list[tuple] = []

        for index, sequence_path in enumerate(sequence_paths, start=1):
            LOGGER.info(
                "Ingesting sequence %d/%d from %s",
                index,
                len(sequence_paths),
                sequence_path,
            )
            try:
                plan = self.ingest_sequence(
                    sequence_path,
                    plugin,
                    client,
                    existing_sequences=existing_sequences,
                )
            except Exception:
                LOGGER.exception(
                    "Sequence '%s' failed; continuing with the next sequence.",
                    sequence_path.name,
                )
                continue

            if plan is None:
                continue

            try:
                sequence_size = sequence_path.stat().st_size
            except OSError:
                LOGGER.exception(
                    "Failed to read local size for sequence '%s'; using 0 bytes.",
                    sequence_path.name,
                )
                sequence_size = 0

            ingested.append((plan, sequence_size))

        plans = [plan for plan, _ in ingested]
        total_original_size = sum(size for _, size in ingested)
        total_remote_size = 0
        for plan in plans:
            try:
                total_remote_size += self._reporter.get_remote_sequence_size(
                    client,
                    plan.sequence_name,
                )
            except Exception:
                LOGGER.exception(
                    "Failed to retrieve remote size for sequence '%s'; continuing.",
                    plan.sequence_name,
                )

        try:
            self._reporter.print_summary(
                original_size=total_original_size,
                remote_size=total_remote_size,
            )
        except Exception:
            LOGGER.exception("Failed to print upload summary; continuing.")

        try:
            self._reporter.print_verification(client, plans)
        except Exception:
            LOGGER.exception("Failed to verify uploaded data; continuing.")

    def ingest_sequence(
        self,
        sequence_path: Path,
        plugin: DatasetPlugin,
        client: MosaicoClient,
        existing_sequences: set[str] | None = None,
    ):
        plan = plugin.create_sequence_descriptor(sequence_path)

        if existing_sequences is not None and plan.sequence_name in existing_sequences:
            LOGGER.warning(
                "Sequence '%s' already exists, skipping.",
                plan.sequence_name,
            )
            return None

        LOGGER.info(
            "Creating sequence '%s' from %s with %d topic(s)",
            plan.sequence_name,
            sequence_path.name,
            len(plan.topics),
        )

        missing_topic_sources = self._find_missing_topic_sources(sequence_path, plan)
        topic_totals = {
            topic.topic_name: (
                0
                if topic.topic_name in missing_topic_sources
                else topic.message_count(sequence_path)
            )
            for topic in plan.topics
        }
        ui = SequenceProgress(self.console)
        ui.setup(topic_totals)

        with client.sequence_create(
            sequence_name=plan.sequence_name,
            metadata=plan.sequence_metadata,
            on_error=OnErrorPolicy.Delete,
        ) as swriter:
            with ui.live():
                topic_writers = self._ingester.prepare_topic_writers(swriter, plan, ui)
                total_messages = self._ingester.run_parallel_ingestion(
                    sequence_path,
                    topic_writers,
                    ui,
                    missing_topic_sources=missing_topic_sources,
                )

        LOGGER.info(
            "Completed sequence '%s' — %d topic(s), %d message(s)",
            plan.sequence_name,
            len(plan.topics),
            total_messages,
        )

        if existing_sequences is not None:
            existing_sequences.add(plan.sequence_name)

        return plan

    def _find_missing_topic_sources(
        self,
        sequence_path: Path,
        plan,
    ) -> dict[str, tuple[str, ...]]:
        missing_topic_sources: dict[str, tuple[str, ...]] = {}

        with HDF5Reader(sequence_path) as reader:
            for topic in plan.topics:
                if not topic.required_paths:
                    continue

                missing_paths = reader.missing_paths(topic.required_paths)
                if not missing_paths:
                    continue

                missing_topic_sources[topic.topic_name] = missing_paths
                missing_list = ", ".join(missing_paths)
                LOGGER.warning(
                    "Topic '%s' is missing source path(s) [%s] in '%s'; "
                    "creating it empty.",
                    topic.topic_name,
                    missing_list,
                    sequence_path.name,
                )

        return missing_topic_sources
