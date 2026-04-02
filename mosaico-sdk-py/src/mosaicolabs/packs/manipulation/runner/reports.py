from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from mosaicolabs.packs.manipulation.contracts import IngestionDescriptor

SequenceResultStatus = Literal["ingested", "skipped", "failed", "interrupted"]
DatasetReportStatus = Literal["success", "partial_failure", "failed", "interrupted"]
RunReportStatus = Literal["success", "partial_failure", "interrupted"]


@dataclass
class SequenceIngestionResult:
    sequence_name: str
    status: SequenceResultStatus
    local_size_bytes: int = 0
    backend: str | None = None
    plan: IngestionDescriptor | None = None
    error: str | None = None


@dataclass
class DatasetIngestionReport:
    root: Path
    plugin_id: str
    status: DatasetReportStatus = "success"
    discovered: int = 0
    ingested: int = 0
    skipped: int = 0
    failed: int = 0
    backend_counts: dict[str, int] = field(default_factory=dict)
    local_size_bytes: int = 0
    remote_size_bytes: int | None = None
    duration_s: float = 0.0
    errors: list[str] = field(default_factory=list)
    ingested_plans: list[IngestionDescriptor] = field(default_factory=list)

    @classmethod
    def failed_report(
        cls,
        root: Path,
        error: str,
        plugin_id: str = "unresolved",
        duration_s: float = 0.0,
    ) -> "DatasetIngestionReport":
        report = cls(
            root=root,
            plugin_id=plugin_id,
            status="failed",
            duration_s=duration_s,
        )
        report.errors.append(error)
        return report

    @classmethod
    def interrupted_report(
        cls,
        root: Path,
        error: str = "Interrupted by user.",
        plugin_id: str = "unresolved",
        duration_s: float = 0.0,
    ) -> "DatasetIngestionReport":
        report = cls(
            root=root,
            plugin_id=plugin_id,
            status="interrupted",
            duration_s=duration_s,
        )
        report.errors.append(error)
        return report

    def record_sequence(self, result: SequenceIngestionResult) -> None:
        self.local_size_bytes += result.local_size_bytes

        if result.backend:
            self.backend_counts[result.backend] = (
                self.backend_counts.get(result.backend, 0) + 1
            )

        if result.status == "ingested":
            self.ingested += 1
            if result.plan is not None:
                self.ingested_plans.append(result.plan)
        elif result.status == "skipped":
            self.skipped += 1
        elif result.status == "failed":
            self.failed += 1

        if result.error:
            self.errors.append(result.error)

    def finalize(self, interrupted: bool = False) -> None:
        if interrupted or self.status == "interrupted":
            self.status = "interrupted"
            return

        if self.status == "failed" and self.failed == 0:
            return

        if self.failed > 0:
            self.status = (
                "partial_failure"
                if (self.ingested > 0 or self.skipped > 0)
                else "failed"
            )
            return

        self.status = "success"


@dataclass
class RunIngestionReport:
    datasets: list[DatasetIngestionReport] = field(default_factory=list)
    duration_s: float = 0.0
    status: RunReportStatus = "success"

    @classmethod
    def from_dataset_reports(
        cls,
        dataset_reports: list[DatasetIngestionReport],
        duration_s: float,
        interrupted: bool = False,
    ) -> "RunIngestionReport":
        if interrupted or any(
            report.status == "interrupted" for report in dataset_reports
        ):
            status: RunReportStatus = "interrupted"
        elif any(
            report.status in {"failed", "partial_failure"} for report in dataset_reports
        ):
            status = "partial_failure"
        else:
            status = "success"

        return cls(datasets=dataset_reports, duration_s=duration_s, status=status)

    @property
    def discovered(self) -> int:
        return sum(report.discovered for report in self.datasets)

    @property
    def ingested(self) -> int:
        return sum(report.ingested for report in self.datasets)

    @property
    def skipped(self) -> int:
        return sum(report.skipped for report in self.datasets)

    @property
    def failed(self) -> int:
        return sum(report.failed for report in self.datasets)

    @property
    def local_size_bytes(self) -> int:
        return sum(report.local_size_bytes for report in self.datasets)

    @property
    def remote_size_bytes(self) -> int | None:
        remote_sizes = [report.remote_size_bytes for report in self.datasets]
        if any(size is None for size in remote_sizes):
            return None
        return sum(size or 0 for size in remote_sizes)

    @property
    def backend_counts(self) -> dict[str, int]:
        aggregated: dict[str, int] = {}
        for report in self.datasets:
            for backend, count in report.backend_counts.items():
                aggregated[backend] = aggregated.get(backend, 0) + count
        return aggregated
