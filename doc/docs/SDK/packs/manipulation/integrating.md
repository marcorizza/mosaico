---
title: Integrating a Dataset
description: How to add a new dataset plugin to the Manipulation Pack.
---

This guide explains how to extend the Manipulation Pack with support for a new dataset format.

!!! abstract "Development Requirements"
    **Integration work requires the full SDK source tree.**

    The pre-compiled package does not expose the internal development layers. To add or modify dataset plugins, iterators, adapters, or registries, you must:

    * **Clone the source:** [**`mosaico-labs/mosaico`**](https://github.com/mosaico-labs/mosaico.git)
    * **Work locally:** Develop directly within the cloned repository environment.

By following this page, you will learn how to:

1. **Choose The Right Backend**
2. **Implement A Dataset Plugin**
3. **Read Raw Data Through Iterators**
4. **Translate Payloads Through Adapters**
5. **Register The New Components**

## Integration Model

The Manipulation Pack keeps responsibilities narrow:

* **A Dataset Plugin** detects a root, discovers sequences, and builds an ingestion plan
* **Iterators** read raw records from the source format
* **Adapters** convert raw payload dictionaries into Mosaico `Message` objects
* **Registries** make plugins and adapters discoverable at runtime

This split is important. It keeps the ingestion plan declarative and makes each part easier to test.

## Step 1: Choose The Backend

Start by deciding whether the dataset should use the file executor or the rosbag executor.

### File-Backed Datasets

Use `SequenceDescriptor` when the dataset is read directly from files such as:

* **HDF5**
* **Parquet**
* **Custom Binary Files**
* **Structured Per Sequence Directories**
* **TensorFlow Datasets (TFDS)**

In this model, the plugin returns a list of `TopicDescriptor` objects.

### Rosbag-Backed Datasets

Use `RosbagSequenceDescriptor` when the source already maps naturally to ROS topics and the ROS bridge can execute the ingestion.

In this model, the plugin returns:

* **The Bag Path**
* **The Sequence Name**
* **The Sequence Metadata**
* **The Default Topics**
* **The Adapter Overrides**

## Step 2: Implement The Dataset Plugin

Every dataset plugin must satisfy the `DatasetPlugin` protocol:

```python
class DatasetPlugin(Protocol):
    dataset_id: str

    def supports(self, root: Path) -> bool: ...
    def discover_sequences(self, root: Path) -> Iterable[Path]: ...
    def create_ingestion_plan(self, sequence_path: Path) -> IngestionDescriptor: ...
```

### `dataset_id`

Choose a stable identifier. It is used in:

* **Operator Prompts**
* **Sequence Names**
* **Sequence Metadata**
* **Adapter Id Prefixes**

### `supports(root)`

Keep this method fast and deterministic.

Good patterns include:

* **Checking For `*.h5`**
* **Checking For `*.bag`**
* **Scanning For Recursive Parquet Files**
* **Validating A Small Signature Of Required Topics Or Columns**
* **Checking For `dataset_info.json` (TFDS)**

Avoid expensive full-dataset reads unless they are necessary for reliable detection.

### `discover_sequences(root)`

Return the logical sequences contained in the dataset root.

Simple datasets usually map one file to one sequence:

```python
def discover_sequences(self, root: Path) -> list[Path]:
    return sorted(root.glob("*.h5"))
```

More complex datasets may expand one physical file into multiple logical sequences. The DROID and Fractal RT-1 plugins are the main examples in the current codebase.

### `create_ingestion_plan(sequence_path)`

This is the core method of the plugin. It returns either:

* **A `SequenceDescriptor`**
* **A `RosbagSequenceDescriptor`**

For file-backed plugins, this method defines:

* **The Sequence Name**
* **The Sequence Metadata**
* **The Topics To Ingest**
* **Any Missing Path Validation Logic**

## Step 3: Build A File Plan

For file-backed datasets, the usual workflow is:

1. **Identify The Logical Sequence**
2. **Define The Sequence Metadata**
3. **Define The Topics**
4. **Return A `SequenceDescriptor`**

Example:

```python
return SequenceDescriptor(
    sequence_name=f"{self.dataset_id}_{sequence_path.stem}",
    sequence_metadata={
        "dataset_id": self.dataset_id,
        "ingestion_backend": "file",
        "source_file": sequence_path.name,
    },
    topics=[
        TopicDescriptor(
            topic_name="/camera/front",
            ontology_type=CompressedImage,
            adapter_id=f"{self.dataset_id}.video_frame",
            payload_iter=iter_video_frames(...),
            message_count=count_video_frames(...),
            required_paths=("camera/front", "timestamps/front"),
        ),
    ],
)
```

### Naming Guidelines

Keep sequence names:

* **Stable**
* **Reproducible**
* **Easy To Trace Back To The Source**

Common ingredients are:

* **The Dataset Family**
* **The Source File Stem**
* **An Episode Suffix When Needed**

### Metadata Guidelines

At minimum, store enough information to trace the uploaded sequence back to the original source.

Useful defaults are:

* **`dataset_id`**
* **`ingestion_backend`**
* **`source_file`**
* **Source Specific Identifiers Such As `episode_index`**
* **`estimated_local_size_bytes` For Plan Precalculation**

If the source contains valuable semantic metadata, attach it during plan construction.

## Step 4: Implement Iterators

Keep raw I/O outside the plugin and move it into dedicated iterator helpers.

This keeps `create_ingestion_plan()` compact and readable.

The Reassemble dataset is a good reference. Its iterators expose factories such as:

* **`iter_records(...)`**
* **`iter_video_frames(...)`**
* **`iter_event_frames(...)`**
* **`iter_audio(...)`**

Each factory returns a callable shaped like:

```python
Callable[[Path], Iterable[dict]]
```

That callable is stored in the `payload_iter` field of a `TopicDescriptor`.

## Step 5: Implement Adapters

Iterators yield raw dictionaries. Adapters turn those dictionaries into Mosaico ontology messages.

All adapters inherit from `BaseAdapter`:

```python
class BaseAdapter(ABC):
    adapter_id: str
    ontology_type: type

    @classmethod
    @abstractmethod
    def translate(cls, payload: dict):
        ...
```

Example:

```python
class MyVideoFrameAdapter(BaseAdapter):
    adapter_id = "mydataset.video_frame"
    ontology_type = CompressedImage

    @classmethod
    def translate(cls, payload: dict) -> Message:
        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=CompressedImage(
                data=payload["image"],
                format=ImageFormat.JPEG,
            ),
        )
```

Keep adapters focused on semantic translation.

Do not put file reads or dataset traversal in the adapter.

## Step 6: Handle Missing Source Paths

If some inputs are optional or inconsistently present, declare:

* **`required_paths`** on each `TopicDescriptor`
* **`find_missing_paths(...)`** on the `SequenceDescriptor`

This allows the executor to:

* **Detect Missing Inputs Early**
* **Warn The Operator**
* **Create The Topic As Empty Instead Of Failing Immediately**

This pattern is already used by the Reassemble and DROID plugins.

## Step 7: Register The Plugin

After implementing the plugin, register it in the default dataset registry:

```python
def build_default_dataset_registry() -> DatasetRegistry:
    registry = DatasetRegistry()
    registry.register(ReassemblePlugin())
    registry.register(MMLPlugin())
    registry.register(DROIDPlugin())
    registry.register(MyDatasetPlugin())
    return registry
```

Without this step, the plugin will not appear in the CLI selection prompt.

## Step 8: Register The Adapters

If the plugin introduces new adapter ids, register the adapter classes in the default adapter registry:

```python
def build_default_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    ...
    registry.register(MyDatasetVideoFrameAdapter)
    registry.register(MyDatasetPoseAdapter)
    return registry
```

If an adapter id is missing, ingestion fails when topic writers are prepared.
