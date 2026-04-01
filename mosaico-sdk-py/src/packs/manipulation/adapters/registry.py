from packs.manipulation.adapters.audio.audio import AudioAdapter
from packs.manipulation.adapters.base import BaseAdapter
from packs.manipulation.adapters.robot.compensated_base_force_torque import (
    CompensatedBaseForceTorqueAdapter,
)
from packs.manipulation.adapters.robot.end_effector import EndEffectorAdapter
from packs.manipulation.adapters.robot.joint_state import JointStateAdapter
from packs.manipulation.adapters.robot.measured_force_torque import (
    MeasuredForceTorqueAdapter,
)
from packs.manipulation.adapters.robot.pose import PoseAdapter
from packs.manipulation.adapters.robot.velocity import VelocityAdapter
from packs.manipulation.adapters.vision.events import EventsAdapter
from packs.manipulation.adapters.vision.video_frame import VideoFrameAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, type[BaseAdapter]] = {}

    def register(self, adapter_cls: type[BaseAdapter]) -> None:
        if adapter_cls.adapter_id in self._adapters:
            raise ValueError(f"Adapter '{adapter_cls.adapter_id}' already registered")
        self._adapters[adapter_cls.adapter_id] = adapter_cls

    def get(self, adapter_id: str) -> type[BaseAdapter]:
        try:
            return self._adapters[adapter_id]
        except KeyError as exc:
            raise KeyError(f"Unknown adapter_id '{adapter_id}'") from exc

    def all(self) -> dict[str, type[BaseAdapter]]:
        return dict(self._adapters)


def build_default_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register(JointStateAdapter)
    registry.register(PoseAdapter)
    registry.register(VelocityAdapter)
    registry.register(VideoFrameAdapter)
    registry.register(EventsAdapter)
    registry.register(MeasuredForceTorqueAdapter)
    registry.register(CompensatedBaseForceTorqueAdapter)
    registry.register(AudioAdapter)
    registry.register(EndEffectorAdapter)
    return registry
