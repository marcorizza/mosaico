from mosaicolabs import MosaicoField, MosaicoType, Serializable


class EndEffector(Serializable):
    __ontology_tag__ = "end_effector"

    efforts: MosaicoType.list_(MosaicoType.float64) = MosaicoField(
        description="End-effector effort values for each controlled dimension."
    )
    positions: MosaicoType.list_(MosaicoType.float64) = MosaicoField(
        description="End-effector position values for each controlled dimension."
    )
    velocities: MosaicoType.list_(MosaicoType.float64) = MosaicoField(
        description="End-effector velocity values for each controlled dimension."
    )
