from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter
from mosaicolabs.packs.manipulation.adapters.reassemble.audio.audio import AudioAdapter
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.compensated_base_force_torque import (
    CompensatedBaseForceTorqueAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.end_effector import (
    EndEffectorAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.joint_state import (
    JointStateAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.measured_force_torque import (
    MeasuredForceTorqueAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.pose import PoseAdapter
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.velocity import (
    VelocityAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.vision.events import (
    EventsAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.vision.video_frame import (
    VideoFrameAdapter,
)


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
