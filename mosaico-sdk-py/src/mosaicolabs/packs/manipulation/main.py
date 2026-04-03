import argparse
import logging
import time
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from mosaicolabs import MosaicoClient, setup_sdk_logging
from mosaicolabs.packs.configs import MOSAICO_HOST, MOSAICO_PORT
from mosaicolabs.packs.manipulation.runner.reports import (
    DatasetIngestionReport,
    RunIngestionReport,
)
from mosaicolabs.packs.manipulation.runner.runner import ManipulationRunner
from mosaicolabs.packs.manipulation.runner.stop_controller import StopController
from mosaicolabs.packs.manipulation.runner.upload_reporter import UploadReporter

LOGGER = logging.getLogger(__name__)
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def configure_logging(level: str, console: Console) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                show_time=True,
                show_path=True,
                rich_tracebacks=True,
                log_time_format="[%X]",
            )
        ],
        force=True,
    )
    setup_sdk_logging(level=level, pretty=True, console=console)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest manipulation datasets into Mosaico.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        type=Path,
        required=True,
        metavar="DIR",
        help="One or more dataset roots to ingest.",
    )
    parser.add_argument(
        "--host", 
        default=MOSAICO_HOST, 
        metavar="ADDR", 
        help="Mosaico server host",
    )
    parser.add_argument(
        "--port",
        default=MOSAICO_PORT,
        type=int,
        metavar="PORT",
        help="Mosaico server port",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=LOG_LEVELS,
        metavar="LEVEL",
        help=f"Logging verbosity (choices: {', '.join(LOG_LEVELS)})",
    )
    return parser.parse_args()


def run_pipeline(args: argparse.Namespace) -> int:
    console = Console(stderr=True)
    configure_logging(args.log_level, console)

    stop_controller = StopController()
    reporter = UploadReporter(console)
    runner = ManipulationRunner(
        console=console,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        stop_requested=stop_controller,
    )

    dataset_reports: list[DatasetIngestionReport] = []
    run_start = time.monotonic()
    reporter.print_run_header(args.datasets, args.host, args.port)

    stop_controller.install()
    try:
        for index, dataset_root in enumerate(args.datasets, start=1):
            if stop_controller.stop_requested:
                break

            dataset_start = time.monotonic()

            if not dataset_root.exists():
                LOGGER.error("Dataset root does not exist: %s", dataset_root)
                report = DatasetIngestionReport.failed_report(
                    root=dataset_root,
                    error=f"Dataset root does not exist: {dataset_root}",
                    duration_s=time.monotonic() - dataset_start,
                )
                dataset_reports.append(report)
                reporter.print_dataset_summary(report)
                continue

            try:
                with MosaicoClient.connect(
                    host=args.host,
                    port=args.port,
                ) as client:
                    report = runner.ingest_root(
                        dataset_root,
                        client,
                        dataset_index=index,
                        dataset_total=len(args.datasets),
                    )
                    dataset_reports.append(report)
                    reporter.print_dataset_summary(report)
            except KeyboardInterrupt:
                stop_controller.request_stop()
                report = DatasetIngestionReport.interrupted_report(
                    root=dataset_root,
                    duration_s=time.monotonic() - dataset_start,
                )
                dataset_reports.append(report)
                reporter.print_dataset_summary(report)
                break
            except Exception:
                LOGGER.exception("Manipulation ingestion failed for %s", dataset_root)
                report = DatasetIngestionReport.failed_report(
                    root=dataset_root,
                    error=f"Dataset ingestion failed for '{dataset_root}'.",
                    duration_s=time.monotonic() - dataset_start,
                )
                dataset_reports.append(report)
                reporter.print_dataset_summary(report)
                continue
    finally:
        stop_controller.restore()

    run_report = RunIngestionReport.from_dataset_reports(
        dataset_reports,
        duration_s=time.monotonic() - run_start,
        interrupted=stop_controller.stop_requested,
    )
    reporter.print_run_summary(run_report)

    if run_report.status == "interrupted":
        LOGGER.warning(
            "Manipulation ingestion interrupted after %s",
            _format_duration(run_report.duration_s),
        )
        return 130

    if run_report.status == "partial_failure":
        LOGGER.warning(
            "Manipulation ingestion completed with failures in %s",
            _format_duration(run_report.duration_s),
        )
        return 1

    LOGGER.info(
        "✓ Manipulation ingestion completed in %s (%.2f seconds)",
        _format_duration(run_report.duration_s),
        run_report.duration_s,
    )
    return 0


def _format_duration(duration_s: float) -> str:
    total_seconds = max(0, int(duration_s))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def main() -> int:
    return run_pipeline(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
