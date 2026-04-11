from typing import List

import pyarrow as pa

from mosaicolabs import Serializable


class TerminateEpisode(Serializable):
    __ontology_tag__ = "terminate_episode"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "terminate_episode",
                pa.list_(value_type=pa.int32(), list_size=3),
                nullable=False,
                metadata={
                    "description": (
                        "RT-1 terminate signal encoded as a 3-element int32 vector in the order "
                        "[terminate, continue, undocumented]."
                    )
                },
            ),
        ]
    )

    terminate_episode: List[int]
