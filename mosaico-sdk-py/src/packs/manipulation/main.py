import argparse
from pathlib import Path

from mosaicolabs import MosaicoClient
from packs.manipulation.runner import ManipulationRunner

MOSAICO_HOST = "localhost"
MOSAICO_PORT = 6726


def sequences_stats():
    with MosaicoClient.connect(MOSAICO_HOST, MOSAICO_PORT) as client:
        sequences = client.list_sequences()
        for sequence in sequences:
            try:
                seq_handler = client.sequence_handler(sequence)
                # Print sequence metadata
                print(f"Sequence: {seq_handler.name}")
                print(f"• Registered Topics: {seq_handler.topics}")
                print(f"• User Metadata: {seq_handler.user_metadata}")

                # Analyze temporal bounds (earliest and latest timestamps across all sensors)
                # Timestamps are consistently handled in nanoseconds
                start, end = seq_handler.timestamp_ns_min, seq_handler.timestamp_ns_max
                print(f"• Duration (ns): {end - start}")

                # Access structural info from the server
                size_mb = seq_handler.total_size_bytes / (1024 * 1024)
                print(f"• Total Size: {size_mb:.2f} MB")
                print(f"• Created At: {seq_handler.created_datetime}")
            except Exception as e:
                print(f"Error retrieving sequence {sequence}: {e}")


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
    sequences_stats()
