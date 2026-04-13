import argparse
import logging
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt

from mosaicolabs import MosaicoClient, setup_sdk_logging
from mosaicolabs.packs.configs import MOSAICO_HOST, MOSAICO_PORT
from mosaicolabs.packs.manipulation.contracts import DatasetPlugin, WriteMode
from mosaicolabs.packs.manipulation.datasets import (
    DatasetRegistry,
    build_default_dataset_registry,
)
from mosaicolabs.packs.manipulation.runner.reporters.reports import (
    DatasetIngestionReport,
    RunIngestionReport,
)
from mosaicolabs.packs.manipulation.runner.reporters.upload_reporter import (
    UploadReporter,
)
from mosaicolabs.packs.manipulation.runner.runner import ManipulationRunner
from mosaicolabs.packs.manipulation.runner.stop_controller import StopController

LOGGER = logging.getLogger(__name__)
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
WRITE_MODES: tuple[WriteMode, ...] = ("sync", "async")


@dataclass(frozen=True)
class DatasetSelection:
    plugin_id: str | None
    warning: str | None = None


def configure_logging(
    level: str, console: Console, log_file: Path | None = None
) -> None:
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

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logging.getLogger("mosaicolabs").addHandler(file_handler)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
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
    parser.add_argument(
        "--log-file",
        default=None,
        type=Path,
        metavar="FILE",
        help="Optional path to a log file. Logs are written to both console and file.",
    )
    parser.add_argument(
        "--write-mode",
        default="sync",
        choices=WRITE_MODES,
        metavar="MODE",
        help=(
            "Topic ingestion mode for file-backed datasets: 'sync' is the "
            "default; 'async' keeps per-topic threads over a shared SDK client."
        ),
    )
    return parser.parse_args(argv)


def _is_interactive_terminal(console: Console) -> bool:
    return sys.stdin.isatty() and console.is_terminal


def _prompt_for_plugin_selection(
    root: Path,
    available_plugins: list[DatasetPlugin],
    console: Console,
) -> DatasetSelection:
    console.print()
    console.print(f"[bold]Select plugin for[/bold] [cyan]{root}[/cyan]")
    for index, plugin in enumerate(available_plugins, start=1):
        console.print(f"  {index}. [bold]{plugin.dataset_id}[/bold]")

    skip_choice = len(available_plugins) + 1
    console.print(f"  {skip_choice}. [bold]none[/bold] [dim](skip dataset)[/dim]")

    choice = Prompt.ask(
        "Plugin",
        choices=[str(index) for index in range(1, skip_choice + 1)],
        console=console,
    )

    if choice == str(skip_choice):
        warning = f"Dataset root '{root}' was skipped by user selection."
        return DatasetSelection(
            plugin_id=None,
            warning=warning,
        )

    selected_plugin = available_plugins[int(choice) - 1]
    return DatasetSelection(
        plugin_id=selected_plugin.dataset_id,
    )


def _select_dataset_plugins(
    dataset_roots: list[Path],
    registry: DatasetRegistry,
    console: Console,
) -> dict[Path, DatasetSelection]:
    if not _is_interactive_terminal(console):
        raise RuntimeError(
            "Manipulation ingestion requires an interactive TTY to select a dataset "
            "plugin for each dataset root."
        )

    selections: dict[Path, DatasetSelection] = {}
    available_plugins = registry.all()
    if not available_plugins:
        raise RuntimeError(
            "No dataset plugins are registered for the manipulation pack."
        )

    for dataset_root in dataset_roots:
        if not dataset_root.exists():
            continue

        selections[dataset_root] = _prompt_for_plugin_selection(
            dataset_root,
            available_plugins,
            console,
        )

    return selections


def run_pipeline(args: argparse.Namespace) -> int:
    console = Console(stderr=True)
    configure_logging(args.log_level, console, log_file=args.log_file)
    dataset_registry = build_default_dataset_registry()

    try:
        dataset_selections = _select_dataset_plugins(
            args.datasets,
            dataset_registry,
            console,
        )
    except RuntimeError as exc:
        LOGGER.error("%s", exc)
        return 1

    stop_controller = StopController()
    reporter = UploadReporter(console)
    runner = ManipulationRunner(
        console=console,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        write_mode=args.write_mode,
        stop_requested=stop_controller,
        dataset_registry=dataset_registry,
    )

    dataset_reports: list[DatasetIngestionReport] = []
    run_start = time.monotonic()
    reporter.print_run_header(args.datasets, args.host, args.port, args.write_mode)

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

            selection = dataset_selections[dataset_root]
            if selection.plugin_id is None:
                report = DatasetIngestionReport.skipped_report(
                    root=dataset_root,
                    plugin_id=selection.plugin_id or "none",
                    warning=selection.warning
                    or f"Dataset root '{dataset_root}' was skipped.",
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
                        selected_plugin_id=selection.plugin_id,
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
