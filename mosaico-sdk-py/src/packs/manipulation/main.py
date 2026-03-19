import h5py
import argparse
from pathlib import Path

from mosaicolabs import MosaicoClient, OnErrorPolicy

from configs import SEQUENCE_METADATA, ROBOT_TOPICS_DATA
from custom_translator import (custom_translator)
from extract_video_frame import extract_video_frames


def sequences_stats():
    with MosaicoClient.connect("localhost", 6726) as client:
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
    # Open the connection with the Mosaico Client
    with MosaicoClient.connect("localhost", 6726) as client:
        # Parse command-line arguments to get the dataset path
        parser = argparse.ArgumentParser()
        parser.add_argument("--dataset", required=True, help="Path del dataset")
        args = parser.parse_args()

        for h5_file in sorted(Path(args.dataset).glob("*.h5")):
            with h5py.File(h5_file) as h5_dataset:
                # Start the Sequence Orchestrator
                with client.sequence_create(
                        sequence_name=h5_file.stem,
                        metadata=SEQUENCE_METADATA,
                        on_error=OnErrorPolicy.Delete
                ) as swriter:
                    writers = {}
                    
                    # Create topic writers for all topics defined in the configuration,
                    # and store them in a dictionary for later use.
                    for topic_name, topic_data in ROBOT_TOPICS_DATA.items():
                        writer = swriter.get_topic_writer(topic_name)

                        if writer is None:
                            writer = swriter.topic_create(
                                topic_name=topic_name,
                                metadata=topic_data["metadata"],
                                ontology_type=topic_data["ontology"],
                            )

                        writers[topic_name] = writer

                    # Read and publish samples topic by topic.
                    for topic_name, topic_data in ROBOT_TOPICS_DATA.items():
                        timestamps = h5_dataset[topic_data["timestamps"]][:]

                        # When source type is video, extract frames from the video dataset
                        # and publish each frame as a separate message.
                        if topic_data.get("source_type") == "video":
                            video_dataset_path = topic_data["fields"]["video"]
                            frames = extract_video_frames(h5_dataset, video_dataset_path, timestamps)

                            for i, payload in enumerate(frames):
                                try:
                                    msg = custom_translator(topic_name, payload)

                                    if msg is None:
                                        print(f"Skipping sample {i} in {h5_file.name} for topic {topic_name}")
                                        continue

                                    writers[topic_name].push(message=msg)
                                except Exception as e:
                                    print(f"Error processing sample {i} in {h5_file.name} for topic {topic_name}: {e}")
                            continue

                        # For other source types, build the raw payload for each sample 
                        # by reading the corresponding fields from the HDF5 dataset
                        topic_fields = {
                            field_name: h5_dataset[topic_path][:]
                            for field_name, topic_path in topic_data["fields"].items()
                        }

                        for i, ts in enumerate(timestamps):
                            try:
                                payload = {"timestamp": ts}

                                # Build the raw payload for the current sample
                                for key, values in topic_fields.items():
                                    payload[key] = values[i]

                                # Translate the raw payload into the target message format
                                msg = custom_translator(topic_name, payload)

                                if msg is None:
                                    print(f"Skipping sample {i} in {h5_file.name} for topic {topic_name}")
                                    continue

                                # Push the translated message to the corresponding topic
                                writers[topic_name].push(message=msg)
                            except Exception as e:
                                print(f"Error processing sample {i} in {h5_file.name} for topic {topic_name}: {e}")

                # All buffers are flushed and the sequence is committed when exiting the SequenceWriter 'with' block
                print("Successfully injected data from HDF5 dataset into Mosaico!")

    # Here the `MosaicoClient` context and all connections are closed


if __name__ == "__main__":
    run_pipeline()
    sequences_stats()
