import logging
import time
from collections.abc import Callable
from pathlib import Path

from rich.console import Console

from mosaicolabs import MosaicoClient
from mosaicolabs.handlers.sequence_handler import SequenceHandler
from mosaicolabs.packs.manipulation.contracts import (
    DatasetPlugin,
    RosbagSequenceDescriptor,
)
from mosaicolabs.packs.manipulation.datasets import build_default_dataset_registry
from mosaicolabs.packs.manipulation.runner.native_executor import NativeSequenceExecutor
from mosaicolabs.packs.manipulation.runner.reports import (
    DatasetIngestionReport,
    SequenceIngestionResult,
)
from mosaicolabs.packs.manipulation.runner.rosbag_executor import RosbagSequenceExecutor
from mosaicolabs.platform.helpers import _decode_app_metadata

LOGGER = logging.getLogger(__name__)


class ManipulationRunner:
    def __init__(
        self,
        console: Console | None = None,
        host: str = "localhost",
        port: int = 6276,
        api_key: str | None = None,
        tls_cert_path: str | None = None,
        log_level: str = "INFO",
        stop_requested: Callable[[], bool] | None = None,
    ) -> None:
        self.console = console or Console(stderr=True)
        self.dataset_registry = build_default_dataset_registry()
        self._stop_requested = stop_requested or (lambda: False)
        self._native_executor = NativeSequenceExecutor(self.console)
        self._rosbag_executor = RosbagSequenceExecutor(
            console=self.console,
            host=host,
            port=port,
            log_level=log_level,
            api_key=api_key,
            tls_cert_path=tls_cert_path,
            stop_requested=self._stop_requested,
        )

    def ingest_root(
        self,
        root: Path,
        client: MosaicoClient,
        dataset_index: int | None = None,
        dataset_total: int | None = None,
    ) -> DatasetIngestionReport:
        dataset_start = time.monotonic()
        dataset_label = (
            f"[{dataset_index}/{dataset_total}] "
            if dataset_index and dataset_total
            else ""
        )

        if self._stop_requested():
            report = DatasetIngestionReport.interrupted_report(root=root)
            report.duration_s = time.monotonic() - dataset_start
            return report

        if not root.exists():
            report = DatasetIngestionReport.failed_report(
                root=root,
                error=f"Dataset root does not exist: {root}",
            )
            report.duration_s = time.monotonic() - dataset_start
            LOGGER.error("%sDataset root does not exist: %s", dataset_label, root)
            return report

        try:
            plugin = self.dataset_registry.resolve(root)
            plugin_id = getattr(plugin, "dataset_id", type(plugin).__name__)
            sequence_paths = list(plugin.discover_sequences(root))
        except Exception:
            LOGGER.exception(
                "Failed to resolve dataset root %s; aborting this ingestion run.",
                root,
            )
            return DatasetIngestionReport.failed_report(
                root=root,
                plugin_id="unresolved",
                error=f"Failed to resolve dataset root '{root}'.",
                duration_s=time.monotonic() - dataset_start,
            )

        report = DatasetIngestionReport(
            root=root,
            plugin_id=plugin_id,
            discovered=len(sequence_paths),
        )

        try:
            existing_sequences = set(client.list_sequences())
        except Exception:
            LOGGER.exception(
                "Failed to list existing sequences; continuing without skip detection."
            )
            report.errors.append(
                "Failed to list existing sequences; skip detection was disabled."
            )
            existing_sequences = set()

        LOGGER.info(
            "%sDataset '%s' from %s with %d sequence(s)",
            dataset_label,
            plugin_id,
            root,
            len(sequence_paths),
        )
        LOGGER.info("Found %d existing sequence(s) on server", len(existing_sequences))

        if not sequence_paths:
            LOGGER.warning("No sequences discovered under %s", root)
            report.duration_s = time.monotonic() - dataset_start
            report.remote_size_bytes = 0
            LOGGER.info(
                "%sCompleted dataset '%s' — discovered=%d ingested=%d skipped=%d failed=%d duration=%.2fs",
                dataset_label,
                plugin_id,
                report.discovered,
                report.ingested,
                report.skipped,
                report.failed,
                report.duration_s,
            )
            return report

        for index, sequence_path in enumerate(sequence_paths, start=1):
            if self._stop_requested():
                report.status = "interrupted"
                report.errors.append("Interrupted by user.")
                break

            LOGGER.info(
                "Ingesting sequence %d/%d from %s",
                index,
                len(sequence_paths),
                sequence_path,
            )
            try:
                sequence_result = self.ingest_sequence(
                    sequence_path,
                    plugin,
                    client,
                    existing_sequences=existing_sequences,
                )
            except KeyboardInterrupt:
                report.status = "interrupted"
                report.errors.append("Interrupted by user.")
                break
            except Exception:
                LOGGER.exception(
                    "Sequence '%s' failed; continuing with the next sequence.",
                    sequence_path.name,
                )
                sequence_result = SequenceIngestionResult(
                    sequence_name=sequence_path.name,
                    status="failed",
                    local_size_bytes=self._get_local_sequence_size(sequence_path),
                    error=f"Sequence '{sequence_path.name}' failed unexpectedly.",
                )

            report.record_sequence(sequence_result)

            if sequence_result.status == "interrupted":
                report.status = "interrupted"
                break

        report.duration_s = time.monotonic() - dataset_start
        report.finalize(interrupted=report.status == "interrupted")
        report.remote_size_bytes = self._resolve_remote_size(client, report)

        LOGGER.info(
            "%sCompleted dataset '%s' — discovered=%d ingested=%d skipped=%d failed=%d duration=%.2fs",
            dataset_label,
            plugin_id,
            report.discovered,
            report.ingested,
            report.skipped,
            report.failed,
            report.duration_s,
        )

        return report

    def ingest_sequence(
        self,
        sequence_path: Path,
        plugin: DatasetPlugin,
        client: MosaicoClient,
        existing_sequences: set[str] | None = None,
    ) -> SequenceIngestionResult:
        local_size = self._get_local_sequence_size(sequence_path)

        try:
            plan = plugin.create_ingestion_plan(sequence_path)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            LOGGER.exception(
                "Failed to create ingestion plan for sequence '%s'.",
                sequence_path.name,
            )
            return SequenceIngestionResult(
                sequence_name=sequence_path.name,
                status="failed",
                local_size_bytes=local_size,
                error=f"Failed to create ingestion plan for '{sequence_path.name}': {exc}",
            )

        backend = getattr(plan, "backend", "native")

        if self._stop_requested():
            return SequenceIngestionResult(
                sequence_name=plan.sequence_name,
                status="interrupted",
                local_size_bytes=local_size,
                backend=backend,
                plan=plan,
                error="Interrupted by user.",
            )

        try:
            if isinstance(plan, RosbagSequenceDescriptor):
                ingested = self._rosbag_executor.ingest_sequence(
                    plan,
                    client=client,
                    existing_sequences=existing_sequences,
                )
            else:
                ingested = self._native_executor.ingest_sequence(
                    sequence_path,
                    plan,
                    client=client,
                    existing_sequences=existing_sequences,
                )
        except KeyboardInterrupt:
            return SequenceIngestionResult(
                sequence_name=plan.sequence_name,
                status="interrupted",
                local_size_bytes=local_size,
                backend=backend,
                plan=plan,
                error="Interrupted by user.",
            )
        except Exception as exc:
            LOGGER.exception(
                "Sequence '%s' failed; continuing with the next sequence.",
                sequence_path.name,
            )
            return SequenceIngestionResult(
                sequence_name=plan.sequence_name,
                status="failed",
                local_size_bytes=local_size,
                backend=backend,
                plan=plan,
                error=f"Sequence '{plan.sequence_name}' failed: {exc}",
            )

        if self._stop_requested():
            return SequenceIngestionResult(
                sequence_name=plan.sequence_name,
                status="interrupted",
                local_size_bytes=local_size,
                backend=backend,
                plan=plan,
                error="Interrupted by user.",
            )

        if not ingested:
            return SequenceIngestionResult(
                sequence_name=plan.sequence_name,
                status="skipped",
                local_size_bytes=local_size,
                backend=backend,
                plan=plan,
            )

        return SequenceIngestionResult(
            sequence_name=plan.sequence_name,
            status="ingested",
            local_size_bytes=local_size,
            backend=backend,
            plan=plan,
        )

    def _get_local_sequence_size(self, sequence_path: Path) -> int:
        try:
            return sequence_path.stat().st_size
        except OSError:
            LOGGER.exception(
                "Failed to read local size for sequence '%s'; using 0 bytes.",
                sequence_path.name,
            )
            return 0

    def _resolve_remote_size(
        self,
        client: MosaicoClient,
        report: DatasetIngestionReport,
    ) -> int | None:
        if report.ingested == 0:
            return 0

        total_remote_size = 0
        for plan in report.ingested_plans:
            try:
                total_remote_size += self._get_remote_sequence_size(
                    client,
                    plan.sequence_name,
                )
            except Exception:
                LOGGER.exception(
                    "Failed to retrieve remote size for sequence '%s'; continuing.",
                    plan.sequence_name,
                )
                report.errors.append(
                    f"Failed to retrieve remote size for '{plan.sequence_name}'."
                )
                return None

        return total_remote_size

    def _get_remote_sequence_size(
        self,
        client: MosaicoClient,
        sequence_name: str,
    ) -> int:
        flight_info, _ = SequenceHandler._get_flight_info(
            client=client._control_client,
            sequence_name=sequence_name,
        )

        total_size_bytes = 0
        for endpoint in flight_info.endpoints:
            endpoint_metadata = _decode_app_metadata(endpoint.app_metadata)
            info_metadata = endpoint_metadata.get("info", {})
            if not isinstance(info_metadata, dict):
                raise ValueError(
                    f"Unexpected endpoint metadata format for '{sequence_name}'."
                )

            endpoint_size = info_metadata.get("total_bytes")
            if endpoint_size is None:
                raise ValueError(
                    f"Missing 'total_bytes' in endpoint metadata for '{sequence_name}'."
                )

            total_size_bytes += int(endpoint_size)

        return total_size_bytes
