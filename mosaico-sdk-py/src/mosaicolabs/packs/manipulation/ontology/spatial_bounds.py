import pyarrow as pa

from mosaicolabs import Serializable, Vector3d


class Vector3dBounds(Serializable):
    __ontology_tag__ = "vector3d_bounds"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "min",
                Vector3d.__msco_pyarrow_struct__,
                nullable=False,
                metadata={"description": "Minimum vector limits."},
            ),
            pa.field(
                "max",
                Vector3d.__msco_pyarrow_struct__,
                nullable=False,
                metadata={"description": "Maximum vector limits."},
            ),
        ]
    )

    min: Vector3d
    max: Vector3d


class Vector3dFrame(Serializable):
    __ontology_tag__ = "vector3d_frame"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "x_axis",
                Vector3d.__msco_pyarrow_struct__,
                nullable=False,
                metadata={"description": "X-axis vector component."},
            ),
            pa.field(
                "y_axis",
                Vector3d.__msco_pyarrow_struct__,
                nullable=False,
                metadata={"description": "Y-axis vector component."},
            ),
            pa.field(
                "z_axis",
                Vector3d.__msco_pyarrow_struct__,
                nullable=False,
                metadata={"description": "Z-axis vector component."},
            ),
        ]
    )

    x_axis: Vector3d
    y_axis: Vector3d
    z_axis: Vector3d


class WorkspaceBounds(Serializable):
    __ontology_tag__ = "workspace_bounds"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "values",
                pa.list_(pa.list_(pa.float64(), list_size=3), list_size=3),
                nullable=False,
                metadata={"description": "Values defining the workspace bounds."},
            ),
        ]
    )

    values: list[list[float]]
