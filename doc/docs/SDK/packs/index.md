---
title: Packs
description: Why Mosaico is the PDF for Robotics and the ultimate solution to the data plumbing nightmare.
---

# Packs

Mosaico Packs are ready-to-use data ingestion pipelines designed specifically for Physical AI and Robotics. 

Each Pack maps internal data streams from multiple different datasets into a single unified ontology. This allows you to instantly run powerful cross-dataset queries on deeply heterogeneous formats using the Mosaico SDK, completely eliminating the need to write custom parsers.

## Available Packs

<div class="grid cards" markdown>

-   :material-robot-industrial:{ .lg .middle } __Manipulation Pack__

    ---

    Integrated ingestion suite for robotic manipulation. Instantly parse DROID, RT-1, REASSEMBLE, and MML.

    [:octicons-arrow-right-24: Manipulation Pack](./manipulation/index.md)

-   :material-code-tags:{ .lg .middle } __Build Your Own__

    ---

    The Mosaico SDK is fully extensible. Build custom pipeline plugins for your proprietary sensor formats.

    [:octicons-arrow-right-24: Build Your Own](https://github.com/mosaico-labs/mosaico)

</div>

*(More open-source packs will be added as the ecosystem grows)*

---

## The plumbing nightmare we accepted as normal

We like writing software, but doing data plumbing is not writing software. Today, the Physical AI sector is plagued by a silent, massive roadblock.

Every research team and hardware platform records data differently. We have legacy ROS `.bag` files that seem to belong to another era. We have complex HDF5 blocks, nested Parquets, and heavy TFRecords with obscure structures. When engineers try to consolidate these datasets to train universal foundation models, they end up spending 80% of their time writing ingestion scripts. Dealing with corrupted timestamps. Fighting mismatched coordinate frames. Unraveling chaotic serialization schemas.

This became the daily routine. The focus shifted from actual machine learning, to endless data wrangling. We accepted this complexity as normal, but it's not.

## Mosaico as the "PDF for Robotics"

In the early days of personal computers, sharing a document was a chaotic mess of proprietary formats. You know the story. Then the PDF was invented. It didn't matter what tool created the document; once it was compiled to a PDF, any machine could read it flawlessly.

Mosaico does exactly this for robotics. And it does it going fast.

Mosaico provides a standardized, extremely high-performance underlying data representation that unifies all modalities: video, audio, text, semantics, robot states, and events. Once your robotic telemetry is ingested into Mosaico, it becomes universally queryable. Instantly streamable. Completely agnostic to the custom sensors that originally generated it. This is not just a nice abstraction: it is a fundamental paradigm shift.