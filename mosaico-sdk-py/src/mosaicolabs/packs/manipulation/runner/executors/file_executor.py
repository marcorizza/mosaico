import logging
from pathlib import Path

from mosaicolabs import OnErrorPolicy
from mosaicolabs.packs.manipulation.contracts import SequenceDescriptor, WriteMode
from mosaicolabs.packs.manipulation.runner.reporters.sequence_progress import (
    SequenceProgress,
)
from mosaicolabs.packs.manipulation.runner.topic_ingester import TopicIngester

LOGGER = logging.getLogger(__name__)


class FileSequenceExecutor:
    def __init__(self, console, write_mode: WriteMode = "sync") -> None:
        self.console = console
        self._write_mode = write_mode
        self._ingester = TopicIngester(write_mode=write_mode)

    def ingest_sequence(
        self,
        sequence_path: Path,
        plan: SequenceDescriptor,
        client,
        existing_sequences: set[str] | None = None,
    ) -> bool:
        if existing_sequences is not None and plan.sequence_name in existing_sequences:
            LOGGER.warning(
                "Sequence '%s' already exists, skipping.", plan.sequence_name
            )
            return False

        LOGGER.info(
            "Creating file sequence '%s' from %s with %d topic(s) using %s topic ingestion",
            plan.sequence_name,
            sequence_path.name,
            len(plan.topics),
            (
                "sync (default)"
                if self._write_mode == "sync"
                else "async (shared-client topic threads)"
            ),
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
                total_messages = self._ingester.run_ingestion(
                    sequence_path,
                    topic_writers,
                    ui,
                    missing_topic_sources=missing_topic_sources,
                )

        LOGGER.info(
            "Completed file sequence '%s' — %d topic(s), %d message(s)",
            plan.sequence_name,
            len(plan.topics),
            total_messages,
        )

        if existing_sequences is not None:
            existing_sequences.add(plan.sequence_name)

        return True

    def _find_missing_topic_sources(
        self,
        sequence_path: Path,
        plan: SequenceDescriptor,
    ) -> dict[str, tuple[str, ...]]:
        missing_topic_sources: dict[str, tuple[str, ...]] = {}

        if not plan.find_missing_paths:
            return missing_topic_sources

        for topic in plan.topics:
            if not topic.required_paths:
                continue

            missing_paths = plan.find_missing_paths(sequence_path, topic.required_paths)
            if not missing_paths:
                continue

            missing_topic_sources[topic.topic_name] = tuple(missing_paths)
            missing_list = ", ".join(missing_paths)
            LOGGER.warning(
                "Topic '%s' is missing source path(s) [%s] in '%s'; creating it empty.",
                topic.topic_name,
                missing_list,
                sequence_path.name,
            )

        return missing_topic_sources
