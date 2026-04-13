from mosaicolabs import MosaicoField, MosaicoType, Serializable


class JointTorqueCommand(Serializable):
    __ontology_tag__ = "joint_torque_command"

    names: MosaicoType.list_(MosaicoType.string) = MosaicoField(
        description="Names of the different robot joints"
    )
    torques: MosaicoType.list_(MosaicoType.float64) = MosaicoField(
        description="Torque values for the corresponding joints, in the same order as the names list."
    )
