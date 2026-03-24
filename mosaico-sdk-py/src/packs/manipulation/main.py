import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from mosaicolabs import MosaicoClient, setup_sdk_logging
from packs.manipulation.runner.runner import ManipulationRunner

LOGGER = logging.getLogger(__name__)
MOSAICO_HOST = "localhost"
MOSAICO_PORT = 6726
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


def run_pipeline():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", required=True, help="Dataset path")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=LOG_LEVELS,
        help="Logging verbosity",
    )
    args = parser.parse_args()

    console = Console(stderr=True)
    configure_logging(args.log_level, console)
    dataset_root = Path(args.datasets)

    if not dataset_root.exists():
        LOGGER.error("Dataset root does not exist: %s", dataset_root)
        raise SystemExit(2)

    runner = ManipulationRunner(console=console)

    try:
        LOGGER.info("Starting manipulation ingestion from %s to %s:%s", dataset_root, MOSAICO_HOST, MOSAICO_PORT)
        
        with MosaicoClient.connect(MOSAICO_HOST, MOSAICO_PORT) as client:
            runner.ingest_root(dataset_root, client)
    except Exception:
        LOGGER.exception("Manipulation ingestion failed for %s", dataset_root)
        raise SystemExit(1)

    LOGGER.info("Manipulation ingestion completed for %s", dataset_root)


if __name__ == "__main__":
    run_pipeline()
