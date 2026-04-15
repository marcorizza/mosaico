from mosaicolabs import MosaicoField, MosaicoType, Serializable, Vector3d


class Vector3dBounds(Serializable):
    __ontology_tag__ = "vector3d_bounds"

    min: Vector3d = MosaicoField(description="Minimum vector limits.")
    max: Vector3d = MosaicoField(description="Maximum vector limits.")


class Vector3dFrame(Serializable):
    __ontology_tag__ = "vector3d_frame"

    x_axis: Vector3d = MosaicoField(description="X-axis vector component.")
    y_axis: Vector3d = MosaicoField(description="Y-axis vector component.")
    z_axis: Vector3d = MosaicoField(description="Z-axis vector component.")


class WorkspaceBounds(Serializable):
    __ontology_tag__ = "workspace_bounds"

    values: MosaicoType.list_(
        MosaicoType.list_(MosaicoType.float64, list_size=3),
        list_size=3,
    ) = MosaicoField(description="Values defining the workspace bounds.")
