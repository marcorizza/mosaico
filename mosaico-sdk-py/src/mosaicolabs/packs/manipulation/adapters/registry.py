from mosaicolabs.packs.manipulation.adapters.base import BaseAdapter
from mosaicolabs.packs.manipulation.adapters.droid.robot.end_effector import (
    DroidEndEffectorAdapter,
)
from mosaicolabs.packs.manipulation.adapters.droid.robot.joint_state import (
    DroidJointStateAdapter,
)
from mosaicolabs.packs.manipulation.adapters.droid.robot.pose import (
    DroidPoseAdapter,
)
from mosaicolabs.packs.manipulation.adapters.droid.scalar.boolean import (
    DroidBooleanAdapter,
)
from mosaicolabs.packs.manipulation.adapters.droid.scalar.floating64 import (
    DroidFloating64Adapter,
)
from mosaicolabs.packs.manipulation.adapters.droid.scalar.integer64 import (
    DroidInteger64Adapter,
)
from mosaicolabs.packs.manipulation.adapters.droid.vision.video_frame import (
    DroidVideoFrameAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.audio.audio import (
    ReassembleAudioAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.compensated_base_force_torque import (
    ReassembleCompensatedBaseForceTorqueAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.end_effector import (
    ReassembleEndEffectorAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.joint_state import (
    ReassembleJointStateAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.measured_force_torque import (
    ReassembleMeasuredForceTorqueAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.pose import (
    ReassemblePoseAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.robot.velocity import (
    ReassembleVelocityAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.vision.events import (
    ReassembleEventsAdapter,
)
from mosaicolabs.packs.manipulation.adapters.reassemble.vision.video_frame import (
    ReassembleVideoFrameAdapter,
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
    registry.register(ReassembleJointStateAdapter)
    registry.register(ReassemblePoseAdapter)
    registry.register(ReassembleVelocityAdapter)
    registry.register(ReassembleVideoFrameAdapter)
    registry.register(ReassembleEventsAdapter)
    registry.register(ReassembleMeasuredForceTorqueAdapter)
    registry.register(ReassembleCompensatedBaseForceTorqueAdapter)
    registry.register(ReassembleAudioAdapter)
    registry.register(ReassembleEndEffectorAdapter)
    registry.register(DroidJointStateAdapter)
    registry.register(DroidPoseAdapter)
    registry.register(DroidEndEffectorAdapter)
    registry.register(DroidVideoFrameAdapter)
    registry.register(DroidBooleanAdapter)
    registry.register(DroidFloating64Adapter)
    registry.register(DroidInteger64Adapter)
    return registry
