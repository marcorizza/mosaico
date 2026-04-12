---
title: Manipulation Pack
description: CLI guide for ingesting manipulation datasets into Mosaico.
---

This guide describes the **Manipulation Pack**, the dataset-oriented CLI provided by the Mosaico SDK for recurring ingestion workflows.


By following this page, you will understand how to:

1. **Run The Pack** from the SDK packs CLI
2. **Select The Right Plugin** for each dataset root
3. **Choose The Ingestion Mode** for file-backed datasets
4. **Interpret The Execution Flow** and the final summaries

## What The Pack Does

The Manipulation Pack is built for curated robotics datasets. It discovers sequences, builds an ingestion plan, uploads the resulting data to Mosaico, and reports the outcome at dataset and run level.

The pack supports both:

* **File Backed Datasets**
* **Rosbag Backed Datasets**

If you need direct programmatic control over `SequenceWriter` and `TopicWriter`, refer to the [writing workflow](../../handling/writing.md).

## Basic Usage

Run the pack through the shared packs entry point:

```bash
mosaicolabs.packs manipulation --datasets /path/to/dataset
```

Example with explicit host, port, and write mode:

```bash
mosaicolabs.packs manipulation \
  --datasets /data/reassemble \
  --host localhost \
  --port 6726 \
  --log-level INFO \
  --write-mode sync
```

!!! note "Interactive Selection"
    The pack currently requires an interactive terminal. For each dataset root, it prompts the operator to choose the dataset plugin that should be used for ingestion.

## CLI Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `--datasets DIR [DIR ...]` | Required | One or more dataset roots to ingest |
| `--host ADDR` | `localhost` | Target Mosaico server host |
| `--port PORT` | `6726` | Target Mosaico server Flight port |
| `--log-level LEVEL` | `INFO` | Logging verbosity |
| `--log-file FILE` | Not Set | Optional file that mirrors the console logs |
| `--write-mode MODE` | `async` | Topic ingestion mode for file-backed datasets |

## Supported Dataset Plugins

The default registry currently includes three plugins.

### `reassemble`

* **Reference**: [TU Wien Research Data](https://researchdata.tuwien.ac.at/records/0ewrv-8cb44)
* **Backend**: File
* **Discovery**: `*.h5`
* **Sequence Naming**: `reassemble_<file_stem>`

This plugin reads HDF5 datasets through the internal `HDF5Reader`. It builds explicit topic descriptors for video, audio, events, and robot state streams.

??? quote "Citation"
    Sliwowski, D. J., Jadav, S., Stanovcic, S., Orbik, J., Heidersberger, J., & Lee, D. (2025). REASSEMBLE: A Multimodal Dataset for Contact-rich Robotic Assembly and Disassembly (1.0.0) [Data set]. TU Wien. https://doi.org/10.48436/0ewrv-8cb44

### `fractal_rt1`

* **Reference**: [TensorFlow Datasets Catalog](https://www.tensorflow.org/datasets/catalog/fractal20220817_data)
* **Backend**: File
* **Discovery**: `dataset_info.json`
* **Sequence Naming**: `fractal_<dataset_name>_ep<episode_index>`

This plugin reads TensorFlow Datasets through the `TFDSReader`. It iterates episodes and translates observations and actions to Mosaico messages.

??? quote "Citation"
    ```bibtex
    @article{brohan2022rt,
      title={Rt-1: Robotics transformer for real-world control at scale},
      author={Brohan, Anthony and Brown, Noah and Carbajal, Justice and Chebotar, Yevgen and Dabis, Joseph and Finn, Chelsea and Gopalakrishnan, Keerthana and Hausman, Karol and Herzog, Alex and Hsu, Jasmine and others},
      journal={arXiv preprint arXiv:2212.06817},
      year={2022}
    }
    ```

### `mml`

* **Reference**: [Zenodo](https://zenodo.org/records/6372438)
* **Backend**: Rosbag
* **Discovery**: `*.bag`
* **Sequence Naming**: `mml_<file_stem>`

This plugin validates the bag through a signature set of ROS topics, then delegates ingestion to the ROS bridge executor.

??? quote "Citation"
    Prabhakar, A., Billard, A., & Reber, D. (2021). Multimodal Sensory Learning for Object Manipulation (v1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.6372438

### `droid`

* **Reference**: [Hugging Face](https://huggingface.co/datasets/lerobot/droid_1.0.1)
* **Backend**: File
* **Discovery**: Recursive `*.parquet`
* **Sequence Naming**: `droid_<parquet_stem>_ep<episode_index>`

This plugin expands one physical parquet file into multiple logical sequences, one for each `episode_index`.

## Execution Flow

At a high level, the pack executes the following steps:

1. **Parse CLI Arguments**
2. **Configure Logging**
3. **Build The Dataset Registry**
4. **Prompt For Plugin Selection**
5. **Discover Sequences**
6. **Build Per-Sequence Ingestion Plans**
7. **Run The Matching Executor**
8. **Print Dataset And Run Summaries**

## File-Backed Ingestion

File-backed datasets use `SequenceDescriptor` plans and are executed by the `FileSequenceExecutor`.

For each sequence, the file executor:

* **Creates The Destination Sequence**
* **Prepares Topic Writers**
* **Resolves Topic Adapters**
* **Computes Progress Totals**
* **Runs Topic Ingestion**

### Write Modes

The `--write-mode` flag controls how file topics are executed.

#### `async`

`async` is the default mode. It uses a `ThreadPoolExecutor` and keeps per-topic parallelism.

Use this mode when:

* **You Want Maximum Throughput**
* **Your Host Has Enough Memory And CPU Headroom**
* **The Dataset Benefits From Parallel Topic Processing**

#### `sync`

`sync` uses the same ingestion pipeline and the same adapters, but processes topics sequentially.

Use this mode when:

* **You Need Lower Peak Memory Usage**
* **You Want A Simpler Debugging Profile**
* **Parallel Video Decoding Is Too Expensive On The Client Host**

!!! note "Scope Of The Flag"
    `--write-mode` applies only to file-backed ingestion. Rosbag-backed execution is delegated to the ROS bridge and is not controlled by this option.

## Rosbag-Backed Ingestion

Rosbag-backed datasets use `RosbagSequenceDescriptor` plans and are executed by the `RosbagSequenceExecutor`.

The executor:

* **Resolves Requested Topics Against The Bag**
* **Skips Missing Topics With Warnings**
* **Applies Adapter Overrides When Needed**
* **Builds A `ROSInjectionConfig`**
* **Runs The `RosbagInjector`**

If none of the declared topics are available in the bag, the sequence is skipped.

## Sequence Naming And Metadata

Each plugin is responsible for defining:

* **The Sequence Name**
* **The Sequence Metadata**
* **The Topics Or Rosbag Selections To Ingest**

This is intentional. The pack provides the orchestration layer, while the plugin owns the dataset semantics.

Examples:

* **Reassemble** stores `dataset_id`, `ingestion_backend`, and `source_file`
* **MML** also stores `source_path`
* **DROID** stores `episode_index` and may enrich metadata from parquet columns
* **Fractal** stores `episode_index` and `estimated_local_size_bytes`

## Next Step

If you need to add support for a new dataset family, continue with the [integration guide](./integrating.md).
