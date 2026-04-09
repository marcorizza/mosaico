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
    WriteMode,
)
from mosaicolabs.packs.manipulation.datasets import (
    DatasetRegistry,
    build_default_dataset_registry,
)
from mosaicolabs.packs.manipulation.runner.executors.file_executor import (
    FileSequenceExecutor,
)
from mosaicolabs.packs.manipulation.runner.executors.rosbag_executor import (
    RosbagSequenceExecutor,
)
from mosaicolabs.packs.manipulation.runner.reporters.reports import (
    DatasetIngestionReport,
    SequenceIngestionResult,
)
from mosaicolabs.platform.helpers import _decode_app_metadata

LOGGER = logging.getLogger(__name__)


class ManipulationRunner:
    def __init__(
        self,
        console: Console | None = None,
        host: str = "localhost",
        port: int = 6276,
        tls_cert_path: str | None = None,
        log_level: str = "INFO",
        write_mode: WriteMode = "async",
        stop_requested: Callable[[], bool] | None = None,
        dataset_registry: DatasetRegistry | None = None,
    ) -> None:
        self.console = console or Console(stderr=True)
        self.dataset_registry = dataset_registry or build_default_dataset_registry()
        self._stop_requested = stop_requested or (lambda: False)
        self._file_executor = FileSequenceExecutor(
            self.console,
            write_mode=write_mode,
        )
        self._rosbag_executor = RosbagSequenceExecutor(
            console=self.console,
            host=host,
            port=port,
            log_level=log_level,
            tls_cert_path=tls_cert_path,
            stop_requested=self._stop_requested,
        )

    def ingest_root(
        self,
        root: Path,
        client: MosaicoClient,
        dataset_index: int | None = None,
        dataset_total: int | None = None,
        selected_plugin_id: str | None = None,
    ) -> DatasetIngestionReport:
        dataset_start = time.monotonic()
        dataset_label = (
            f"[{dataset_index}/{dataset_total}] "
            if dataset_index and dataset_total
            else ""
        )

        if self._stop_requested():
            return self._build_interrupted_report(root, dataset_start)

        if not root.exists():
            return self._handle_missing_root(root, dataset_label, dataset_start)

        plugin, plugin_id, sequence_paths = self._discover_sequences(
            root, dataset_start, selected_plugin_id=selected_plugin_id
        )
        if isinstance(plugin, DatasetIngestionReport):
            return plugin

        report = DatasetIngestionReport(
            root=root,
            plugin_id=plugin_id,
            discovered=len(sequence_paths),
        )

        existing_sequences = self._get_existing_sequences(client, report)

        LOGGER.info(
            "%sDataset '%s' from %s with %d sequence(s)",
            dataset_label,
            plugin_id,
            root,
            len(sequence_paths),
        )
        LOGGER.info("Found %d existing sequence(s) on server", len(existing_sequences))

        if not sequence_paths:
            return self._finalize_empty_report(report, dataset_label, dataset_start)

        self._process_sequences(
            sequence_paths,
            plugin,
            client,
            existing_sequences,
            report,
        )

        report.duration_s = time.monotonic() - dataset_start
        report.finalize(
            interrupted=report.status == "interrupted" or self._stop_requested()
        )
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

    def _build_interrupted_report(
        self, root: Path, start_time: float
    ) -> DatasetIngestionReport:
        report = DatasetIngestionReport.interrupted_report(root=root)
        report.duration_s = time.monotonic() - start_time
        return report

    def _handle_missing_root(
        self, root: Path, label: str, start_time: float
    ) -> DatasetIngestionReport:
        report = DatasetIngestionReport.failed_report(
            root=root,
            error=f"Dataset root does not exist: {root}",
        )
        report.duration_s = time.monotonic() - start_time
        LOGGER.error("%sDataset root does not exist: %s", label, root)
        return report

    def _discover_sequences(
        self,
        root: Path,
        start_time: float,
        selected_plugin_id: str | None = None,
    ) -> tuple | DatasetIngestionReport:
        try:
            if selected_plugin_id is None:
                plugin = self.dataset_registry.resolve(root)
            else:
                plugin = self.dataset_registry.get(selected_plugin_id)
            plugin_id = getattr(plugin, "dataset_id", type(plugin).__name__)
            sequence_paths = list(plugin.discover_sequences(root))
            return plugin, plugin_id, sequence_paths
        except KeyError:
            return DatasetIngestionReport.failed_report(
                root=root,
                plugin_id=selected_plugin_id or "unresolved",
                error=f"Unknown dataset plugin '{selected_plugin_id}'.",
                duration_s=time.monotonic() - start_time,
            )
        except Exception:
            LOGGER.exception("Failed to resolve dataset root %s", root)
            return DatasetIngestionReport.failed_report(
                root=root,
                plugin_id="unresolved",
                error=f"Failed to resolve dataset root '{root}'.",
                duration_s=time.monotonic() - start_time,
            )

    def _get_existing_sequences(
        self, client: MosaicoClient, report: DatasetIngestionReport
    ) -> set[str]:
        try:
            return set(client.list_sequences())
        except Exception:
            LOGGER.exception(
                "Failed to list existing sequences; continuing without skip detection."
            )
            report.warnings.append(
                "Failed to list existing sequences; skip detection was disabled."
            )
            return set()

    def _finalize_empty_report(
        self, report: DatasetIngestionReport, label: str, start_time: float
    ) -> DatasetIngestionReport:
        LOGGER.warning("No sequences discovered under %s", report.root)
        report.duration_s = time.monotonic() - start_time
        report.remote_size_bytes = 0
        LOGGER.info(
            "%sCompleted dataset '%s' — discovered=0 ingested=0 skipped=0 failed=0 duration=%.2fs",
            label,
            report.plugin_id,
            report.duration_s,
        )
        return report

    def _process_sequences(
        self,
        sequence_paths: list[Path],
        plugin: DatasetPlugin,
        client: MosaicoClient,
        existing_sequences: set[str],
        report: DatasetIngestionReport,
    ) -> None:
        for index, sequence_path in enumerate(sequence_paths, start=1):
            if self._stop_requested():
                self._mark_report_interrupted(report)
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
                self._mark_report_interrupted(report)
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
                self._mark_report_interrupted(report)
                break

    def _mark_report_interrupted(self, report: DatasetIngestionReport) -> None:
        report.status = "interrupted"
        report.errors.append("Interrupted by user.")

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
            return self._build_sequence_error_result(
                sequence_name=sequence_path.name,
                local_size=local_size,
                error=f"Failed to create ingestion plan for '{sequence_path.name}': {exc}",
            )

        backend = getattr(plan, "backend", "file")

        if self._stop_requested():
            return self._build_sequence_interrupted_result(plan, local_size, backend)

        try:
            if isinstance(plan, RosbagSequenceDescriptor):
                ingested = self._rosbag_executor.ingest_sequence(
                    plan,
                    client=client,
                    existing_sequences=existing_sequences,
                )
            else:
                ingested = self._file_executor.ingest_sequence(
                    sequence_path,
                    plan,
                    client=client,
                    existing_sequences=existing_sequences,
                )
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            LOGGER.exception(
                "Sequence '%s' failed; continuing with the next sequence.",
                sequence_path.name,
            )
            return self._build_sequence_error_result(
                sequence_name=plan.sequence_name,
                local_size=local_size,
                error=f"Sequence '{plan.sequence_name}' failed: {exc}",
                backend=backend,
                plan=plan,
            )

        if self._stop_requested():
            return self._build_sequence_interrupted_result(plan, local_size, backend)

        return SequenceIngestionResult(
            sequence_name=plan.sequence_name,
            status="ingested" if ingested else "skipped",
            local_size_bytes=local_size,
            backend=backend,
            plan=plan,
        )

    def _build_sequence_error_result(
        self,
        sequence_name: str,
        local_size: int,
        error: str,
        backend: str | None = None,
        plan=None,
    ) -> SequenceIngestionResult:
        return SequenceIngestionResult(
            sequence_name=sequence_name,
            status="failed",
            local_size_bytes=local_size,
            backend=backend,
            plan=plan,
            error=error,
        )

    def _build_sequence_interrupted_result(
        self, plan, local_size: int, backend: str
    ) -> SequenceIngestionResult:
        return SequenceIngestionResult(
            sequence_name=plan.sequence_name,
            status="interrupted",
            local_size_bytes=local_size,
            backend=backend,
            plan=plan,
            error="Interrupted by user.",
        )

    def _get_local_sequence_size(self, sequence_path: Path) -> int:
        real_path = sequence_path
        episode_count = 1

        if "@@" in sequence_path.stem:
            real_stem = sequence_path.stem.split("@@")[0]
            real_path = sequence_path.with_name(f"{real_stem}{sequence_path.suffix}")

            cache = getattr(self, "_episode_count_cache", None)
            if cache is None:
                self._episode_count_cache: dict[Path, int] = {}
                cache = self._episode_count_cache

            if real_path in cache:
                episode_count = cache[real_path]
            else:
                try:
                    import pyarrow.parquet as pq

                    table = pq.read_table(real_path, columns=["episode_index"])
                    episode_count = max(1, table.column("episode_index").n_unique())
                except Exception:
                    LOGGER.warning(
                        "Could not count episodes in '%s'; using full file size.",
                        real_path.name,
                    )
                    episode_count = 1
                cache[real_path] = episode_count

        try:
            return real_path.stat().st_size // episode_count
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
