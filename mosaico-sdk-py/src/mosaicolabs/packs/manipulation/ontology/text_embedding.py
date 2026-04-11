from typing import List

import pyarrow as pa

from mosaicolabs import Serializable


class TextEmbedding(Serializable):
    __ontology_tag__ = "text_embedding"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "values",
                pa.list_(pa.float32()),
                nullable=False,
                metadata={"description": "Values of the text embedding."},
            ),
        ]
    )

    values: List[float]
