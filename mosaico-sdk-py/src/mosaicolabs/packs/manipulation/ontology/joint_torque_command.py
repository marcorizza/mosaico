from typing import List

import pyarrow as pa

from mosaicolabs import Serializable


class JointTorqueCommand(Serializable):
    __ontology_tag__ = "joint_torque_command"

    __msco_pyarrow_struct__ = pa.struct(
        [
            pa.field(
                "names",
                pa.list_(pa.string()),
                nullable=False,
                metadata={"description": "Names of the different robot joints"},
            ),
            pa.field(
                "torques",
                pa.list_(pa.float64()),
                nullable=False,
                metadata={
                    "description": "Torque values for the corresponding joints, in the same order as the names list."
                },
            ),
        ]
    )

    names: List[str]
    torques: List[float]
