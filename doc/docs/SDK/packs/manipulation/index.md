---
title: Manipulation Pack
description: An overview of the dataset orchestration suite for robotics and physical AI.
---

The **Manipulation Pack** is a curated collection of heterogeneous open-source robotic manipulation datasets, each individually studied, analyzed, and mapped into Mosaico's unified semantic ontology. Every dataset in this pack was manually inspected to identify its internal topics and data streams; custom ontologies were written specifically to represent the physical semantics of each source format — from HDF5 to Parquet, from TensorFlow Records to ROS bags.

The result is a single, ready-to-use ingestion suite where a `RobotJoint` topic originating from a ROS bag looks and behaves exactly like a `RobotJoint` topic coming from a DeepMind TFRecord. This is the core value proposition: proving that Mosaico acts as the universal standard for semantic sensor data description across deeply fragmented ecosystems.

??? question "In Depth Explanation"
    * **[Documentation: Data Models & Ontology](../../ontology.md)**
    * **[Documentation: The Writing Workflow](../../handling/writing.md)**
    * **[Documentation: The ROS Bridge](../../bridges/ros.md)**

### Basic Usage

!!! info "Infrastructure Prerequisite"
    Before running any manipulation pack flow, ensure your Mosaico infrastructure is active.
    Please refer to the **[Daemon Setup](../../../daemon/install.md)** for setting up the environment.

From your terminal, use the `mosaicolabs.packs manipulation` command followed by your dataset directories:

```bash
mosaicolabs.packs manipulation --datasets /path/to/dataset
```

### Configuration Options

The CLI supports several global flags to control the execution environment:

| Option | Default | Description |
| :--- | :--- | :--- |
| `--datasets` | Required | One or more dataset roots to ingest. |
| `--host` | `localhost` | The hostname of your Mosaico Server. |
| `--port` | `6726` | The Flight port of your Mosaico Server. |
| `--log-level` | `INFO` | Set verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `--write-mode` | `sync` | Topic execution mode for file-backed data (`sync` or `async`). |

### Supported Datasets

We provide built-in support for multiple open-source formats. We recommend exploring them in the following order to understand the pack's capabilities:

#### [Reassemble](https://researchdata.tuwien.ac.at/records/0ewrv-8cb44)

  * **Execution Backend**: File (HDF5)
  * **Primary Purpose**: Designed to seamlessly parse and stitch together multimodal, contact-rich robotic assembly sequences, translating complex sensory streams into structured episodes.

??? quote "Citation"
    Sliwowski, D. J., Jadav, S., Stanovcic, S., Orbik, J., Heidersberger, J., & Lee, D. (2025). REASSEMBLE: A Multimodal Dataset for Contact-rich Robotic Assembly and Disassembly (1.0.0) [Data set]. TU Wien. https://doi.org/10.48436/0ewrv-8cb44

#### [RT-1 (Fractal)](https://www.tensorflow.org/datasets/catalog/fractal20220817_data)

  * **Execution Backend**: File (TFDS)
  * **Primary Purpose**: Bypasses traditional TensorFlow overhead to natively unpack and inject episodic manipulations shaped by the Google RT-1 Transformer ontology.

??? quote "Citation"
    ```bibtex
    @article{brohan2022rt,
      title={Rt-1: Robotics transformer for real-world control at scale},
      author={Brohan, Anthony and Brown, Noah and Carbajal, Justice and Chebotar, Yevgen and Dabis, Joseph and Finn, Chelsea and Gopalakrishnan, Keerthana and Hausman, Karol and Herzog, Alex and Hsu, Jasmine and others},
      journal={arXiv preprint arXiv:2212.06817},
      year={2022}
    }
    ```

#### [LeRobot DROID](https://huggingface.co/datasets/lerobot/droid_1.0.1)

  * **Execution Backend**: File (Parquet)
  * **Primary Purpose**: Highly specialized to structurally expand massive, unified huggingface parquet architectures into distinct, logical manipulation episodes.

#### [MML](https://zenodo.org/records/6372438)

  * **Execution Backend**: Rosbag 
  * **Primary Purpose**: Secures ingestion of legacy Multimodal Sensory Learning records securely via the highly-performant generic ROS bridge.

??? quote "Citation"
    Prabhakar, A., Billard, A., & Reber, D. (2021). Multimodal Sensory Learning for Object Manipulation (v1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.6372438

### Ready to start?

If your robotic data is saved in a proprietary format and isn't supported out-of-the-box, the pack is fully extensible. 
We recommend jumping directly to the **[Integrating a Custom Dataset](./integrating.md)** guide to build your own Plugin and Adapter.
