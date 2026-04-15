from typing import Optional

from mosaicolabs import MosaicoField, MosaicoType, Serializable


class TekscanSensor(Serializable):
    __ontology_tag__ = "tekscan_sensor"

    values: MosaicoType.list_(MosaicoType.float64) = MosaicoField(
        description="Values of the sensor array."
    )
    rows: Optional[MosaicoType.int64] = MosaicoField(
        default=None, description="Number of rows in the sensor array."
    )
    cols: Optional[MosaicoType.int64] = MosaicoField(
        default=None, description="Number of columns in the sensor array."
    )
