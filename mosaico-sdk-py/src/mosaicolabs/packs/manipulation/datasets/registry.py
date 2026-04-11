from pathlib import Path

from mosaicolabs.packs.manipulation.contracts import DatasetPlugin
from mosaicolabs.packs.manipulation.datasets.droid import DROIDPlugin
from mosaicolabs.packs.manipulation.datasets.fractal_rt1 import FractalRT1Plugin
from mosaicolabs.packs.manipulation.datasets.mml import MMLPlugin
from mosaicolabs.packs.manipulation.datasets.reassemble import ReassemblePlugin


class DatasetRegistry:
    def __init__(self) -> None:
        self._plugins: list[DatasetPlugin] = []

    def register(self, plugin: DatasetPlugin) -> None:
        self._plugins.append(plugin)

    def all(self) -> list[DatasetPlugin]:
        return list(self._plugins)

    def get(self, dataset_id: str) -> DatasetPlugin:
        for plugin in self._plugins:
            if plugin.dataset_id == dataset_id:
                return plugin
        raise KeyError(f"Unknown dataset plugin '{dataset_id}'")

    def resolve(self, root: Path) -> DatasetPlugin:
        for plugin in self._plugins:
            if plugin.supports(root):
                return plugin
        raise ValueError(f"No dataset plugin found for {root}")


def build_default_dataset_registry() -> DatasetRegistry:
    registry = DatasetRegistry()
    registry.register(FractalRT1Plugin())
    registry.register(ReassemblePlugin())
    registry.register(MMLPlugin())
    registry.register(DROIDPlugin())
    return registry
