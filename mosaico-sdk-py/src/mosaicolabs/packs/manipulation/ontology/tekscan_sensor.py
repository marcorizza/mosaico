from typing import List, Optional

import pyarrow as pa

from mosaicolabs import Serializable


class TekscanSensor(Serializable):
    __ontology_tag__ = "tekscan_sensor"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "values",
                pa.list_(pa.float64()),
                nullable=False,
                metadata={"description": "Values of the sensor array."},
            ),
            pa.field(
                "rows",
                pa.int64(),
                nullable=True,
                metadata={"description": "Number of rows in the sensor array."},
            ),
            pa.field(
                "cols",
                pa.int64(),
                nullable=True,
                metadata={"description": "Number of columns in the sensor array."},
            ),
        ]
    )

    values: List[float]
    rows: Optional[int] = None
    cols: Optional[int] = None
