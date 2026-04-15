import numpy as np
from mosaicolabs import Message

from mosaicopacks.manipulation.adapters.base import BaseAdapter
from mosaicopacks.manipulation.ontology.end_effector import EndEffector


class DroidEndEffectorAdapter(BaseAdapter):
    adapter_id = "droid.end_effector"
    ontology_type = EndEffector

    @classmethod
    def translate(cls, payload: dict) -> Message:
        pos = payload.get("position", 0.0)
        vel = payload.get("velocity", 0.0)
        if pos is None:
            pos = 0.0
        if vel is None:
            vel = 0.0

        if isinstance(pos, (list, tuple, np.ndarray)):
            pos_list = list(pos)
        else:
            pos_list = [float(pos)]

        if isinstance(vel, (list, tuple, np.ndarray)):
            vel_list = list(vel)
        else:
            vel_list = [float(vel)]

        return Message(
            timestamp_ns=int(payload["timestamp"] * 1e9),
            data=EndEffector(
                positions=pos_list,
                velocities=vel_list,
                efforts=[0.0] * len(pos_list),
            ),
        )
