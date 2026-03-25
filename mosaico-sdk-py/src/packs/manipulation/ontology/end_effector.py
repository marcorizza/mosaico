from typing import List

import pyarrow as pa

from mosaicolabs import Serializable, HeaderMixin


class EndEffector(Serializable, HeaderMixin):
    __ontology_tag__ = "end_effector"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "efforts",
                pa.list_(pa.float64()),
                nullable=False,
            ),
            pa.field(
                "positions",
                pa.list_(pa.float64()),
                nullable=False,
            ),
            pa.field(
                "velocities",
                pa.list_(pa.float64()),
                nullable=False,
            ),
        ]
    )
    
    efforts: List[float]
    positions: List[float]
    velocities: List[float]
