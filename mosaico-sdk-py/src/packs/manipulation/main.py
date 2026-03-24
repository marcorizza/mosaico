import argparse
from pathlib import Path

from mosaicolabs import MosaicoClient
from packs.manipulation.runner import ManipulationRunner

MOSAICO_HOST = "localhost"
MOSAICO_PORT = 6726


def run_pipeline():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", required=True, help="Dataset path")
    args = parser.parse_args()

    dataset_root = Path(args.datasets)
    runner = ManipulationRunner()

    with MosaicoClient.connect(MOSAICO_HOST, MOSAICO_PORT) as client:
        runner.ingest_root(dataset_root, client)


if __name__ == "__main__":
    run_pipeline()
